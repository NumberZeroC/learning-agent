#!/usr/bin/env python3
"""
工作流成果展示 API

支持：
- 获取所有已完成的层（合并文件）
- 获取单个层的详细信息
- 获取单个主题的详细信息
- 获取工作流运行状态
"""

from flask import Blueprint, jsonify
from pathlib import Path
import sys
import json
import os
import time
from functools import wraps

# 缓存存储
_cache = {}
_CACHE_TTL = 14400  # 4 小时 = 14400 秒

def cached(ttl=None):
    """缓存装饰器"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cache_key = f"{f.__name__}:{args}:{kwargs}"
            cache_ttl = ttl or _CACHE_TTL
            
            # 检查缓存
            if cache_key in _cache:
                cached_time, cached_data = _cache[cache_key]
                if time.time() - cached_time < cache_ttl:
                    return cached_data
            
            # 执行函数并缓存结果
            result = f(*args, **kwargs)
            _cache[cache_key] = (time.time(), result)
            return result
        return wrapper
    return decorator

# 添加项目路径 - 使用绝对路径避免工作目录问题
web_dir = Path(__file__).resolve().parent.parent
project_dir = web_dir.parent
sys.path.insert(0, str(project_dir))

workflow_bp = Blueprint('workflow', __name__, url_prefix='/api/workflow')

# 工作流结果目录 - 使用相对路径（基于项目根目录）
PROJECT_ROOT = Path(__file__).parent.parent.parent
WORKFLOW_RESULTS_DIR = PROJECT_ROOT / "data" / "workflow_results"


@workflow_bp.route('/layers')
@cached(ttl=_CACHE_TTL)
def get_all_layers():
    """获取所有已完成的层（从合并文件读取）"""
    if not WORKFLOW_RESULTS_DIR.exists():
        return jsonify({
            "success": True,
            "data": {
                "layers": [],
                "total": 0
            }
        })
    
    layers = []
    seen_layers = set()
    
    # 扫描所有合并文件（支持两种命名：layer_X_workflow.json 和 layer_X_merged.json）
    for pattern in ["layer_*_workflow.json", "layer_*_merged.json"]:
        for merged_file in sorted(WORKFLOW_RESULTS_DIR.glob(pattern)):
            try:
                # 提取层号，避免重复
                layer_num = int(merged_file.stem.split('_')[1])
                if layer_num in seen_layers:
                    continue  # 跳过重复的层
                seen_layers.add(layer_num)
                
                with open(merged_file, 'r', encoding='utf-8') as f:
                    layer_data = json.load(f)
                
                layers.append({
                    "layer": layer_data.get('layer', layer_num),
                    "layer_name": layer_data.get('layer_name', ''),
                    "agent": layer_data.get('agent', ''),
                    "topics": layer_data.get('topics', []),
                    "task_count": layer_data.get('task_count', len(layer_data.get('topics', []))),
                    "completed_at": layer_data.get('completed_at', '')
                })
            except Exception as e:
                print(f"读取合并文件失败 {merged_file.name}: {e}")
    
    # 按层号排序
    layers.sort(key=lambda x: x['layer'])
    
    return jsonify({
        "success": True,
        "data": {
            "layers": layers,
            "total": len(layers)
        }
    })


@workflow_bp.route('/layer/<int:layer_num>')
@cached(ttl=_CACHE_TTL)
def get_layer(layer_num: int):
    """获取指定层的详细信息（支持两种文件名）"""
    # 优先查找 workflow.json，其次 merged.json
    merged_file = WORKFLOW_RESULTS_DIR / f"layer_{layer_num}_workflow.json"
    if not merged_file.exists():
        merged_file = WORKFLOW_RESULTS_DIR / f"layer_{layer_num}_merged.json"
    
    if not merged_file.exists():
        return jsonify({
            "success": False,
            "error": f"第{layer_num}层尚未完成"
        }), 404
    
    try:
        with open(merged_file, 'r', encoding='utf-8') as f:
            layer_data = json.load(f)
        
        return jsonify({
            "success": True,
            "data": layer_data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"读取失败：{str(e)}"
        }), 500


@workflow_bp.route('/topic/<int:layer_num>/<int:topic_index>')
@cached(ttl=_CACHE_TTL)
def get_topic(layer_num: int, topic_index: int):
    """获取指定主题的详细信息（支持两种文件名）"""
    # 优先查找 workflow.json，其次 merged.json
    merged_file = WORKFLOW_RESULTS_DIR / f"layer_{layer_num}_workflow.json"
    if not merged_file.exists():
        merged_file = WORKFLOW_RESULTS_DIR / f"layer_{layer_num}_merged.json"
    
    if not merged_file.exists():
        return jsonify({
            "success": False,
            "error": f"第{layer_num}层尚未完成"
        }), 404
    
    try:
        with open(merged_file, 'r', encoding='utf-8') as f:
            layer_data = json.load(f)
        
        topics = layer_data.get('topics', [])
        
        # 索引从 0 开始
        if topic_index < 0 or topic_index >= len(topics):
            return jsonify({
                "success": False,
                "error": f"主题索引超出范围 (0-{len(topics)-1})"
            }), 404
        
        topic = topics[topic_index]
        
        return jsonify({
            "success": True,
            "data": topic
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"读取失败：{str(e)}"
        }), 500


@workflow_bp.route('/status')
def get_workflow_status():
    """获取工作流运行状态"""
    # 检查是否有进程在运行
    running = False
    completed_tasks = 0
    
    # 方法 1: 检查 PID 文件（如果有的话）
    pid_file = project_dir / "workflow.pid"
    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # 检查进程是否存在
            os.kill(pid, 0)  # 不发送信号，只检查进程是否存在
            running = True
        except:
            running = False
    
    # 方法 2: 统计已完成的任务数
    if WORKFLOW_RESULTS_DIR.exists():
        for task_file in WORKFLOW_RESULTS_DIR.glob("layer_*_task_*.json"):
            completed_tasks += 1
    
    # 方法 3: 检查日志文件（最近 5 分钟有更新）
    import time
    log_dir = project_dir / "logs"
    if log_dir.exists():
        current_time = time.time()
        for log_file in log_dir.glob("workflow_*.log"):
            try:
                mtime = log_file.stat().st_mtime
                if current_time - mtime < 300:  # 5 分钟内
                    running = True
                    break
            except:
                pass
    
    return jsonify({
        "success": True,
        "data": {
            "running": running,
            "completed_tasks": completed_tasks,
            "results_dir": str(WORKFLOW_RESULTS_DIR)
        }
    })


@workflow_bp.route('/summary')
def get_workflow_summary():
    """获取工作流汇总统计"""
    if not WORKFLOW_RESULTS_DIR.exists():
        return jsonify({
            "success": True,
            "data": {
                "total_layers": 0,
                "total_topics": 0,
                "total_tasks": 0,
                "layers": {}
            }
        })
    
    total_layers = 0
    total_topics = 0
    total_tasks = 0
    layer_stats = {}
    
    # 统计合并文件
    for merged_file in WORKFLOW_RESULTS_DIR.glob("layer_*_merged.json"):
        try:
            with open(merged_file, 'r', encoding='utf-8') as f:
                layer_data = json.load(f)
            
            layer_num = layer_data.get('layer', 0)
            topic_count = layer_data.get('task_count', len(layer_data.get('topics', [])))
            
            total_layers += 1
            total_topics += topic_count
            
            layer_stats[str(layer_num)] = {
                "layer_name": layer_data.get('layer_name', ''),
                "topics": topic_count,
                "completed_at": layer_data.get('completed_at', '')
            }
        except:
            pass
    
    # 统计任务文件
    task_files = list(WORKFLOW_RESULTS_DIR.glob("layer_*_task_*.json"))
    total_tasks = len(task_files)
    
    return jsonify({
        "success": True,
        "data": {
            "total_layers": total_layers,
            "total_topics": total_topics,
            "total_tasks": total_tasks,
            "layers": layer_stats
        }
    })


# 注册蓝图
def register_blueprint(app):
    """注册蓝图到 Flask 应用"""
    app.register_blueprint(workflow_bp)
