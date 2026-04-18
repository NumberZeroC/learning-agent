#!/usr/bin/env python3
"""
Learning Agent 公开知识展示网站

定位：对外公开发布，只读展示知识内容
功能：
- 知识架构展示
- 知识点详情浏览
- 学习进度统计

已禁用功能：
- ❌ 聊天问答
- ❌ 配置管理
- ❌ 工作流执行
- ❌ API Key 配置

安全特性：
- 只读模式，无写操作
- 不暴露 API Key
- 不暴露内部配置
- 简化的权限控制

部署说明：
- 生产环境部署使用此版本
- 监听 0.0.0.0:80 或 443
- 建议配置 Nginx 反向代理
- 启用 HTTPS
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, send_from_directory
from logging.handlers import RotatingFileHandler

project_dir = Path(__file__).parent.parent
web_dir = Path(__file__).parent

app = Flask(__name__)

# ============================================
# 日志配置
# ============================================
log_dir = project_dir / "logs"
log_dir.mkdir(exist_ok=True)

log_file = log_dir / "web_public.log"
handler = RotatingFileHandler(
    log_file, maxBytes=10 * 1024 * 1024, backupCount=10, encoding="utf-8"
)
handler.setFormatter(
    logging.Formatter("%(asctime)s - [%(levelname)s] - %(name)s - %(message)s")
)
handler.setLevel(logging.INFO)

app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)
app.logger.addHandler(logging.StreamHandler())

# ============================================
# 数据目录
# ============================================
DATA_DIR = project_dir / "data" / "workflow_results"
CONFIG_DIR = project_dir / "config"

# ============================================
# 安全配置（只读模式）
# ============================================
@app.errorhandler(Exception)
def handle_exception(e):
    """全局错误处理 - 不暴露内部细节"""
    app.logger.error(f"请求异常：{e}", exc_info=False)
    return jsonify(
        {"success": False, "error": "服务暂时不可用"}
    ), 500


@app.errorhandler(404)
def handle_404(e):
    return jsonify({"success": False, "error": "页面未找到"}), 404


@app.after_request
def after_request(response):
    """安全头配置"""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Cache-Control"] = "public, max-age=300"
    return response


# ============================================
# 页面路由
# ============================================
@app.route("/")
def index():
    """主页 - 知识架构展示"""
    return render_template("public_index.html")


@app.route("/layer/<int:layer_id>")
def layer_detail(layer_id):
    """层级详情页"""
    if layer_id < 1 or layer_id > 5:
        return jsonify({"error": "无效的层级"}), 404
    return render_template("public_layer.html", layer_id=layer_id)


@app.route("/topic/<int:layer_id>/<int:topic_index>")
def topic_detail(layer_id, topic_index):
    """主题详情页"""
    if layer_id < 1 or layer_id > 5:
        return jsonify({"error": "无效的层级"}), 404
    return render_template("public_topic.html", layer_id=layer_id, topic_index=topic_index)


# ============================================
# 数据 API（只读）
# ============================================
@app.route("/api/summary")
def api_summary():
    """获取工作流汇总数据"""
    summary_file = DATA_DIR / "workflow_summary.json"

    if summary_file.exists():
        with open(summary_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 只返回公开数据
            return jsonify({
                "success": True,
                "data": {
                    "total_workflows": data.get("total_workflows", 0),
                    "total_tasks": data.get("total_tasks", 0),
                    "total_success": data.get("total_success", 0)
                }
            })

    return jsonify({"success": False, "error": "数据未找到"}), 404


@app.route("/api/layers")
def api_layers():
    """获取知识架构层级数据"""
    framework_file = CONFIG_DIR / "knowledge_framework.yaml"
    
    if framework_file.exists():
        try:
            import yaml
            with open(framework_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            layers = data.get("layers", [])
            # 简化数据，移除敏感信息
            public_layers = []
            for layer in layers:
                public_layers.append({
                    "layer": layer.get("layer"),
                    "name": layer.get("name"),
                    "description": layer.get("description", ""),
                    "topics_count": len(layer.get("topics", []))
                })
            
            return jsonify({
                "success": True,
                "data": {
                    "name": data.get("name", "知识体系"),
                    "version": data.get("version", "1.0"),
                    "layers": public_layers
                }
            })
        except Exception as e:
            app.logger.error(f"加载架构失败：{e}")
    
    return jsonify({"success": False, "error": "数据未找到"}), 404


@app.route("/api/layer/<int:layer_id>")
def api_layer_detail(layer_id):
    """获取指定层级详情"""
    framework_file = CONFIG_DIR / "knowledge_framework.yaml"
    
    if framework_file.exists():
        try:
            import yaml
            with open(framework_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            layers = data.get("layers", [])
            target_layer = next((l for l in layers if l.get("layer") == layer_id), None)
            
            if target_layer:
                # 简化主题数据
                topics = []
                for topic in target_layer.get("topics", []):
                    topics.append({
                        "name": topic.get("name"),
                        "description": topic.get("description", ""),
                        "priority": topic.get("priority", "medium"),
                        "subtopics": topic.get("subtopics", [])
                    })
                
                return jsonify({
                    "success": True,
                    "data": {
                        "layer": target_layer.get("layer"),
                        "name": target_layer.get("name"),
                        "description": target_layer.get("description", ""),
                        "topics": topics
                    }
                })
        except Exception as e:
            app.logger.error(f"加载层级详情失败：{e}")
    
    return jsonify({"success": False, "error": "数据未找到"}), 404


@app.route("/api/stats")
def api_stats():
    """获取公开统计数据"""
    # 统计已生成的知识点数量
    stats = {
        "total_layers": 5,
        "total_topics": 17,
        "generated_topics": 0,
        "last_updated": None
    }
    
    # 检查最新的工作流结果
    if DATA_DIR.exists():
        workflow_files = list(DATA_DIR.glob("workflow_*.json"))
        if workflow_files:
            latest = max(workflow_files, key=lambda f: f.stat().st_mtime)
            try:
                with open(latest, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    stats["generated_topics"] = data.get("success_count", 0)
                    stats["last_updated"] = data.get("completed_at", "")
            except Exception:
                pass
    
    return jsonify({"success": True, "stats": stats})


# ============================================
# 健康检查
# ============================================
@app.route("/health")
def health_check():
    """健康检查接口"""
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0-public",
            "mode": "read-only"
        }
    )


# ============================================
# 启动信息
# ============================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Learning Agent 公开知识展示网站")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    parser.add_argument("--port", type=int, default=80, help="监听端口")
    parser.add_argument("--debug", action="store_true", help="调试模式（生产环境禁用）")

    args = parser.parse_args()

    app.logger.info("=" * 60)
    app.logger.info("🌐 Learning Agent 公开知识展示网站")
    app.logger.info("=" * 60)
    app.logger.info(f"📍 监听地址：http://{args.host}:{args.port}")
    app.logger.info("🔒 运行模式：只读展示")
    app.logger.info("✅ 已禁用：聊天、配置、工作流执行")
    app.logger.info("=" * 60)

    print(f"\n🌐 启动 Web 服务：http://{args.host}:{args.port}")
    print("=" * 60)
    print("🔒 运行模式：只读展示")
    print("✅ 已禁用：聊天、配置、工作流执行")
    print("=" * 60 + "\n")

    app.run(host=args.host, port=args.port, debug=args.debug)
