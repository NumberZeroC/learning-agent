#!/usr/bin/env python3
"""
聊天 API 路由

支持两种模式：
- Ask 模式：Web 问答助手，实时对话交互
- Task 模式：后台任务执行，批量知识生成

支持流式响应（SSE）
"""

from flask import Blueprint, jsonify, request, Response, stream_with_context
from pathlib import Path
import sys
import json
from datetime import datetime
import urllib.request
import urllib.error
import time

# 导入配置和工具
web_dir = Path(__file__).parent.parent
project_dir = web_dir.parent
sys.path.insert(0, str(project_dir))

# 导入服务
from services.ask_service import get_ask_service, AskService
from services.task_service import get_task_service, TaskService

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')


@chat_bp.route('/send', methods=['POST'])
def send_message():
    """
    发送消息给 Agent (Ask 模式) - 非流式
    
    请求体:
    {
        "message": "用户消息",
        "agent": "master_agent"  # 可选，默认 master_agent
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "error": "请求数据为空"
        }), 400
    
    message = data.get('message', '')
    agent_name = data.get('agent', 'master_agent')
    
    if not message:
        return jsonify({
            "success": False,
            "error": "消息内容为空"
        }), 400
    
    # 使用 AskService 处理消息
    ask_service = get_ask_service()
    result = ask_service.chat(message, agent_name)
    
    return jsonify(result)


@chat_bp.route('/stream', methods=['POST'])
def stream_message():
    """
    发送消息给 Agent (Ask 模式) - 流式响应 (SSE)
    
    请求体:
    {
        "message": "用户消息",
        "agent": "web_chat_agent"  # 可选，默认 web_chat_agent（专门用于聊天）
    }
    
    返回 Server-Sent Events 流
    
    注意：
    - web_chat_agent: 专门用于聊天问答，输出自然语言
    - master_agent: 用于工作流任务分解，输出 JSON
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "error": "请求数据为空"
        }), 400
    
    message = data.get('message', '')
    # 默认使用 web_chat_agent 而不是 master_agent
    # master_agent 用于工作流任务分解（输出 JSON），不适合聊天
    agent_name = data.get('agent', 'web_chat_agent')
    
    if not message:
        return jsonify({
            "success": False,
            "error": "消息内容为空"
        }), 400
    
    def generate():
        """生成 SSE 流"""
        try:
            # 获取 Agent 配置
            ask_service = get_ask_service()
            agent = ask_service.agents.get(agent_name, {})
            system_prompt = agent.get('system_prompt', '你是一个有帮助的 AI 助手。')
            
            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'agent': agent_name})}\n\n"
            
            # 调用流式 LLM API
            for chunk in ask_service.chat_stream(message, system_prompt):
                yield f"data: {json.dumps(chunk)}\n\n"
            
            # 发送结束事件
            yield f"data: {json.dumps({'type': 'end', 'timestamp': datetime.now().isoformat()})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


@chat_bp.route('/history', methods=['GET'])
def get_history():
    """获取对话历史"""
    agent_name = request.args.get('agent', 'master_agent')
    limit = request.args.get('limit', 20, type=int)
    
    ask_service = get_ask_service()
    history = ask_service.get_history(agent_name, limit)
    
    return jsonify({
        "success": True,
        "data": {
            "history": history,
            "total": len(history),
            "agent": agent_name
        }
    })


@chat_bp.route('/clear', methods=['POST'])
def clear_history():
    """清除对话历史"""
    agent_name = request.args.get('agent', 'master_agent')
    
    ask_service = get_ask_service()
    ask_service.clear_history(agent_name)
    
    return jsonify({
        "success": True,
        "message": f"已清除 {agent_name} 的对话历史"
    })


@chat_bp.route('/agents', methods=['GET'])
def get_available_agents():
    """获取可用 Agent 列表"""
    ask_service = get_ask_service()
    agents = ask_service.get_available_agents()
    
    return jsonify({
        "success": True,
        "data": {
            "agents": agents,
            "total": len(agents)
        }
    })


# ==================== Task 模式 API ====================

@chat_bp.route('/task', methods=['POST'])
def execute_task():
    """
    执行后台任务 (Task 模式)
    
    请求体:
    {
        "request": "任务请求内容",
        "layers": [1, 2, 3],  # 可选，指定层级
        "priority": "normal"   # 可选，优先级
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "error": "请求数据为空"
        }), 400
    
    request_content = data.get('request', '')
    layers = data.get('layers')
    priority_str = data.get('priority', 'normal')
    
    if not request_content:
        return jsonify({
            "success": False,
            "error": "任务请求内容为空"
        }), 400
    
    # 解析优先级
    from agents import TaskPriority
    priority_map = {
        'low': TaskPriority.LOW,
        'normal': TaskPriority.NORMAL,
        'high': TaskPriority.HIGH,
        'urgent': TaskPriority.URGENT
    }
    priority = priority_map.get(priority_str.lower(), TaskPriority.NORMAL)
    
    # 使用 TaskService 执行任务
    task_service = get_task_service(verbose=True)
    result = task_service.execute(request_content, layers=layers, priority=priority)
    
    return jsonify({
        "success": result.get('success', False),
        "data": result
    })


@chat_bp.route('/task/<task_id>', methods=['GET'])
def get_task_status(task_id: str):
    """获取任务状态"""
    task_service = get_task_service()
    status = task_service.get_task_status(task_id)
    
    if status:
        return jsonify({
            "success": True,
            "data": status
        })
    else:
        return jsonify({
            "success": False,
            "error": f"任务 {task_id} 不存在"
        }), 404


@chat_bp.route('/tasks', methods=['GET'])
def get_all_tasks():
    """获取所有任务列表"""
    task_service = get_task_service()
    tasks = task_service.get_all_tasks()
    
    return jsonify({
        "success": True,
        "data": {
            "tasks": tasks,
            "total": len(tasks)
        }
    })


@chat_bp.route('/knowledge', methods=['GET'])
def get_generated_knowledge():
    """获取已生成的知识"""
    task_service = get_task_service()
    knowledge = task_service.get_generated_knowledge()
    
    return jsonify({
        "success": True,
        "data": {
            "knowledge": knowledge,
            "total_layers": len(knowledge)
        }
    })


@chat_bp.route('/summary', methods=['GET'])
def get_learning_summary():
    """获取学习路线总结"""
    task_service = get_task_service()
    summary = task_service.get_summary()
    
    return jsonify({
        "success": True,
        "data": summary
    })


# 注册蓝图
def register_blueprint(app):
    """注册蓝图到 Flask 应用"""
    app.register_blueprint(chat_bp)
