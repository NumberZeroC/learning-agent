#!/usr/bin/env python3
"""
自定义主题 Web API

支持：
- 生成自定义主题
- 智能分类主题
- 列出已生成的主题
- 获取主题详情
"""

from flask import Blueprint, jsonify, request, render_template
from pathlib import Path
import sys
import logging
from functools import wraps

web_dir = Path(__file__).parent.parent
project_dir = web_dir.parent
sys.path.insert(0, str(project_dir))

from custom_topic_generator import CustomTopicGenerator

logger = logging.getLogger("custom_topic_routes")

custom_bp = Blueprint("custom", __name__, url_prefix="/api/custom")

_generator = None


def get_generator():
    global _generator
    if _generator is None:
        _generator = CustomTopicGenerator()
        _generator.initialize()
    return _generator


@custom_bp.route("/")
def custom_topic_page():
    """自定义主题生成页面"""
    return render_template("custom_topic.html")


@custom_bp.route("/generate", methods=["POST"])
def generate_custom_topic():
    """
    生成自定义主题
    
    Request:
    {
        "topic": "微服务架构",
        "agent": "engineering_worker",  // 可选
        "description": "分布式系统设计模式",  // 可选
        "skip_details": false,  // 可选
        "skip_relation": true   // 可选
    }
    
    Response:
    {
        "success": true,
        "data": {
            "topic_id": "custom_20260419_001",
            "topic_name": "微服务架构",
            "agent": "engineering_worker",
            "keypoint_count": 15,
            "knowledge": {...}
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "请提供请求参数"}), 400
        
        topic = data.get("topic")
        if not topic:
            return jsonify({"success": False, "error": "主题名称不能为空"}), 400
        
        agent = data.get("agent")
        description = data.get("description", "")
        skip_details = data.get("skip_details", False)
        skip_relation = data.get("skip_relation", True)
        
        generator = get_generator()
        
        result = generator.generate(
            topic=topic,
            agent=agent,
            description=description,
            skip_details=skip_details,
            skip_relation=skip_relation,
        )
        
        if result.success:
            return jsonify({
                "success": True,
                "data": {
                    "topic_id": result.topic_id,
                    "topic_name": result.topic_name,
                    "agent": result.agent,
                    "keypoint_count": result.keypoint_count,
                    "created_at": result.created_at,
                    "knowledge": result.knowledge,
                }
            })
        else:
            return jsonify({"success": False, "error": result.error}), 500
            
    except Exception as e:
        logger.error(f"生成失败：{e}")
        return jsonify({"success": False, "error": str(e)}), 500


@custom_bp.route("/classify", methods=["POST"])
def classify_topic():
    """
    智能分类主题
    
    Request:
    {
        "topic": "微服务架构",
        "description": "分布式系统设计"  // 可选
    }
    
    Response:
    {
        "success": true,
        "data": {
            "agent": "engineering_worker",
            "reason": "包含工程实践关键词"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "请提供请求参数"}), 400
        
        topic = data.get("topic")
        if not topic:
            return jsonify({"success": False, "error": "主题名称不能为空"}), 400
        
        description = data.get("description", "")
        
        generator = get_generator()
        
        keyword_agent = generator._classify_by_keywords(topic)
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        llm_agent = loop.run_until_complete(generator._classify_topic(topic, description))
        
        final_agent = llm_agent or keyword_agent
        
        agent_names = {
            "theory_worker": "基础理论层",
            "tech_stack_worker": "技术栈层",
            "core_skill_worker": "核心能力层",
            "engineering_worker": "工程实践层",
            "interview_worker": "面试准备层",
        }
        
        reason = f"关键词匹配：{agent_names.get(keyword_agent, '未知')}"
        if llm_agent:
            reason = f"LLM 智能分析：{agent_names.get(llm_agent, '未知')}"
        
        return jsonify({
            "success": True,
            "data": {
                "agent": final_agent,
                "agent_name": agent_names.get(final_agent, "未知"),
                "keyword_agent": keyword_agent,
                "llm_agent": llm_agent,
                "reason": reason,
            }
        })
        
    except Exception as e:
        logger.error(f"分类失败：{e}")
        return jsonify({"success": False, "error": str(e)}), 500


