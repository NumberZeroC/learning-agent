#!/usr/bin/env python3
"""
Learning Agent Web 应用（优化版）

核心功能：
1. 工作流成果展示（主页）
2. Web 聊天问答

优化改进：
- 全局错误处理中间件
- 简化API Key加载逻辑
- 响应缓存支持
"""

import os
import sys
import json
import logging
from pathlib import Path
from flask import Flask, render_template, jsonify, send_from_directory, request
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

project_dir = Path(__file__).parent.parent
env_file = project_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)

web_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))
sys.path.insert(0, str(web_dir))

log_dir = project_dir / "logs"
log_dir.mkdir(exist_ok=True)

log_file = log_dir / "web.log"
handler = RotatingFileHandler(
    log_file, maxBytes=10 * 1024 * 1024, backupCount=10, encoding="utf-8"
)
handler.setFormatter(
    logging.Formatter("%(asctime)s - [%(levelname)s] - %(name)s - %(message)s")
)
handler.setLevel(logging.INFO)

app = Flask(__name__)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)
app.logger.addHandler(logging.StreamHandler())

DATA_DIR = project_dir / "data" / "workflow_results"


@app.errorhandler(Exception)
def handle_exception(e):
    """全局错误处理"""
    app.logger.error(f"请求异常: {e}", exc_info=True)
    return jsonify(
        {"success": False, "error": str(e), "error_type": type(e).__name__}
    ), 500


@app.errorhandler(404)
def handle_404(e):
    return jsonify({"success": False, "error": "Resource not found"}), 404


@app.errorhandler(500)
def handle_500(e):
    return jsonify({"success": False, "error": "Internal server error"}), 500


@app.after_request
def after_request(response):
    """请求后处理：添加通用头"""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


api_key = ""
try:
    from services.key_vault import get_key_vault

    vault = get_key_vault()
    api_key = vault.get_key("dashscope") or ""
except Exception:
    if not api_key:
        config_path = project_dir / "config" / "agent_config.yaml"
        if config_path.exists():
            import yaml

            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                api_key = (
                    config.get("providers", {})
                    .get("dashscope", {})
                    .get("api_key_value", "")
                )

        if not api_key:
            api_key = os.getenv("DASHSCOPE_API_KEY", "")

if api_key:
    app.logger.info(f"✅ API Key 已加载 (前缀：{api_key[:15]}...)")
    app.logger.info("🎉 完整功能可用（Web 展示 + 聊天 + 工作流）")
else:
    app.logger.info("ℹ️  Web 服务已启动（知识展示模式）")
    app.logger.info("💡 提示：配置 API Key 后可启用聊天和工作流功能")
    app.logger.info("💡 配置方法：export DASHSCOPE_API_KEY=sk-xxx 或编辑 .env 文件")

from routes.chat_routes import chat_bp
from routes.workflow_routes import (
    workflow_bp,
    register_blueprint as register_workflow_bp,
)
from routes.config_routes import config_bp
from routes.workflow_run_routes import workflow_run_bp

app.register_blueprint(chat_bp)
register_workflow_bp(app)
app.register_blueprint(config_bp)
app.register_blueprint(workflow_run_bp)


@app.route("/")
def index():
    return render_template("workflow.html")


@app.route("/chat")
def chat_page():
    return render_template("chat.html")


@app.route("/config")
def config_page():
    return render_template("config.html")


@app.route("/layer/<int:layer_id>")
def layer_detail(layer_id):
    return render_template("layer.html", layer_id=layer_id)


@app.route("/topic/<int:layer_id>/<int:topic_index>")
def topic_detail(layer_id, topic_index):
    return render_template("topic.html", layer_id=layer_id, topic_index=topic_index)


@app.route("/api/summary")
def api_summary():
    summary_file = DATA_DIR / "workflow_summary.json"

    if summary_file.exists():
        with open(summary_file, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))

    return jsonify({"error": "Summary not found"}), 404


@app.route("/health")
def health_check():
    from datetime import datetime

    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "api_key_configured": bool(api_key),
        }
    )


@app.route("/api/stats")
def api_stats():
    """获取LLM调用统计"""
    try:
        from services.llm_client import LLMClient

        stats = LLMClient.get_stats()
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


def initialize_ask_service():
    """初始化 Ask 服务"""
    try:
        from services.ask_service import get_ask_service

        ask_service = get_ask_service()
        app.logger.info(
            f"Ask 服务初始化完成，可用Agent: {len(ask_service.get_available_agents())} 个"
        )
        return ask_service
    except Exception as e:
        app.logger.warning(f"Ask 服务初始化失败：{e}")
        return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Learning Agent Web 应用")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址")
    parser.add_argument("--port", type=int, default=5001, help="监听端口")
    parser.add_argument("--debug", action="store_true", help="调试模式")

    args = parser.parse_args()

    initialize_ask_service()

    print(f"\n启动 Web 服务：http://{args.host}:{args.port}")
    print("=" * 60 + "\n")

    app.run(host=args.host, port=args.port, debug=args.debug)
