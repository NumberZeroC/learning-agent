"""Message types for CCP"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class ToolCall(BaseModel):
    """Tool call definition"""
    
    id: str
    name: str
    input: dict[str, Any]
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class ContentBlock(BaseModel):
    """Content block for messages"""
    
    type: Literal["text", "image", "diff", "json"]
    text: str | None = None
    data: bytes | None = None
    format: str | None = None  # For images: "png", "jpeg", etc.
    
    model_config = {"arbitrary_types_allowed": True}
    
    @classmethod
    def text_block(cls, text: str) -> "ContentBlock":
        """Create a text content block"""
        return cls(type="text", text=text)
    
    @classmethod
    def image_block(cls, data: bytes, format: str = "png") -> "ContentBlock":
        """Create an image content block"""
        return cls(type="image", data=data, format=format)
    
    @classmethod
    def diff_block(cls, diff: str) -> "ContentBlock":
        """Create a diff content block"""
        return cls(type="diff", text=diff)


class Message(BaseModel):
    """Base message class"""
    
    role: Literal["user", "assistant", "system"]
    content: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)
    tool_calls: list[ToolCall] | None = None
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API calls"""
        return {
            "role": self.role,
            "content": self.content,
        }


class ToolUseMessage(Message):
    """Tool use message from assistant"""
    
    role: Literal["assistant"] = "assistant"
    tool_use_id: str
    tool_name: str
    tool_input: dict[str, Any]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to Anthropic API format"""
        return {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": self.tool_use_id,
                    "name": self.tool_name,
                    "input": self.tool_input,
                }
            ],
        }


class ToolResultMessage(Message):
    """Tool result message from user"""
    
    role: Literal["user"] = "user"
    tool_use_id: str
    content: list[ContentBlock]
    is_error: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to Anthropic API format"""
        content_list = []
        for block in self.content:
            if block.type == "text":
                content_list.append({
                    "type": "text",
                    "text": block.text,
                })
            elif block.type == "image":
                # Base64 encode for API
                import base64
                content_list.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": f"image/{block.format}",
                        "data": base64.b64encode(block.data).decode(),
                    },
                })
        
        return {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": self.tool_use_id,
                    "content": content_list,
                    "is_error": self.is_error,
                }
            ],
        }


class SystemMessage(Message):
    """System message for instructions"""
    
    role: Literal["system"] = "system"
    priority: int = 0  # Higher priority messages come first


def format_messages_for_api(messages: list[Message]) -> list[dict[str, Any]]:
    """Format messages for LLM API calls"""
    result = []
    for msg in messages:
        result.append(msg.to_dict())
    return result
