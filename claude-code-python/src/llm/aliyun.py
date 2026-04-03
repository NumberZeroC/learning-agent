"""Alibaba Cloud (Aliyun) DashScope provider for Qwen models"""

from __future__ import annotations

import os
from typing import AsyncIterator

import structlog

from ..models.llm import LLMConfig, LLMResponse, ToolCall, Usage
from ..models.messages import Message
from ..models.tools import ToolDefinition
from .base import LLMProvider

logger = structlog.get_logger(__name__)


class AliyunProvider(LLMProvider):
    """
    Alibaba Cloud DashScope API provider for Qwen (通义千问) models.
    
    Supports:
    - qwen-turbo
    - qwen-plus
    - qwen-max
    - qwen-max-longcontext
    
    API Docs: https://help.aliyun.com/zh/dashscope/
    """
    
    # Default model
    DEFAULT_MODEL = os.environ.get("ALIYUN_MODEL", "qwen-plus")
    
    # Model mapping for compatibility
    MODEL_MAPPING = {
        "claude-sonnet-4-20250514": "qwen-plus",
        "claude-opus-4-20250514": "qwen-max",
        "claude-haiku-4-20250514": "qwen-turbo",
    }
    
    # Supported models
    SUPPORTED_MODELS = [
        "qwen-turbo",
        "qwen-plus",
        "qwen-max",
        "qwen-max-longcontext",
        "qwen3.5-plus",  # New model
        "qwen3.5-turbo",
    ]
    
    def __init__(
        self,
        api_key: str | None = None,
        config: LLMConfig | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        super().__init__(config)
        
        # Get API key from environment
        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("ALIYUN_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Aliyun DashScope API key required. Set DASHSCOPE_API_KEY or ALIYUN_API_KEY env var."
            )
        
        # Use DashScope endpoint
        self.base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        
        # Model override
        if model:
            self._model_override = model
        else:
            self._model_override = None
        
        # Lazy client
        self._client = None
    
    @property
    def model(self) -> str:
        """Get current model name"""
        if self._model_override:
            return self._model_override
        
        # Map Claude model to Qwen model
        config_model = self.config.model if self.config else None
        if config_model and config_model in self.MODEL_MAPPING:
            return self.MODEL_MAPPING[config_model]
        
        return self.DEFAULT_MODEL
    
    @property
    def client(self):
        """Lazy load OpenAI-compatible client"""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                
                self._client = AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
            except ImportError:
                raise ImportError(
                    "openai package required. Install with: pip install openai"
                )
        return self._client
    
    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        system: str | None = None,
        config: LLMConfig | None = None,
    ) -> LLMResponse:
        """Send chat request to Aliyun DashScope"""
        
        cfg = self._merge_configs(config)
        
        # Convert messages to OpenAI format
        openai_messages = []
        
        # Add system message
        if system:
            openai_messages.append({"role": "system", "content": system})
        
        # Convert other messages
        for msg in messages:
            openai_messages.append(msg.to_dict())
        
        # Build request
        params = {
            "model": self.model,
            "messages": openai_messages,
            "max_tokens": cfg.max_tokens,
            "temperature": cfg.temperature,
            "top_p": cfg.top_p,
        }
        
        # Add tools if provided
        if tools:
            params["tools"] = [t.to_dict() for t in tools]
            params["tool_choice"] = "auto"
        
        logger.info(
            "Sending Aliyun DashScope request",
            model=self.model,
            message_count=len(openai_messages),
        )
        
        try:
            response = await self.client.chat.completions.create(**params)
            
            # Parse response
            llm_response = self._parse_response(response)
            
            # Update stats
            self._update_stats(llm_response)
            
            logger.info(
                "Received Aliyun DashScope response",
                tokens=llm_response.usage.total_tokens,
            )
            
            return llm_response
            
        except Exception as e:
            logger.error("Aliyun DashScope API error", error=str(e))
            raise
    
    async def chat_stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        system: str | None = None,
        config: LLMConfig | None = None,
    ) -> AsyncIterator[LLMResponse]:
        """Send streaming chat request"""
        
        cfg = self._merge_configs(config)
        
        # Convert messages
        openai_messages = []
        if system:
            openai_messages.append({"role": "system", "content": system})
        for msg in messages:
            openai_messages.append(msg.to_dict())
        
        # Build request
        params = {
            "model": self.model,
            "messages": openai_messages,
            "max_tokens": cfg.max_tokens,
            "temperature": cfg.temperature,
            "top_p": cfg.top_p,
            "stream": True,
        }
        
        if tools:
            params["tools"] = [t.to_dict() for t in tools]
        
        try:
            stream = await self.client.chat.completions.create(**params)
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield LLMResponse(
                        text=chunk.choices[0].delta.content,
                        model=self.model,
                    )
                    
        except Exception as e:
            logger.error("Aliyun streaming error", error=str(e))
            raise
    
    def _parse_response(self, response) -> LLMResponse:
        """Parse API response"""
        
        # Extract text
        text_content = ""
        tool_calls = []
        
        choice = response.choices[0]
        message = choice.message
        
        if message.content:
            text_content = message.content
        
        # Extract tool calls
        if message.tool_calls:
            for tc in message.tool_calls:
                import json
                try:
                    input_data = json.loads(tc.function.arguments) if tc.function.arguments else {}
                except json.JSONDecodeError:
                    input_data = {}
                
                tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    input=input_data,
                ))
        
        # Extract usage
        usage = Usage(
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
        )
        
        # Map stop reason
        stop_reason_map = {
            "stop": "end_turn",
            "tool_calls": "tool_use",
            "length": "max_tokens",
        }
        stop_reason = stop_reason_map.get(choice.finish_reason, "end_turn")
        
        return LLMResponse(
            text=text_content,
            tool_calls=tool_calls,
            model=self.model,
            stop_reason=stop_reason,  # type: ignore
            usage=usage,
        )
    
    async def close(self) -> None:
        """Close client session"""
        if self._client and hasattr(self._client, "close"):
            await self._client.close()
            self._client = None
    
    def __repr__(self) -> str:
        return f"AliyunProvider(model={self.model})"


# Convenience function for creating provider
def create_aliyun_provider(
    api_key: str | None = None,
    model: str = "qwen-plus",
    **kwargs,
) -> AliyunProvider:
    """Create Aliyun provider with common settings"""
    return AliyunProvider(
        api_key=api_key,
        model=model,
        **kwargs,
    )
