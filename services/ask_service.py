#!/usr/bin/env python3
"""
Ask Service - Web 问答助手服务（轻量级优化版）

核心功能：
- 对话历史管理（内存 + 文件持久化）
- Agent 回复生成（使用 LLMClient）
- 多轮对话上下文注入
- 会话管理

优化改进：
- 移除SQLite依赖，使用文件存储
- 多轮对话上下文注入
- 配置热更新支持
"""

import os
import json
import yaml
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger("ask_service")


class AskService:
    """Ask 服务 - Web 问答助手"""

    MAX_HISTORY_LENGTH = 10
    HISTORY_FILE = Path("data/chat_history/chat_history.json")

    def __init__(self, config_path: str = "config/agent_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._histories: Dict[str, List[Dict]] = {}
        self.agents = self._init_agents()
        self._llm_clients: Dict[str, Any] = {}
        self._api_config_cache: Dict = {}
        self._config_loaded_time: float = 0

        self.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._load_history_from_file()

    def _load_config(self) -> Dict:
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {}

    def _load_history_from_file(self):
        """从文件加载对话历史"""
        if self.HISTORY_FILE.exists():
            try:
                with open(self.HISTORY_FILE, "r", encoding="utf-8") as f:
                    self._histories = json.load(f)
                logger.info(f"已加载对话历史：{len(self._histories)} 个会话")
            except Exception as e:
                logger.warning(f"加载对话历史失败：{e}")

    def _save_history_to_file(self):
        """保存对话历史到文件"""
        try:
            with open(self.HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self._histories, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存对话历史失败：{e}")

    def _get_api_config(self) -> Dict[str, str]:
        """获取API配置（引用统一模块）"""
        now = time.time()
        if self._api_config_cache and (now - self._config_loaded_time) < 300:
            return self._api_config_cache

        from services.agent_factory import get_api_config
        api_key, base_url = get_api_config(self.config)

        model = self.config.get("global", {}).get("default_model", "qwen3.5-plus")

        self._api_config_cache = {
            "api_key": api_key,
            "base_url": base_url,
            "model": model,
        }
        self._config_loaded_time = now

        return self._api_config_cache

    def _get_llm_client(self, agent_name: str) -> Any:
        """获取LLM客户端（按Agent缓存）"""
        if agent_name not in self._llm_clients:
            from services.llm_client import LLMClient

            api_config = self._get_api_config()
            agent_config = self.agents.get(agent_name, {})

            self._llm_clients[agent_name] = LLMClient(
                api_key=api_config["api_key"],
                base_url=api_config["base_url"],
                model=agent_config.get("model", api_config["model"]),
                agent_name=agent_name,
                enable_cache=True,
            )

        return self._llm_clients[agent_name]

    def _init_agents(self) -> Dict[str, Dict]:
        agents_config = self.config.get("agents", {})
        agents = {}

        for name, conf in agents_config.items():
            if conf.get("enabled", False):
                agents[name] = {
                    "name": name,
                    "role": conf.get("role", "助手"),
                    "system_prompt": conf.get(
                        "system_prompt", "你是一个有帮助的 AI 助手。"
                    ),
                    "layer": conf.get("layer", 0),
                }

        return agents

    def get_available_agents(self) -> List[Dict]:
        return list(self.agents.values())

    def chat(
        self,
        message: str,
        agent_name: str = "master_agent",
        session_id: Optional[str] = None,
        include_history: bool = True,
    ) -> Dict:
        """
        发送消息并获取回复（支持多轮对话上下文）

        Args:
            message: 用户消息
            agent_name: Agent 名称
            session_id: 会话 ID
            include_history: 是否包含历史上下文

        Returns:
            Dict: {success, reply, agent, timestamp, usage, cost}
        """
        try:
            agent = self.agents.get(agent_name, {})
            system_prompt = agent.get("system_prompt", "你是一个有帮助的 AI 助手。")

            messages = self._build_messages(
                message, agent_name, session_id, include_history
            )

            llm_client = self._get_llm_client(agent_name)
            result = llm_client.chat(
                messages=messages, system_prompt=system_prompt, max_retries=2
            )

            if result.get("success"):
                reply = result["content"]
                self._save_history(agent_name, message, reply, session_id)

                return {
                    "success": True,
                    "reply": reply,
                    "agent": agent_name,
                    "timestamp": datetime.now().isoformat(),
                    "usage": result.get("usage", {}),
                    "cost": result.get("cost", 0),
                    "cached": result.get("cached", False),
                }
            else:
                error_msg = result.get("error", "Unknown error")
                logger.error(f"LLM 调用失败：{error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "agent": agent_name,
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"chat 异常：{e}")
            return {
                "success": False,
                "error": str(e),
                "agent": agent_name,
                "timestamp": datetime.now().isoformat(),
            }

    def _build_messages(
        self,
        message: str,
        agent_name: str,
        session_id: Optional[str],
        include_history: bool,
    ) -> List[Dict]:
        """构建消息列表（包含历史上下文）"""
        messages = []

        if include_history:
            history = self.get_history(
                agent_name, limit=self.MAX_HISTORY_LENGTH, session_id=session_id
            )
            for h in history:
                if h["role"] in ["user", "assistant"]:
                    messages.append({"role": h["role"], "content": h["content"]})

        messages.append({"role": "user", "content": message})

        return messages

    def _save_history(
        self,
        agent_name: str,
        user_msg: str,
        reply: str,
        session_id: Optional[str] = None,
    ):
        """保存对话历史"""
        key = f"{agent_name}_{session_id}" if session_id else agent_name
        timestamp = datetime.now().isoformat()

        if key not in self._histories:
            self._histories[key] = []

        self._histories[key].append(
            {"role": "user", "content": user_msg, "timestamp": timestamp}
        )
        self._histories[key].append(
            {"role": "assistant", "content": reply, "timestamp": timestamp}
        )

        if len(self._histories[key]) > self.MAX_HISTORY_LENGTH * 2:
            self._histories[key] = self._histories[key][-self.MAX_HISTORY_LENGTH * 2 :]

        self._save_history_to_file()

    def get_history(
        self,
        agent_name: str = "master_agent",
        limit: int = 10,
        session_id: Optional[str] = None,
    ) -> List[Dict]:
        """获取对话历史"""
        key = f"{agent_name}_{session_id}" if session_id else agent_name
        history = self._histories.get(key, [])
        return history[-limit:] if limit else history

    def clear_history(
        self, agent_name: str = "master_agent", session_id: Optional[str] = None
    ):
        """清空对话历史"""
        key = f"{agent_name}_{session_id}" if session_id else agent_name
        if key in self._histories:
            del self._histories[key]
        self._save_history_to_file()

    def refresh_config(self):
        """刷新配置（强制重新加载）"""
        self._api_config_cache = {}
        self._config_loaded_time = 0
        self._llm_clients.clear()


_instance: Optional[AskService] = None


def get_ask_service() -> AskService:
    """获取 Ask 服务单例"""
    global _instance
    if _instance is None:
        _instance = AskService()
    return _instance
