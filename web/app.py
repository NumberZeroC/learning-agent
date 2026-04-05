#!/usr/bin/env python3
"""
Learning Agent Web 应用

核心功能：
1. 工作流成果展示（主页）
2. Web 聊天问答
"""

import os
import sys
import json
import logging
from pathlib import Path
from flask import Flask, render_template, jsonify, send_from_directory
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# 加载 .env 文件
project_dir = Path(__file__).parent.parent
env_file = project_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ 已加载环境变量：{env_file}")
else:
    print(f"⚠️  未找到 .env 文件：{env_file}")

# 添加项目路径
web_dir = Path(__file__).parent
project_dir = web_dir.parent
sys.path.insert(0, str(project_dir))
sys.path.insert(0, str(web_dir))

# 配置日志
log_dir = project_dir / "logs"
log_dir.mkdir(exist_ok=True)

# 日志配置：最多保留 10 个文件，每个文件最大 10MB
log_file = log_dir / "web.log"
handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=10,  # 保留 10 个备份文件
    encoding='utf-8'
)
handler.setFormatter(logging.Formatter(
    '%(asctime)s - [%(levelname)s] - %(name)s - %(message)s'
))
handler.setLevel(logging.INFO)

# 配置 Flask app 的 logger
app = Flask(__name__)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# 同时输出到控制台
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s - [%(levelname)s] - %(message)s'
))
app.logger.addHandler(console_handler)

app.logger.info("🚀 Learning Agent Web 服务启动")
app.logger.info(f"📝 日志文件：{log_file}")
app.logger.info(f"📊 日志策略：最多保留 10 个文件，每个文件最大 10MB")

# 数据目录
DATA_DIR = project_dir / "data" / "workflow_results"

# 验证 API Key 是否加载（优先检查配置文件）
api_key = ''
config_path = project_dir / "config" / "agent_config.yaml"
if config_path.exists():
    import yaml
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        providers = config.get('providers', {})
        dashscope = providers.get('dashscope', {})
        api_key = dashscope.get('api_key_value', '')

# 如果配置文件没有，检查环境变量
if not api_key:
    api_key = os.getenv('DASHSCOPE_API_KEY', '')

if api_key:
    print(f"✅ API Key 已加载 (前缀：{api_key[:15]}...)")
else:
    print("❌ API Key 未配置，请在配置页面设置")

# 注册路由蓝图
from routes.chat_routes import chat_bp
from routes.workflow_routes import workflow_bp, register_blueprint as register_workflow_bp
from routes.config_routes import config_bp
from routes.workflow_run_routes import workflow_run_bp

app.register_blueprint(chat_bp)
register_workflow_bp(app)
app.register_blueprint(config_bp)
app.register_blueprint(workflow_run_bp)


# ==================== 页面路由 ====================

@app.route('/')
def index():
    """首页 - 工作流成果展示"""
    return render_template('workflow.html')


@app.route('/chat')
def chat_page():
    """聊天问答页"""
    return render_template('chat.html')


@app.route('/config')
def config_page():
    """配置管理页"""
    return render_template('config.html')


@app.route('/layer/<int:layer_id>')
def layer_detail(layer_id):
    """层级详情页"""
    return render_template('layer.html', layer_id=layer_id)


@app.route('/topic/<int:layer_id>/<int:topic_index>')
def topic_detail(layer_id, topic_index):
    """知识点详情页"""
    return render_template('topic.html', layer_id=layer_id, topic_index=topic_index)


# ==================== API 路由 ====================

@app.route('/api/summary')
def api_summary():
    """获取工作流汇总"""
    summary_file = DATA_DIR / "workflow_summary.json"
    
    if summary_file.exists():
        with open(summary_file, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    
    return jsonify({"error": "Summary not found"}), 404


@app.route('/health')
def health_check():
    """健康检查接口"""
    from datetime import datetime
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })


# ==================== 初始化函数 ====================

def initialize_ask_service():
    """初始化 Ask 服务"""
    print("\n" + "="*60)
    print("🌐 初始化 Ask 服务...")
    print("="*60)
    
    try:
        from services.ask_service import get_ask_service
        ask_service = get_ask_service()
        print(f"✅ Ask 服务初始化完成")
        print(f"   可用 Agent: {len(ask_service.get_available_agents())} 个")
        return ask_service
    except Exception as e:
        print(f"⚠️  Ask 服务初始化失败：{e}")
        return None


# ==================== 主入口 ====================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="Learning Agent Web 应用")
    parser.add_argument('--host', default='127.0.0.1', help='监听地址')
    parser.add_argument('--port', type=int, default=5001, help='监听端口')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    
    args = parser.parse_args()
    
    # 初始化 Ask 服务
    initialize_ask_service()
    
    print(f"\n🚀 启动 Web 服务：http://{args.host}:{args.port}")
    print("="*60 + "\n")
    
    # 启动 Flask
    app.run(host=args.host, port=args.port, debug=args.debug)