@custom_bp.route("/list", methods=["GET"])
def list_custom_topics():
    """
    列出所有已生成的自定义主题
    
    Response:
    {
        "success": true,
        "data": {
            "topics": [
                {
                    "topic_id": "custom_20260419_001",
                    "topic_name": "微服务架构",
                    "agent": "engineering_worker",
                    "success": true,
                    "created_at": "2026-04-19T..."
                }
            ],
            "total_count": 5,
            "success_count": 4
        }
    }
    """
    try:
        generator = get_generator()
        topics = generator.list_custom_topics()
        
        return jsonify({
            "success": True,
            "data": {
                "topics": topics,
                "total_count": len(topics),
                "success_count": sum(1 for t in topics if t.get("success")),
            }
        })
        
    except Exception as e:
        logger.error(f"获取列表失败：{e}")
        return jsonify({"success": False, "error": str(e)}), 500


@custom_bp.route("/<topic_id>", methods=["GET"])
def get_custom_topic(topic_id):
    """
    获取单个自定义主题详情
    
    Response:
    {
        "success": true,
        "data": {
            "topic_id": "custom_20260419_001",
            "topic_name": "微服务架构",
            "knowledge": {...}
        }
    }
    """
    try:
        generator = get_generator()
        topic_data = generator.get_custom_topic(topic_id)
        
        if not topic_data:
            return jsonify({"success": False, "error": f"未找到主题：{topic_id}"}), 404
        
        return jsonify({
            "success": True,
            "data": {
                "topic_id": topic_id,
                "topic_name": topic_data.get("topic_name", ""),
                "knowledge": topic_data,
            }
        })
        
    except Exception as e:
        logger.error(f"获取主题失败：{e}")
        return jsonify({"success": False, "error": str(e)}), 500


@custom_bp.route("/agents", methods=["GET"])
def get_available_agents():
    """
    获取可用的 Agent 列表
    
    Response:
    {
        "success": true,
        "data": {
            "agents": [
                {"name": "theory_worker", "display_name": "基础理论层", "layer": 1},
                ...
            ]
        }
    }
    """
    try:
        agents = [
            {"name": "theory_worker", "display_name": "基础理论层", "layer": 1, "description": "算法、原理、数学基础"},
            {"name": "tech_stack_worker", "display_name": "技术栈层", "layer": 2, "description": "框架、工具、编程语言"},
            {"name": "core_skill_worker", "display_name": "核心能力层", "layer": 3, "description": "设计、架构、规划能力"},
            {"name": "engineering_worker", "display_name": "工程实践层", "layer": 4, "description": "项目、部署、运维实践"},
            {"name": "interview_worker", "display_name": "面试准备层", "layer": 5, "description": "面试、简历、软技能"},
        ]
        
        return jsonify({
            "success": True,
            "data": {
                "agents": agents,
            }
        })
        
    except Exception as e:
        logger.error(f"获取 Agent 列表失败：{e}")
        return jsonify({"success": False, "error": str(e)}), 500


@custom_bp.route("/config", methods=["GET"])
def get_custom_config():
    """
    获取自定义主题生成配置
    
    Response:
    {
        "success": true,
        "data": {
            "default_skip_relation": true,
            "classifier_enabled": true,
            ...
        }
    }
    """
    try:
        generator = get_generator()
        config = generator.custom_config
        
        gen_config = config.get("generation", {})
        classifier_config = config.get("classifier", {})
        
        return jsonify({
            "success": True,
            "data": {
                "classifier_enabled": classifier_config.get("enabled", True),
                "default_skip_details": not gen_config.get("rounds", {}).get("details", {}).get("enabled", True),
                "default_skip_relation": not gen_config.get("rounds", {}).get("relation", {}).get("enabled", False),
                "rules": classifier_config.get("rules", {}),
            }
        })
        
    except Exception as e:
        logger.error(f"获取配置失败：{e}")
        return jsonify({"success": False, "error": str(e)}), 500