"""LLM related types"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel


class Usage(BaseModel):
    """Token usage tracking"""
    
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    
    @property
    def total_tokens(self) -> int:
        """Total tokens used"""
        return self.input_tokens + self.output_tokens
    
    def estimate_cost(self, model: str) -> float:
        """Estimate cost based on model pricing (USD)"""
        # Pricing as of 2026
        pricing = {
            "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},  # per 1M tokens
            "claude-opus-4-20250514": {"input": 15.0, "output": 75.0},
            "claude-haiku-4-20250514": {"input": 0.8, "output": 4.0},
        }
        
        rates = pricing.get(model, {"input": 3.0, "output": 15.0})
        input_cost = (self.input_tokens / 1_000_000) * rates["input"]
        output_cost = (self.output_tokens / 1_000_000) * rates["output"]
        return input_cost + output_cost


class LLMConfig(BaseModel):
    """LLM configuration"""
    
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = -1
    stop_sequences: list[str] = field(default_factory=list)
    
    # Extended thinking
    thinking_enabled: bool = False
    thinking_budget: int = 1024
    
    # Caching
    cache_prompt: bool = True
    cache_system: bool = True
    
    # Timeouts
    timeout_seconds: float = 60.0
    
    def to_api_params(self) -> dict[str, Any]:
        """Convert to API parameters"""
        params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }
        
        if self.top_k > 0:
            params["top_k"] = self.top_k
        if self.stop_sequences:
            params["stop_sequences"] = self.stop_sequences
        
        return params


class ToolCall(BaseModel):
    """Tool call from LLM"""
    
    id: str
    name: str
    input: dict[str, Any]
    
    def __str__(self) -> str:
        return f"ToolCall({self.name}, id={self.id})"


class LLMResponse(BaseModel):
    """Response from LLM"""
    
    # Content
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    
    # Metadata
    model: str
    stop_reason: Literal["end_turn", "tool_use", "max_tokens", "stop_sequence"] | None = None
    
    # Usage
    usage: Usage = field(default_factory=Usage)
    
    # Raw response for debugging
    raw: dict[str, Any] = field(default_factory=dict)
    
    @property
    def has_tool_calls(self) -> bool:
        """Check if response contains tool calls"""
        return len(self.tool_calls) > 0
    
    @property
    def is_complete(self) -> bool:
        """Check if response is complete (no tool calls pending)"""
        return self.stop_reason == "end_turn" and not self.has_tool_calls
    
    def __str__(self) -> str:
        if self.text:
            return self.text[:100] + "..." if len(self.text) > 100 else self.text
        if self.tool_calls:
            return f"Tool calls: {[tc.name for tc in self.tool_calls]}"
        return "Empty response"
