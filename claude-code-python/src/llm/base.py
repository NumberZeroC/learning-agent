"""Base LLM provider interface"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator

from ..models.messages import Message
from ..models.llm import LLMConfig, LLMResponse
from ..models.tools import ToolDefinition


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig()
        self._request_count = 0
        self._total_tokens = 0
    
    @property
    def model(self) -> str:
        """Get current model name"""
        return self.config.model
    
    @property
    def request_count(self) -> int:
        """Get total number of requests made"""
        return self._request_count
    
    @property
    def total_tokens(self) -> int:
        """Get total tokens used"""
        return self._total_tokens
    
    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        system: str | None = None,
        config: LLMConfig | None = None,
    ) -> LLMResponse:
        """
        Send a chat request to the LLM.
        
        Args:
            messages: List of conversation messages
            tools: Optional list of available tools
            system: Optional system prompt
            config: Optional config override
        
        Returns:
            LLMResponse with text and/or tool calls
        """
        pass
    
    @abstractmethod
    async def chat_stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        system: str | None = None,
        config: LLMConfig | None = None,
    ) -> AsyncIterator[LLMResponse]:
        """
        Send a streaming chat request to the LLM.
        
        Args:
            messages: List of conversation messages
            tools: Optional list of available tools
            system: Optional system prompt
            config: Optional config override
        
        Yields:
            LLMResponse chunks as they arrive
        """
        pass
    
    def _update_stats(self, response: LLMResponse) -> None:
        """Update internal statistics after a request"""
        self._request_count += 1
        self._total_tokens += response.usage.total_tokens
    
    def _merge_configs(self, override: LLMConfig | None) -> LLMConfig:
        """Merge override config with default config"""
        if override is None:
            return self.config
        # Create a new config with override values
        return LLMConfig(
            model=override.model or self.config.model,
            max_tokens=override.max_tokens or self.config.max_tokens,
            temperature=override.temperature or self.config.temperature,
            top_p=override.top_p or self.config.top_p,
            top_k=override.top_k if override.top_k > 0 else self.config.top_k,
            stop_sequences=override.stop_sequences or self.config.stop_sequences,
            thinking_enabled=override.thinking_enabled or self.config.thinking_enabled,
            thinking_budget=override.thinking_budget or self.config.thinking_budget,
            timeout_seconds=override.timeout_seconds or self.config.timeout_seconds,
        )
    
    async def close(self) -> None:
        """Close any open connections. Override in subclasses if needed."""
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model})"
