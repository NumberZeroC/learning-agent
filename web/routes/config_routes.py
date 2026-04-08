#!/usr/bin/env python3
"""
配置管理 API 路由（安全增强版）

核心改进：
- API Key 通过 KeyVault 加密存储
- 配置文件不再包含敏感 Key
- 完整的审计日志
"""

from flask import Blueprint, jsonify, render_template, request
from pathlib import Path
import sys
import yaml
import logging
from datetime import datetime

# 项目路径
web_dir = Path(__file__).parent.parent
project_dir = web_dir.parent
sys.path.insert(0, str(project_dir))

config_bp = Blueprint('config', __name__)
logger = logging.getLogger('config_routes')


@config_bp.route('/config')
def config_page():
    """配置管理页面"""
    return render_template('config.html')


@config_bp.route('/api/config')
def get_config():
    """获取完整配置（不含 API Key 明文）"""
    try:
        config_path = project_dir / "config" / "agent_config.yaml"
        
        if not config_path.exists():
            return jsonify({
                "success": False,
                "error": "配置文件不存在"
            }), 404
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 从 KeyVault 获取 Key 状态（不返回明文）
        try:
            from services.key_vault import get_key_vault
            vault = get_key_vault()
            
            if 'providers' in config:
                for provider_key in config['providers'].keys():
                    configured = vault.is_key_configured(provider_key)
                    prefix = vault.get_key_prefix(provider_key)
                    config['providers'][provider_key]['key_configured'] = configured
                    config['providers'][provider_key]['key_prefix'] = prefix
                    # 移除明文 Key（如果存在）
                    if 'api_key_value' in config['providers'][provider_key]:
                        del config['providers'][provider_key]['api_key_value']
        
        except Exception as e:
            logger.warning(f"KeyVault 未就绪，使用降级模式：{e}")
        
        return jsonify({
            "success": True,
            "data": config
        })
        
    except Exception as e:
        logger.error(f"获取配置失败：{e}")
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
        logger.error(f"获取 Agent 配置失败：{e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@config_bp.route('/api/config/providers')
def get_providers_config():
    """获取大模型提供商配置（安全版）"""
    try:
        config_path = project_dir / "config" / "agent_config.yaml"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        providers = config.get('providers', {})
        
        # 从 KeyVault 获取 Key 状态
        try:
            from services.key_vault import get_key_vault
            vault = get_key_vault()
            
            for provider_key in providers.keys():
                configured = vault.is_key_configured(provider_key)
                prefix = vault.get_key_prefix(provider_key)
                providers[provider_key]['key_configured'] = configured
                providers[provider_key]['key_prefix'] = prefix
                # 移除明文 Key
                if 'api_key_value' in providers[provider_key]:
                    del providers[provider_key]['api_key_value']
        
        except Exception as e:
            logger.warning(f"KeyVault 未就绪：{e}")
        
        return jsonify({
            "success": True,
            "data": providers
        })
        
    except Exception as e:
        logger.error(f"获取 Provider 配置失败：{e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@config_bp.route('/api/config/providers/<provider>/key', methods=['POST'])
def update_api_key(provider: str):
    """
    更新 API Key（加密存储）
    
    Request:
    {
        "api_key": "sk-sp-xxx"
    }
    """
    try:
        data = request.get_json()
        api_key = data.get('api_key', '').strip()
        
        if not api_key:
            return jsonify({
                "success": False,
                "error": "API Key 不能为空"
            }), 400
        
        # 基本格式验证
        if not api_key.startswith('sk-'):
            return jsonify({
                "success": False,
                "error": "API Key 格式不正确，应以 sk- 开头"
            }), 400
        
        # 保存到 KeyVault
        from services.key_vault import get_key_vault
        vault = get_key_vault()
        
        prefix = vault.save_key(
            provider=provider,
            api_key=api_key,
            user_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        # 如果配置文件中有旧的明文 Key，移除它
        config_path = project_dir / "config" / "agent_config.yaml"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if 'providers' in config and provider in config['providers']:
                if 'api_key_value' in config['providers'][provider]:
                    del config['providers'][provider]['api_key_value']
                    
                    with open(config_path, 'w', encoding='utf-8') as f:
                        yaml.dump(config, f, allow_unicode=True)
        
        logger.info(f"✅ {provider} API Key 已更新 (前缀：{prefix})")
        
        return jsonify({
            "success": True,
            "key_prefix": prefix,
            "message": "API Key 已安全保存"
        })
        
    except Exception as e:
        logger.error(f"更新 API Key 失败：{e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@config_bp.route('/api/config/providers/<provider>/key', methods=['DELETE'])
def delete_api_key(provider: str):
    """删除 API Key"""
    try:
        from services.key_vault import get_key_vault
        vault = get_key_vault()
        
        deleted = vault.delete_key(
            provider=provider,
            user_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        if deleted:
            logger.info(f"✅ {provider} API Key 已删除")
            return jsonify({
                "success": True,
                "message": "API Key 已删除"
            })
        else:
            return jsonify({
                "success": False,
                "error": "未找到该 Provider 的 API Key"
            }), 404
        
    except Exception as e:
        logger.error(f"删除 API Key 失败：{e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@config_bp.route('/api/config/providers/<provider>/test', methods=['POST'])
def test_api_key(provider: str):
    """测试 API Key 连接"""
    try:
        from services.key_vault import get_key_vault
        vault = get_key_vault()
        
        api_key = vault.get_key(provider)
        
        if not api_key:
            return jsonify({
                "success": False,
                "error": "未配置 API Key"
            }), 404
        
        # 获取 Provider 配置
        config_path = project_dir / "config" / "agent_config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        provider_config = config.get('providers', {}).get(provider, {})
        base_url = provider_config.get('base_url', '')
        
        # 简单测试连接
        import urllib.request
        import json
        
        # 使用正确的 DashScope API 端点（兼容 OpenAI 格式）
        if not base_url or 'coding.dashscope' in base_url:
            test_url = 'https://coding.dashscope.aliyuncs.com/v1/chat/completions'
            payload = {
                "model": "qwen3.5-plus",
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 1
            }
        else:
            # 旧版 API
            test_url = f'{base_url}/services/aigc/text-generation/generation'
            payload = {
                "model": "qwen-turbo",
                "input": {"messages": [{"role": "user", "content": "Hi"}]},
                "parameters": {"max_tokens": 1}
            }
        
        req = urllib.request.Request(
            test_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode())
                return jsonify({
                    "success": True,
                    "message": "连接测试成功",
                    "response": result
                })
        except urllib.error.HTTPError as e:
            if e.code == 401:
                return jsonify({
                    "success": False,
                    "error": "API Key 无效（401）"
                }), 401
            raise
        
    except Exception as e:
        logger.error(f"测试 API Key 失败：{e}")
        return jsonify({
            "success": False,
            "error": f"连接测试失败：{str(e)}"
        }), 500


@config_bp.route('/api/config/audit-logs')
def get_audit_logs():
    """获取配置审计日志（管理员）"""
    try:
        from services.key_vault import get_key_vault
        vault = get_key_vault()
        
        provider = request.args.get('provider')
        limit = int(request.args.get('limit', 100))
        
        logs = vault.get_audit_logs(limit=limit, provider=provider)
        
        return jsonify({
            "success": True,
            "data": {
                "logs": logs,
                "total": len(logs)
            }
        })
        
    except Exception as e:
        logger.error(f"获取审计日志失败：{e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@config_bp.route('/api/config', methods=['PUT'])
def save_config():
    """保存配置（不含 API Key）"""
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
        
        # 更新配置（不包含 API Key）
        if 'global' in new_config:
            current_config['global'] = new_config['global']
        
        if 'providers' in new_config:
            for provider_key, provider_config in new_config['providers'].items():
                if provider_key in current_config['providers']:
                    # 移除 API Key 字段（Key 通过 KeyVault 管理）
                    if 'api_key_value' in provider_config:
                        del provider_config['api_key_value']
                    if 'key_configured' in provider_config:
                        del provider_config['key_configured']
                    if 'key_prefix' in provider_config:
                        del provider_config['key_prefix']
                    
                    # 更新其他字段
                    current_config['providers'][provider_key].update(provider_config)
        
        if 'agents' in new_config:
            for agent_key, agent_config in new_config['agents'].items():
                if agent_key in current_config['agents']:
                    current_config['agents'][agent_key].update(agent_config)
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(current_config, f, allow_unicode=True, default_flow_style=False)
        
        logger.info(f"✅ 配置已保存 (来源 IP: {request.remote_addr})")
        
        return jsonify({
            "success": True,
            "message": "配置已保存"
        })
        
    except Exception as e:
        logger.error(f"保存配置失败：{e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
