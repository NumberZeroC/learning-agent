#!/usr/bin/env python3
"""
工作流运行管理 API

支持：
- 启动知识生成工作流
- 检查工作流状态
- 停止工作流
"""

from flask import Blueprint, jsonify, request
from pathlib import Path
import sys
import os
import subprocess
import signal
import logging

# 配置日志
logger = logging.getLogger('workflow_run_routes')

# 项目路径
web_dir = Path(__file__).parent.parent
project_dir = web_dir.parent
sys.path.insert(0, str(project_dir))

workflow_run_bp = Blueprint('workflow_run', __name__, url_prefix='/api/workflow/run')


def check_api_config():
    """检查大模型 API 配置"""
    try:
        # 优先检查配置文件（用户通过配置页面设置的）
        config_path = project_dir / "config" / "agent_config.yaml"
        api_key = ''
        base_url = 'https://coding.dashscope.aliyuncs.com/v1'  # 默认值
        
        # 优先从 KeyVault 获取（加密存储）
        try:
            from services.key_vault import get_key_vault
            vault = get_key_vault()
            api_key = vault.get_key('dashscope') or ''
        except Exception as e:
            logger.warning(f"KeyVault 未就绪，尝试从配置文件读取：{e}")
            
            # 降级：从配置文件读取
            if config_path.exists():
                import yaml
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    providers = config.get('providers', {})
                    dashscope = providers.get('dashscope', {})
                    api_key = dashscope.get('api_key_value', '')
                    base_url = dashscope.get('base_url', base_url)
            
            # 再降级：从环境变量读取
            if not api_key:
                api_key = os.getenv('DASHSCOPE_API_KEY', '')
        
        if not api_key:
            return {
                "ok": False,
                "error": "API Key 未配置",
                "detail": "请在配置页面设置 API Key"
            }
        
        # 检查配置文件是否存在
        if not config_path.exists():
            return {
                "ok": False,
                "error": "配置文件不存在",
                "detail": f"缺少文件：{config_path}"
            }
        
        # 尝试导入并测试 API（使用配置文件中的端点）
        import urllib.request
        import json
        
        # 从配置文件读取 dashscope 配置
        dashscope = {}
        if config_path.exists():
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                dashscope = config.get('providers', {}).get('dashscope', {})
        
        # 兼容新旧 API 格式
        if 'coding.dashscope.aliyuncs.com' in base_url:
            # 新版 API（兼容 OpenAI 格式）
            url = f"{base_url}/chat/completions"
            # 使用配置文件中配置的模型，如果没有则使用默认值
            test_model = dashscope.get('models', {}).get('qwen3.5-plus', {}).get('name', 'qwen3.5-plus')
            payload = {
                "model": test_model,
                "messages": [
                    {"role": "user", "content": "Hi"}
                ],
                "max_tokens": 1,
                "stream": False
            }
        else:
            # 旧版 API
            url = f"{base_url}/services/aigc/text-generation/generation"
            payload = {
                "model": "qwen-turbo",
                "input": {
                    "messages": [
                        {"role": "user", "content": "Hi"}
                    ]
                },
                "parameters": {
                    "max_tokens": 1
                }
            }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                # 兼容新旧 API 格式
                if 'output' in result or 'request_id' in result or 'choices' in result:
                    model_name = 'qwen-plus' if 'coding.dashscope' in base_url else 'qwen-turbo'
                    return {
                        "ok": True,
                        "message": "API 连接测试成功",
                        "model": model_name
                    }
        except urllib.error.HTTPError as e:
            error_code = e.code
            if error_code == 401:
                return {
                    "ok": False,
                    "error": "API Key 无效",
                    "detail": "请检查 API Key 是否正确"
                }
            elif error_code == 403:
                return {
                    "ok": False,
                    "error": "API 权限不足",
                    "detail": "请检查账户余额和权限"
                }
            elif error_code == 429:
                return {
                    "ok": True,  # 429 说明 API Key 是有效的，只是限流
                    "message": "API 连接成功（当前限流）",
                    "warning": "API 调用频率过高"
                }
            else:
                return {
                    "ok": False,
                    "error": f"API 返回错误 ({error_code})",
                    "detail": str(e)
                }
        except Exception as e:
            error_msg = str(e)
            return {
                "ok": False,
                "error": "API 连接失败",
                "detail": error_msg
            }
        except Exception as e:
            error_msg = str(e)
            if '401' in error_msg:
                return {
                    "ok": False,
                    "error": "API Key 无效",
                    "detail": "请检查 API Key 是否正确"
                }
            elif '403' in error_msg:
                return {
                    "ok": False,
                    "error": "API 权限不足",
                    "detail": "请检查账户余额和权限"
                }
            else:
                return {
                    "ok": False,
                    "error": "API 连接失败",
                    "detail": error_msg
                }
        
        return {
            "ok": True,
            "message": "API 配置检查通过"
        }
        
    except Exception as e:
        return {
            "ok": False,
            "error": "配置检查异常",
            "detail": str(e)
        }


def check_workflow_script():
    """检查工作流脚本是否存在"""
    script_path = project_dir / "workflow_orchestrator.py"
    if not script_path.exists():
        return {
            "ok": False,
            "error": "工作流脚本不存在",
            "detail": f"缺少文件：{script_path}"
        }
    
    return {
        "ok": True,
        "path": str(script_path)
    }


