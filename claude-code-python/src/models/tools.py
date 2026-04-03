"""Tool related types"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel


T = TypeVar("T", bound="ToolInput")


class ToolInput(BaseModel):
    """Base class for tool inputs"""
    
    pass


class ToolResult(BaseModel):
    """Result from tool execution"""
    
    content: list[dict[str, Any]]
    is_error: bool = False
    error_message: str | None = None
    
    @classmethod
    def success(cls, content: list[dict[str, Any]]) -> "ToolResult":
        """Create a success result"""
        return cls(content=content, is_error=False)
    
    @classmethod
    def error(cls, message: str) -> "ToolResult":
        """Create an error result"""
        return cls(content=[], is_error=True, error_message=message)
    
    def to_text(self) -> str:
        """Convert result to text representation"""
        texts = []
        for item in self.content:
            if isinstance(item, dict):
                if "text" in item:
                    texts.append(item["text"])
                elif "diff" in item:
                    texts.append(item["diff"])
                else:
                    texts.append(str(item))
            else:
                texts.append(str(item))
        return "\n".join(texts)


class ToolDefinition(BaseModel):
    """Tool definition for LLM"""
    
    name: str
    description: str
    input_schema: dict[str, Any]  # JSON Schema
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to API format"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


class ToolCall(BaseModel):
    """Record of a tool call"""
    
    id: str
    name: str
    input: dict[str, Any]
    result: ToolResult | None = None
    status: Literal["pending", "running", "completed", "failed", "cancelled"] = "pending"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    
    @property
    def is_complete(self) -> bool:
        """Check if call is complete"""
        return self.status in ("completed", "failed", "cancelled")
    
    @property
    def duration_ms(self) -> int | None:
        """Get execution duration in milliseconds"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() * 1000)
        return None
