#!/usr/bin/env python3
"""
配置管理 API 路由
"""

from flask import Blueprint, jsonify, render_template, request
from pathlib import Path
import sys
import yaml

# 项目路径
web_dir = Path(__file__).parent.parent
project_dir = web_dir.parent
sys.path.insert(0, str(project_dir))

config_bp = Blueprint('config', __name__)


@config_bp.route('/config')
def config_page():
    """配置管理页面"""
    return render_template('config.html')


@config_bp.route('/api/config')
def get_config():
    """获取完整配置"""
    try:
        config_path = project_dir / "config" / "agent_config.yaml"
        
        if not config_path.exists():
            return jsonify({
                "success": False,
                "error": "配置文件不存在"
            }), 404
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 隐藏敏感的 API Key（只显示前缀）
        if 'providers' in config and 'dashscope' in config['providers']:
            api_key = config['providers']['dashscope'].get('api_key_value', '')
            if api_key:
                config['providers']['dashscope']['api_key_value'] = api_key[:15] + '...'
        
        return jsonify({
            "success": True,
            "data": config
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@config_bp.route('/api/config/agents')
def get_agents_config():
    """获取 Agent 配置列表"""
    try:
        config_path = project_dir / "config" / "agent_config.yaml"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        agents = config.get('agents', {})
        
        # 简化返回数据
        agents_list = []
        for key, agent in agents.items():
            agents_list.append({
                "key": key,
                "name": agent.get('role', key),
                "enabled": agent.get('enabled', False),
                "layer": agent.get('layer', 0),
                "model": agent.get('model', 'qwen3.5-plus'),
                "description": agent.get('description', '')
            })
        
        return jsonify({
            "success": True,
            "data": {
                "agents": agents_list,
                "total": len(agents_list)
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@config_bp.route('/api/config/providers')
def get_providers_config():
    """获取大模型提供商配置"""
    try:
        config_path = project_dir / "config" / "agent_config.yaml"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        providers = config.get('providers', {})
        
        # 隐藏 API Key
        for provider in providers.values():
            if 'api_key_value' in provider:
                provider['api_key_value'] = provider['api_key_value'][:15] + '...'
        
        return jsonify({
            "success": True,
            "data": providers
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@config_bp.route('/api/config', methods=['PUT'])
def save_config():
    """保存配置"""
    try:
        config_path = project_dir / "config" / "agent_config.yaml"
        
        if not config_path.exists():
            return jsonify({
                "success": False,
                "error": "配置文件不存在"
            }), 404
        
        new_config = request.get_json()
        
        if not new_config:
            return jsonify({
                "success": False,
                "error": "配置数据为空"
            }), 400
        
        # 读取现有配置
        with open(config_path, 'r', encoding='utf-8') as f:
            current_config = yaml.safe_load(f)
        
        # 更新配置（保留原有结构）
        if 'global' in new_config:
            current_config['global'] = new_config['global']
        
        if 'providers' in new_config:
            for provider_key, provider_config in new_config['providers'].items():
                if provider_key in current_config['providers']:
                    # 特殊处理 API Key：如果前端传了完整 Key，直接覆盖
                    if 'api_key_value' in provider_config:
                        current_config['providers'][provider_key]['api_key_value'] = provider_config['api_key_value']
                    # 其他字段正常更新
                    for key, value in provider_config.items():
                        if key != 'api_key_value':
                            current_config['providers'][provider_key][key] = value
        
        if 'tools' in new_config:
            for tool_key, tool_config in new_config['tools'].items():
                if tool_key in current_config['tools']:
                    current_config['tools'][tool_key].update(tool_config)
        
        if 'agents' in new_config:
            for agent_key, agent_config in new_config['agents'].items():
                if agent_key in current_config['agents']:
                    current_config['agents'][agent_key].update(agent_config)
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(current_config, f, allow_unicode=True, default_flow_style=False)
        
        return jsonify({
            "success": True,
            "message": "配置已保存"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