def get_workflow_status():
    """获取工作流运行状态"""
    pid_file = project_dir / "workflow.pid"
    
    if not pid_file.exists():
        return {
            "running": False,
            "status": "idle"
        }
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # 检查进程是否存在
        os.kill(pid, 0)
        
        return {
            "running": True,
            "status": "running",
            "pid": pid
        }
    except (ProcessLookupError, ValueError):
        # 进程不存在，清理 PID 文件
        pid_file.unlink(missing_ok=True)
        return {
            "running": False,
            "status": "crashed"
        }
    except Exception as e:
        return {
            "running": False,
            "status": "unknown",
            "error": str(e)
        }


@workflow_run_bp.route('/check', methods=['GET'])
def preflight_check():
    """启动前检查"""
    results = {
        "api_config": check_api_config(),
        "script": check_workflow_script(),
        "status": get_workflow_status()
    }
    
    # 判断是否可以启动
    can_start = (
        results["api_config"]["ok"] and
        results["script"]["ok"] and
        not results["status"]["running"]
    )
    
    return jsonify({
        "success": True,
        "data": {
            "checks": results,
            "can_start": can_start
        }
    })


def verify_admin_key(provided_key):
    """验证管理员密钥"""
    if not provided_key:
        return False
    
    # 从环境变量获取预设密钥
    env_key = os.getenv('WEB_ADMIN_KEY', '')
    
    if not env_key:
        # 如果没有配置密钥，则不验证（兼容旧版本）
        logger.warning("WEB_ADMIN_KEY 未配置，跳过密钥验证")
        return True
    
    # 比较密钥（使用常量时间比较防止时序攻击）
    import hmac
    return hmac.compare_digest(provided_key.strip(), env_key.strip())


@workflow_run_bp.route('/start', methods=['POST'])
def start_workflow():
    """启动知识生成工作流"""
    try:
        # 1. 验证管理员密钥（如果配置了 WEB_ADMIN_KEY）
        data = request.get_json() or {}
        admin_key = data.get('admin_key', '')
        
        if not verify_admin_key(admin_key):
            logger.warning(f"❌ 密钥验证失败：IP={request.remote_addr}")
            return jsonify({
                "success": False,
                "error": "密钥验证失败",
                "detail": "管理员密钥错误，无权执行此操作"
            }), 403
        
        # 2. 检查是否已经在运行
        status = get_workflow_status()
        if status["running"]:
            return jsonify({
                "success": False,
                "error": "工作流已在运行中",
                "detail": f"进程 ID: {status.get('pid', 'unknown')}"
            }), 400
        
        # 3. 前置检查
        api_check = check_api_config()
        if not api_check["ok"]:
            return jsonify({
                "success": False,
                "error": "API 配置检查失败",
                "detail": api_check.get("error", "") + ": " + api_check.get("detail", "")
            }), 400
        
        script_check = check_workflow_script()
        if not script_check["ok"]:
            return jsonify({
                "success": False,
                "error": "脚本检查失败",
                "detail": script_check.get("error", "") + ": " + script_check.get("detail", "")
            }), 400
        
        # 4. 获取请求参数
        layers = data.get('layers', [1, 2, 3, 4, 5])
        regenerate = data.get('regenerate', True)
        
        # 4. 启动工作流进程
        script_path = script_check["path"]
        log_dir = project_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"workflow_{Path(__file__).stem}.log"
        
        # 构建命令
        cmd = [
            sys.executable,
            script_path,
            "--layers", ",".join(map(str, layers)),
            "--regenerate" if regenerate else "--skip-existing"
        ]
        
        # 启动后台进程
        with open(log_file, 'w') as log:
            process = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=subprocess.STDOUT,
                cwd=project_dir,
                start_new_session=True
            )
        
        # 保存 PID
        pid_file = project_dir / "workflow.pid"
        with open(pid_file, 'w') as f:
            f.write(str(process.pid))
        
        return jsonify({
            "success": True,
            "message": "工作流已启动",
            "data": {
                "pid": process.pid,
                "log_file": str(log_file),
                "estimated_time": "45-60 分钟",
                "estimated_calls": "100-150 次 API 调用"
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "启动失败",
            "detail": str(e)
        }), 500


@workflow_run_bp.route('/stop', methods=['POST'])
def stop_workflow():
    """停止工作流"""
    try:
        pid_file = project_dir / "workflow.pid"
        
        if not pid_file.exists():
            return jsonify({
                "success": False,
                "error": "工作流未运行"
            }), 400
        
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # 发送终止信号
        os.killpg(os.getpgid(pid), signal.SIGTERM)
        
        # 清理 PID 文件
        pid_file.unlink()
        
        return jsonify({
            "success": True,
            "message": "工作流已停止"
        })
        
    except ProcessLookupError:
        pid_file.unlink(missing_ok=True)
        return jsonify({
            "success": False,
            "error": "进程不存在"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "停止失败",
            "detail": str(e)
        }), 500


@workflow_run_bp.route('/status', methods=['GET'])
def workflow_status():
    """获取工作流状态"""
    status = get_workflow_status()
    
    # 如果运行中，尝试读取日志
    if status["running"]:
        log_dir = project_dir / "logs"
        log_files = sorted(log_dir.glob("workflow_*.log"))
        
        if log_files:
            latest_log = log_files[-1]
            try:
                with open(latest_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # 读取最后 50 行
                    status["recent_logs"] = lines[-50:]
                    status["log_file"] = str(latest_log)
            except:
                pass
    
    return jsonify({
        "success": True,
        "data": status
    })
