#!/usr/bin/env python3
"""
LLM 客户端（优化版 - 集成事件总线）

统一的 LLM 调用客户端，支持：
- DashScope/Qwen 等兼容 OpenAI API 格式的模型
- 自动重试机制
- 审计日志记录
- Token 用量统计
- 成本估算
- 事件总线集成

优化改进：
- ✅ 发布 LLM 调用事件（开始/完成/错误）
- ✅ 支持事件驱动的通知和监控
"""

import os
import json
import urllib.request
import urllib.error
import time
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime


class LLMClient:
    """
    轻量级 LLM 客户端
    
    支持 DashScope/Qwen 等兼容 OpenAI API 格式的模型
    
    功能：
    - LLM API 调用
    - 调用次数统计
    - Token 用量统计
    - 成本估算
    - 审计日志记录
    """
    
    # 全局统计（所有实例共享）
    _global_stats = {
        "total_calls": 0,
        "success_calls": 0,
        "failed_calls": 0,
        "total_tokens": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_cost": 0.0,
        "by_model": {},
        "by_agent": {}
    }
    
    # 价格配置（每 1K tokens）
    _price_config = {
        "qwen3.5-plus": {"input": 0.004, "output": 0.012},
        "qwen-plus": {"input": 0.002, "output": 0.006},
        "qwen-max": {"input": 0.008, "output": 0.024},
        "qwen-turbo": {"input": 0.001, "output": 0.003},
        "default": {"input": 0.002, "output": 0.006}
    }
    
    def __init__(
        self,
        api_key: str,
        base_url: str = os.environ.get("DASHSCOPE_BASE_URL", "https://coding.dashscope.aliyuncs.com/v1"),
        model: str = "qwen-plus",
        temperature: float = 0.7,
        max_tokens: int = 4000,
        timeout: int = 120,
        agent_name: str = "unknown"
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.agent_name = agent_name
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> Dict[str, Any]:
        """
        发送聊天请求（集成事件总线）
        
        Args:
            messages: 对话消息列表
            system_prompt: 系统提示词
            max_retries: 最大重试次数
            retry_delay: 重试延迟
            
        Returns:
            包含 content 的字典，失败时包含 error
        """
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 构建消息
        if system_prompt:
            full_messages = [{"role": "system", "content": system_prompt}] + messages
        else:
            full_messages = messages
        
        payload = {
            "model": self.model,
            "messages": full_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        last_error = None
        start_time = time.time()
        
        # 📢 发布 LLM 调用开始事件
        try:
            from utils.event_bus import publish_event, EventType
            publish_event(EventType.LLM_CALL_START, {
                "agent": self.agent_name,
                "model": self.model,
                "messages_count": len(full_messages)
            }, source="llm_client")
        except Exception:
            pass  # 事件总线不可用时不影晌主流程
        
        for attempt in range(max_retries):
            try:
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(url, data=data, headers=headers, method='POST')
                
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    
                    # 更新统计
                    LLMClient._global_stats["total_calls"] += 1
                    
                    if 'choices' in result and len(result['choices']) > 0:
                        content = result['choices'][0]['message']['content']
                        usage = result.get('usage', {})
                        
                        # 统计 token 用量
                        prompt_tokens = usage.get('prompt_tokens', 0)
                        completion_tokens = usage.get('completion_tokens', 0)
                        total_tokens = usage.get('total_tokens', 0)
                        
                        LLMClient._global_stats["success_calls"] += 1
                        LLMClient._global_stats["total_tokens"] += total_tokens
                        LLMClient._global_stats["prompt_tokens"] += prompt_tokens
                        LLMClient._global_stats["completion_tokens"] += completion_tokens
                        
                        # 按模型统计
                        if self.model not in LLMClient._global_stats["by_model"]:
                            LLMClient._global_stats["by_model"][self.model] = {
                                "calls": 0,
                                "tokens": 0,
                                "cost": 0.0
                            }
                        LLMClient._global_stats["by_model"][self.model]["calls"] += 1
                        LLMClient._global_stats["by_model"][self.model]["tokens"] += total_tokens
                        
                        # 计算成本
                        price = self._price_config.get(self.model, self._price_config["default"])
                        cost = (prompt_tokens * price["input"] + completion_tokens * price["output"]) / 1000
                        LLMClient._global_stats["by_model"][self.model]["cost"] += cost
                        LLMClient._global_stats["total_cost"] += cost
                        
                        # 按 Agent 统计
                        if self.agent_name not in LLMClient._global_stats["by_agent"]:
                            LLMClient._global_stats["by_agent"][self.agent_name] = {
                                "calls": 0,
                                "tokens": 0,
                                "cost": 0.0,
                                "success": 0,
                                "failed": 0
                            }
                        LLMClient._global_stats["by_agent"][self.agent_name]["calls"] += 1
                        LLMClient._global_stats["by_agent"][self.agent_name]["tokens"] += total_tokens
                        LLMClient._global_stats["by_agent"][self.agent_name]["cost"] += cost
                        LLMClient._global_stats["by_agent"][self.agent_name]["success"] += 1
                        
                        # 记录审计日志
                        try:
                            from services.llm_audit_log import log_llm_call
                            log_llm_call(
                                agent_name=self.agent_name,
                                model=self.model,
                                base_url=self.base_url,
                                success=True,
                                prompt_tokens=prompt_tokens,
                                completion_tokens=completion_tokens,
                                total_tokens=total_tokens,
                                cost=cost,
                                duration_ms=(time.time() - start_time) * 1000,
                                retries=attempt
                            )
                        except Exception as e:
                            pass  # 审计日志记录失败不影响主流程
                        
                        # 📢 发布 LLM 调用完成事件
                        try:
                            from utils.event_bus import publish_event, EventType
                            publish_event(EventType.LLM_CALL_COMPLETE, {
                                "agent": self.agent_name,
                                "model": self.model,
                                "tokens": total_tokens,
                                "cost": cost,
                                "duration_ms": (time.time() - start_time) * 1000,
                                "success": True
                            }, source="llm_client")
                        except Exception:
                            pass
                        
                        return {
                            "success": True,
                            "content": content,
                            "model": self.model,
                            "usage": usage,
                            "cost": cost,
                            "duration_ms": (time.time() - start_time) * 1000
                        }
                    else:
                        error_msg = result.get('error', {}).get('message', 'Unknown error')
                        last_error = error_msg
                        # 失败统计
                        LLMClient._global_stats["failed_calls"] += 1
                        if self.agent_name in LLMClient._global_stats["by_agent"]:
                            LLMClient._global_stats["by_agent"][self.agent_name]["failed"] += 1
                        
            except urllib.error.HTTPError as e:
                last_error = f"HTTP Error {e.code}: {e.reason}"
                
            except urllib.error.URLError as e:
                last_error = f"URL Error: {e.reason}"
                
            except json.JSONDecodeError as e:
                last_error = f"JSON 解析错误：{str(e)}"
                
            except Exception as e:
                last_error = f"未知错误：{str(e)}"
            
            # 失败统计（只在最后一次重试失败时统计）
            if attempt == max_retries - 1:
                LLMClient._global_stats["failed_calls"] += 1
                if self.agent_name in LLMClient._global_stats["by_agent"]:
                    LLMClient._global_stats["by_agent"][self.agent_name]["failed"] += 1
                
                # 记录审计日志（失败）
                try:
                    from services.llm_audit_log import log_llm_call
                    log_llm_call(
                        agent_name=self.agent_name,
                        model=self.model,
                        base_url=self.base_url,
                        success=False,
                        cost=0.0,
                        duration_ms=(time.time() - start_time) * 1000,
                        retries=attempt,
                        error_message=last_error
                    )
                except Exception:
                    pass
            
            # 重试前等待
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                time.sleep(wait_time)
        
        # 📢 发布 LLM 调用错误事件
        try:
            from utils.event_bus import publish_event, EventType
            publish_event(EventType.LLM_CALL_ERROR, {
                "agent": self.agent_name,
                "model": self.model,
                "error": last_error,
                "retries": max_retries,
                "duration_ms": (time.time() - start_time) * 1000
            }, source="llm_client")
        except Exception:
            pass
        
        return {
            "success": False,
            "error": f"最大重试次数已用尽 - {last_error}",
            "retries": max_retries,
            "duration_ms": (time.time() - start_time) * 1000
        }
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """获取全局统计信息"""
        return {
            "total_calls": cls._global_stats["total_calls"],
            "success_calls": cls._global_stats["success_calls"],
            "failed_calls": cls._global_stats["failed_calls"],
            "success_rate": f"{cls._global_stats['success_calls'] / max(cls._global_stats['total_calls'], 1) * 100:.1f}%",
            "total_tokens": cls._global_stats["total_tokens"],
            "prompt_tokens": cls._global_stats["prompt_tokens"],
            "completion_tokens": cls._global_stats["completion_tokens"],
            "total_cost": f"¥{cls._global_stats['total_cost']:.4f}",
            "by_model": cls._global_stats["by_model"],
            "by_agent": cls._global_stats["by_agent"]
        }
    
    @classmethod
    def reset_stats(cls):
        """重置统计信息"""
        cls._global_stats = {
            "total_calls": 0,
            "success_calls": 0,
            "failed_calls": 0,
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_cost": 0.0,
            "by_model": {},
            "by_agent": {}
        }
    
    @classmethod
    def print_stats(cls):
        """打印统计信息"""
        stats = cls.get_stats()
        print("\n" + "="*60)
        print("📊 LLM 调用统计")
        print("="*60)
        print(f"   总调用次数：{stats['total_calls']}")
        print(f"   成功：{stats['success_calls']} | 失败：{stats['failed_calls']}")
        print(f"   成功率：{stats['success_rate']}")
        print(f"   总 Token 数：{stats['total_tokens']:,}")
        print(f"   - Prompt: {stats['prompt_tokens']:,}")
        print(f"   - Completion: {stats['completion_tokens']:,}")
        print(f"   预估成本：{stats['total_cost']}")
        
        if stats['by_model']:
            print("\n   按模型统计:")
            for model, data in stats['by_model'].items():
                print(f"   - {model}: {data['calls']}次，{data['tokens']:,} tokens, ¥{data['cost']:.4f}")
        
        if stats['by_agent']:
            print("\n   按 Agent 统计:")
            for agent, data in stats['by_agent'].items():
                print(f"   - {agent}: {data['calls']}次，成功{data['success']}, 失败{data['failed']}, {data['tokens']:,} tokens")
        
        print("="*60 + "\n")
