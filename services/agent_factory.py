#!/usr/bin/env python3
"""
Agent Factory - Agent 创建工厂

统一的 Agent 创建逻辑，从配置文件创建 AsyncSubAgent 实例。
只使用 key_vault 单例获取 API Key。
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

# 确保项目根目录在 path 中
project_dir = Path(__file__).parent.parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

from models.agent import AsyncSubAgent
from services.key_vault import get_key_vault

logger = logging.getLogger("agent_factory")


def get_api_config(config: Dict = None) -> Tuple[str, str]:
    """
    获取 API 配置（统一入口）

    Args:
        config: 可选的配置字典，用于获取 base_url

    Returns:
        Tuple[str, str]: (api_key, base_url)
    """
    api_key = ""
    base_url = "https://coding.dashscope.aliyuncs.com/v1"

    # 优先使用 key_vault
    try:
        vault = get_key_vault()
        api_key = vault.get_key("dashscope") or ""
    except Exception as e:
        logger.warning(f"⚠️  key_vault 获取失败：{e}")

    # 如果 key_vault 没有，尝试备用方式
    if not api_key:
        if config:
            providers = config.get("providers", {})
            dashscope = providers.get("dashscope", {})
            api_key = dashscope.get("api_key_value", "") or os.getenv("DASHSCOPE_API_KEY", "")
            base_url = dashscope.get("base_url", base_url)
        else:
            api_key = os.getenv("DASHSCOPE_API_KEY", "")

    return api_key, base_url


def create_agent(
    agent_name: str,
    agent_config: Dict,
    api_key: str,
    base_url: str,
    layer: int = None,
    enable_cache: bool = True,
) -> AsyncSubAgent:
    """
    创建单个 Agent

    Args:
        agent_name: Agent 名称
        agent_config: Agent 配置字典
        api_key: API Key
        base_url: API Base URL
        layer: 层级（可选，从配置中获取）
        enable_cache: 是否启用缓存

    Returns:
        AsyncSubAgent: Agent 实例
    """
    return AsyncSubAgent(
        name=agent_name,
        role=agent_config.get("role", "专家"),
        layer=layer or agent_config.get("layer", 0),
        system_prompt=agent_config.get("system_prompt", ""),
        model=agent_config.get("model", "qwen3.5-plus"),
        api_key=api_key,
        base_url=base_url,
        enable_cache=enable_cache,
    )


def create_agents_from_config(
    config: Dict,
    enable_cache: bool = True,
    agent_filter: Dict[str, int] = None,
    min_layer: int = 0,
) -> Dict[str, AsyncSubAgent]:
    """
    从配置创建多个 Agent

    Args:
        config: 完整配置字典
        enable_cache: 是否启用缓存
        agent_filter: 可选的 Agent 过滤器，指定每个 Agent 的层级
        min_layer: 最小层级过滤（默认 0，即所有启用的 Agent）

    Returns:
        Dict[str, AsyncSubAgent]: Agent 名称到实例的映射
    """
    api_key, base_url = get_api_config(config)

    agents_config = config.get("agents", {})
    agents = {}

    for agent_name, agent_conf in agents_config.items():
        # 检查是否启用
        if not agent_conf.get("enabled", False):
            continue

        # 获取层级（确保有默认值）
        if agent_filter and agent_name in agent_filter:
            layer = agent_filter[agent_name].get("layer", 0)
        else:
            layer = agent_conf.get("layer", 0)

        # 层级过滤
        if layer is None or layer < min_layer:
            continue

        # 创建 Agent
        agents[agent_name] = create_agent(
            agent_name=agent_name,
            agent_config=agent_conf,
            api_key=api_key,
            base_url=base_url,
            layer=layer,
            enable_cache=enable_cache,
        )

    logger.info(f"✅ 创建 {len(agents)} 个异步子 Agent")
    return agents


def create_classifier_agent(config: Dict) -> Optional[AsyncSubAgent]:
    """
    创建主题分类 Agent

    Args:
        config: 完整配置字典

    Returns:
        AsyncSubAgent: 分类 Agent 实例
    """
    classifier_config = config.get("agents", {}).get("topic_classifier", {})

    if not classifier_config.get("enabled", False):
        return None

    api_key, base_url = get_api_config(config)

    return create_agent(
        agent_name="topic_classifier",
        agent_config=classifier_config,
        api_key=api_key,
        base_url=base_url,
        layer=0,
        enable_cache=False,  # 分类不需要缓存
    )