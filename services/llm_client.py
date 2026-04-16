#!/usr/bin/env python3
"""
LLM 客户端（优化版 - httpx + async）

统一的 LLM 调用客户端，支持：
- DashScope/Qwen 等兼容 OpenAI API 格式的模型
- httpx 异步/同步请求
- 自动重试机制
- 审计日志记录
- Token 用量统计
- 成本估算
- 事件总线集成
- 请求缓存（相同prompt跳过重复调用）
"""

import os
import json
import time
import hashlib
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from functools import lru_cache

import httpx


class LLMClient:
    """
    LLM 客户端（httpx 版）

    支持：
    - 同步调用 (chat)
    - 异步调用 (async_chat)
    - 请求缓存
    - 统计信息
    """

    _global_stats = {
        "total_calls": 0,
        "success_calls": 0,
        "failed_calls": 0,
        "total_tokens": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_cost": 0.0,
        "cached_calls": 0,
        "by_model": {},
        "by_agent": {},
    }

    _price_config = {
        "qwen3.5-plus": {"input": 0.004, "output": 0.012},
        "qwen-plus": {"input": 0.002, "output": 0.006},
        "qwen-max": {"input": 0.008, "output": 0.024},
        "qwen-turbo": {"input": 0.001, "output": 0.003},
        "deepseek-chat": {"input": 0.001, "output": 0.002},
        "deepseek-coder": {"input": 0.001, "output": 0.002},
        "default": {"input": 0.002, "output": 0.006},
    }

    def __init__(
        self,
        api_key: str,
        base_url: str = os.environ.get(
            "DASHSCOPE_BASE_URL", "https://coding.dashscope.aliyuncs.com/v1"
        ),
        model: str = "qwen-plus",
        temperature: float = 0.7,
        max_tokens: int = 4000,
        timeout: int = 120,
        agent_name: str = "unknown",
        enable_cache: bool = True,
        cache_ttl: int = 3600,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.agent_name = agent_name
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl

        self._cache: Dict[str, Dict] = {}

        self._client: Optional[httpx.Client] = None
        self._async_client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
            )
        return self._client

    async def _get_async_client(self) -> httpx.AsyncClient:
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
            )
        return self._async_client

    def _build_cache_key(self, messages: List[Dict], system_prompt: str) -> str:
        content = json.dumps(
            {"system": system_prompt, "messages": messages}, sort_keys=True
        )
        return hashlib.md5(content.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        if not self.enable_cache:
            return None

        cached = self._cache.get(cache_key)
        if cached:
            elapsed = time.time() - cached["timestamp"]
            if elapsed < self.cache_ttl:
                LLMClient._global_stats["cached_calls"] += 1
                return cached["result"]
            else:
                del self._cache[cache_key]
        return None

    def _save_to_cache(self, cache_key: str, result: Dict):
        if self.enable_cache and result.get("success"):
            self._cache[cache_key] = {"result": result, "timestamp": time.time()}

    def _build_payload(self, messages: List[Dict], system_prompt: str = "") -> Dict:
        if system_prompt:
            full_messages = [{"role": "system", "content": system_prompt}] + messages
        else:
            full_messages = messages

        return {
            "model": self.model,
            "messages": full_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    def _update_stats(
        self, success: bool, usage: Dict = None, cost: float = 0, cached: bool = False
    ):
        LLMClient._global_stats["total_calls"] += 1

        if success:
            LLMClient._global_stats["success_calls"] += 1
            if usage:
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)

                LLMClient._global_stats["total_tokens"] += total_tokens
                LLMClient._global_stats["prompt_tokens"] += prompt_tokens
                LLMClient._global_stats["completion_tokens"] += completion_tokens

                if self.model not in LLMClient._global_stats["by_model"]:
                    LLMClient._global_stats["by_model"][self.model] = {
                        "calls": 0,
                        "tokens": 0,
                        "cost": 0.0,
                    }
                LLMClient._global_stats["by_model"][self.model]["calls"] += 1
                LLMClient._global_stats["by_model"][self.model]["tokens"] += (
                    total_tokens
                )
                LLMClient._global_stats["by_model"][self.model]["cost"] += cost

                if self.agent_name not in LLMClient._global_stats["by_agent"]:
                    LLMClient._global_stats["by_agent"][self.agent_name] = {
                        "calls": 0,
                        "tokens": 0,
                        "cost": 0.0,
                        "success": 0,
                        "failed": 0,
                    }
                LLMClient._global_stats["by_agent"][self.agent_name]["calls"] += 1
                LLMClient._global_stats["by_agent"][self.agent_name]["tokens"] += (
                    total_tokens
                )
                LLMClient._global_stats["by_agent"][self.agent_name]["cost"] += cost
                LLMClient._global_stats["by_agent"][self.agent_name]["success"] += 1

                LLMClient._global_stats["total_cost"] += cost
        else:
            LLMClient._global_stats["failed_calls"] += 1
            if self.agent_name in LLMClient._global_stats["by_agent"]:
                LLMClient._global_stats["by_agent"][self.agent_name]["failed"] += 1

    def _publish_event(self, event_type: str, data: Dict):
        try:
            from utils.event_bus import publish_event, EventType

            event_map = {
                "start": EventType.LLM_CALL_START,
                "complete": EventType.LLM_CALL_COMPLETE,
                "error": EventType.LLM_CALL_ERROR,
            }
            publish_event(event_map.get(event_type), data, source="llm_client")
        except Exception:
            pass

    def _log_audit(
        self,
        success: bool,
        usage: Dict = None,
        cost: float = 0,
        duration_ms: float = 0,
        retries: int = 0,
        error: str = None,
    ):
        try:
            from services.llm_audit_log import log_llm_call

            log_llm_call(
                agent_name=self.agent_name,
                model=self.model,
                base_url=self.base_url,
                success=success,
                prompt_tokens=usage.get("prompt_tokens", 0) if usage else 0,
                completion_tokens=usage.get("completion_tokens", 0) if usage else 0,
                total_tokens=usage.get("total_tokens", 0) if usage else 0,
                cost=cost,
                duration_ms=duration_ms,
                retries=retries,
                error_message=error,
            )
        except Exception:
            pass

    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> Dict[str, Any]:
        cache_key = self._build_cache_key(messages, system_prompt)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            cached_result["cached"] = True
            return cached_result

        url = f"{self.base_url}/chat/completions"
        payload = self._build_payload(messages, system_prompt)

        start_time = time.time()
        last_error = None

        self._publish_event(
            "start",
            {
                "agent": self.agent_name,
                "model": self.model,
                "messages_count": len(payload["messages"]),
            },
        )

        client = self._get_client()

        for attempt in range(max_retries):
            try:
                response = client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()

                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    usage = result.get("usage", {})

                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    price = self._price_config.get(
                        self.model, self._price_config["default"]
                    )
                    cost = (
                        prompt_tokens * price["input"]
                        + completion_tokens * price["output"]
                    ) / 1000

                    duration_ms = (time.time() - start_time) * 1000

                    self._update_stats(True, usage, cost)
                    self._log_audit(True, usage, cost, duration_ms, attempt)

                    result_data = {
                        "success": True,
                        "content": content,
                        "model": self.model,
                        "usage": usage,
                        "cost": cost,
                        "duration_ms": duration_ms,
                        "cached": False,
                    }

                    self._save_to_cache(cache_key, result_data)

                    self._publish_event(
                        "complete",
                        {
                            "agent": self.agent_name,
                            "model": self.model,
                            "tokens": usage.get("total_tokens", 0),
                            "cost": cost,
                            "duration_ms": duration_ms,
                            "success": True,
                        },
                    )

                    return result_data
                else:
                    last_error = result.get("error", {}).get("message", "Unknown error")

            except httpx.HTTPStatusError as e:
                last_error = (
                    f"HTTP Error {e.response.status_code}: {e.response.text[:200]}"
                )
            except httpx.RequestError as e:
                last_error = f"Request Error: {str(e)}"
            except json.JSONDecodeError as e:
                last_error = f"JSON 解析错误：{str(e)}"
            except Exception as e:
                last_error = f"未知错误：{str(e)}"

            if attempt < max_retries - 1:
                wait_time = retry_delay * (2**attempt)
                time.sleep(wait_time)

        duration_ms = (time.time() - start_time) * 1000
        self._update_stats(False)
        self._log_audit(
            False, duration_ms=duration_ms, retries=max_retries, error=last_error
        )

        self._publish_event(
            "error",
            {
                "agent": self.agent_name,
                "model": self.model,
                "error": last_error,
                "retries": max_retries,
                "duration_ms": duration_ms,
            },
        )

        return {
            "success": False,
            "error": f"最大重试次数已用尽 - {last_error}",
            "retries": max_retries,
            "duration_ms": duration_ms,
        }

    async def async_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> Dict[str, Any]:
        cache_key = self._build_cache_key(messages, system_prompt)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            cached_result["cached"] = True
            return cached_result

        url = f"{self.base_url}/chat/completions"
        payload = self._build_payload(messages, system_prompt)

        start_time = time.time()
        last_error = None

        self._publish_event(
            "start",
            {
                "agent": self.agent_name,
                "model": self.model,
                "messages_count": len(payload["messages"]),
            },
        )

        client = await self._get_async_client()

        for attempt in range(max_retries):
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()

                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    usage = result.get("usage", {})

                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    price = self._price_config.get(
                        self.model, self._price_config["default"]
                    )
                    cost = (
                        prompt_tokens * price["input"]
                        + completion_tokens * price["output"]
                    ) / 1000

                    duration_ms = (time.time() - start_time) * 1000

                    self._update_stats(True, usage, cost)
                    self._log_audit(True, usage, cost, duration_ms, attempt)

                    result_data = {
                        "success": True,
                        "content": content,
                        "model": self.model,
                        "usage": usage,
                        "cost": cost,
                        "duration_ms": duration_ms,
                        "cached": False,
                    }

                    self._save_to_cache(cache_key, result_data)

                    self._publish_event(
                        "complete",
                        {
                            "agent": self.agent_name,
                            "model": self.model,
                            "tokens": usage.get("total_tokens", 0),
                            "cost": cost,
                            "duration_ms": duration_ms,
                            "success": True,
                        },
                    )

                    return result_data
                else:
                    last_error = result.get("error", {}).get("message", "Unknown error")

            except httpx.HTTPStatusError as e:
                last_error = (
                    f"HTTP Error {e.response.status_code}: {e.response.text[:200]}"
                )
            except httpx.RequestError as e:
                last_error = f"Request Error: {str(e)}"
            except json.JSONDecodeError as e:
                last_error = f"JSON 解析错误：{str(e)}"
            except Exception as e:
                last_error = f"未知错误：{str(e)}"

            if attempt < max_retries - 1:
                wait_time = retry_delay * (2**attempt)
                await asyncio.sleep(wait_time)

        duration_ms = (time.time() - start_time) * 1000
        self._update_stats(False)
        self._log_audit(
            False, duration_ms=duration_ms, retries=max_retries, error=last_error
        )

        self._publish_event(
            "error",
            {
                "agent": self.agent_name,
                "model": self.model,
                "error": last_error,
                "retries": max_retries,
                "duration_ms": duration_ms,
            },
        )

        return {
            "success": False,
            "error": f"最大重试次数已用尽 - {last_error}",
            "retries": max_retries,
            "duration_ms": duration_ms,
        }

    def close(self):
        if self._client:
            self._client.close()
            self._client = None

    async def async_close(self):
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        return {
            "total_calls": cls._global_stats["total_calls"],
            "success_calls": cls._global_stats["success_calls"],
            "failed_calls": cls._global_stats["failed_calls"],
            "cached_calls": cls._global_stats["cached_calls"],
            "success_rate": f"{cls._global_stats['success_calls'] / max(cls._global_stats['total_calls'], 1) * 100:.1f}%",
            "total_tokens": cls._global_stats["total_tokens"],
            "prompt_tokens": cls._global_stats["prompt_tokens"],
            "completion_tokens": cls._global_stats["completion_tokens"],
            "total_cost": f"¥{cls._global_stats['total_cost']:.4f}",
            "by_model": cls._global_stats["by_model"],
            "by_agent": cls._global_stats["by_agent"],
        }

    @classmethod
    def reset_stats(cls):
        cls._global_stats = {
            "total_calls": 0,
            "success_calls": 0,
            "failed_calls": 0,
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_cost": 0.0,
            "cached_calls": 0,
            "by_model": {},
            "by_agent": {},
        }

    @classmethod
    def print_stats(cls):
        stats = cls.get_stats()
        print("\n" + "=" * 60)
        print("📊 LLM 调用统计")
        print("=" * 60)
        print(f"   总调用次数：{stats['total_calls']}")
        print(
            f"   成功：{stats['success_calls']} | 失败：{stats['failed_calls']} | 缓存命中：{stats['cached_calls']}"
        )
        print(f"   成功率：{stats['success_rate']}")
        print(f"   总 Token 数：{stats['total_tokens']:,}")
        print(f"   - Prompt: {stats['prompt_tokens']:,}")
        print(f"   - Completion: {stats['completion_tokens']:,}")
        print(f"   预估成本：{stats['total_cost']}")

        if stats["by_model"]:
            print("\n   按模型统计:")
            for model, data in stats["by_model"].items():
                print(
                    f"   - {model}: {data['calls']}次，{data['tokens']:,} tokens, ¥{data['cost']:.4f}"
                )

        if stats["by_agent"]:
            print("\n   按 Agent 统计:")
            for agent, data in stats["by_agent"].items():
                print(
                    f"   - {agent}: {data['calls']}次，成功{data['success']}, 失败{data['failed']}, {data['tokens']:,} tokens"
                )

        print("=" * 60 + "\n")

    @classmethod
    async def batch_chat(
        cls,
        clients: List["LLMClient"],
        messages_list: List[List[Dict]],
        system_prompts: List[str] = None,
    ) -> List[Dict]:
        if system_prompts is None:
            system_prompts = [""] * len(messages_list)

        tasks = [
            client.async_chat(messages, system_prompt)
            for client, messages, system_prompt in zip(
                clients, messages_list, system_prompts
            )
        ]

        return await asyncio.gather(*tasks)
