#!/usr/bin/env python3
"""
AsyncSubAgent - 异步子 Agent

提供异步 LLM 调用能力的 Agent 封装。
"""

import sys
from pathlib import Path
from typing import Dict

# 确保项目根目录在 path 中
project_dir = Path(__file__).parent.parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

from services.llm_client import LLMClient


class AsyncSubAgent:
    """异步子 Agent"""

    def __init__(
        self,
        name: str,
        role: str,
        layer: int,
        system_prompt: str,
        model: str = "qwen-plus",
        api_key: str = "",
        base_url: str = "",
        enable_cache: bool = True,
    ):
        self.name = name
        self.role = role
        self.layer = layer
        self.system_prompt = system_prompt

        self.llm_client = LLMClient(
            api_key=api_key,
            base_url=base_url,
            model=model,
            agent_name=name,
            enable_cache=enable_cache,
        )

    async def ask(self, question: str, max_retries: int = 2) -> Dict:
        """向 Agent 发送问题并获取回答"""
        user_message = question

        result = await self.llm_client.async_chat(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=self.system_prompt,
            max_retries=max_retries,
        )

        if result.get("success"):
            return {
                "success": True,
                "content": result["content"],
                "agent": self.name,
                "layer": self.layer,
                "tokens": result.get("usage", {}).get("total_tokens", 0),
                "cached": result.get("cached", False),
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unknown error"),
                "agent": self.name,
            }

    async def close(self):
        """关闭 LLM 客户端连接"""
        await self.llm_client.async_close()