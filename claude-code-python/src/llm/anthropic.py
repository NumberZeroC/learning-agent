"""Anthropic Claude provider"""

from __future__ import annotations

import os
from typing import AsyncIterator

import structlog

from ..models.llm import LLMConfig, LLMResponse, ToolCall, Usage
from ..models.messages import Message, format_messages_for_api
from ..models.tools import ToolDefinition
from .base import LLMProvider

logger = structlog.get_logger(__name__)


class AnthropicProvider(LLMProvider):
    """
    Anthropic Claude API provider.
    
    Also supports Anthropic-compatible endpoints:
    - Aliyun Coding Plan: https://coding.dashscope.aliyuncs.com/apps/anthropic
    - Other compatible services
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        config: LLMConfig | None = None,
        base_url: str | None = None,
    ):
        super().__init__(config)
        
        # Get API key from environment
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY env var."
            )
        
        # Get base URL from parameter or environment
        self.base_url = base_url or os.environ.get("ANTHROPIC_BASE_URL")
        
        # Get model from environment if not in config
        if config and not config.model:
            env_model = os.environ.get("ANTHROPIC_MODEL")
            if env_model:
                self.config.model = env_model
        
        # Lazy client
        self._client = None
    
    @property
    def client(self):
        """Lazy load Anthropic client"""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
                
                self._client = AsyncAnthropic(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
            except ImportError:
                raise ImportError(
                    "anthropic package required. Install with: pip install anthropic"
                )
        return self._client
    
    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        system: str | None = None,
        config: LLMConfig | None = None,
    ) -> LLMResponse:
        """Send a chat request to Anthropic"""
        
        config = self._merge_configs(config)
        
        # Prepare API parameters
        params = config.to_api_params()
        
        # Format messages
        formatted_messages = format_messages_for_api(messages)
        
        # Add tools if provided
        if tools:
            params["tools"] = [t.to_dict() for t in tools]
        
        # Add system prompt if provided
        if system:
            params["system"] = system
        
        logger.debug(
            "Sending Anthropic request",
            model=config.model,
            message_count=len(messages),
            tool_count=len(tools) if tools else 0,
        )
        
        try:
            # Make API call
            response = await self.client.messages.create(
                messages=formatted_messages,
                **params,
            )
            
            # Parse response
            llm_response = self._parse_response(response)
            
            # Update stats
            self._update_stats(llm_response)
            
            logger.debug(
                "Received Anthropic response",
                tokens=llm_response.usage.total_tokens,
                stop_reason=llm_response.stop_reason,
                tool_calls=len(llm_response.tool_calls),
            )
            
            return llm_response
            
        except Exception as e:
            logger.error("Anthropic API error", error=str(e))
            raise
    
    async def chat_stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        system: str | None = None,
        config: LLMConfig | None = None,
    ) -> AsyncIterator[LLMResponse]:
        """Send a streaming chat request to Anthropic"""
        
        config = self._merge_configs(config)
        
        # Prepare API parameters
        params = config.to_api_params()
        
        # Format messages
        formatted_messages = format_messages_for_api(messages)
        
        # Add tools if provided
        if tools:
            params["tools"] = [t.to_dict() for t in tools]
        
        # Add system prompt if provided
        if system:
            params["system"] = system
        
        logger.debug(
            "Sending Anthropic streaming request",
            model=config.model,
        )
        
        try:
            # Make streaming API call
            async with self.client.messages.stream(
                messages=formatted_messages,
                **params,
            ) as stream:
                # Accumulate response
                text_content = ""
                tool_calls = []
                current_tool_id = None
                current_tool_name = None
                current_tool_input = ""
                
                async for event in stream:
                    if event.type == "content_block_start":
                        if event.content_block.type == "tool_use":
                            current_tool_id = event.content_block.id
                            current_tool_name = event.content_block.name
                            current_tool_input = ""
                    
                    elif event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
                            text_content += event.delta.text
                            yield LLMResponse(
                                text=event.delta.text,
                                model=config.model,
                            )
                        elif event.delta.type == "input_json_delta":
                            current_tool_input += event.delta.partial_json
                    
                    elif event.type == "content_block_stop":
                        if current_tool_id and current_tool_name:
                            import json
                            try:
                                tool_input = json.loads(current_tool_input) if current_tool_input else {}
                            except json.JSONDecodeError:
                                tool_input = {}
                            
                            tool_calls.append(ToolCall(
                                id=current_tool_id,
                                name=current_tool_name,
                                input=tool_input,
                            ))
                            current_tool_id = None
                            current_tool_name = None
                            current_tool_input = ""
                    
                    elif event.type == "message_delta":
                        if event.usage.output_tokens:
                            # Final usage update
                            pass
                    
                    elif event.type == "message_stop":
                        # Get final message
                        final_message = await stream.get_final_message()
                        
                        # Yield final response with all content
                        usage = Usage(
                            input_tokens=final_message.usage.input_tokens,
                            output_tokens=final_message.usage.output_tokens,
                        )
                        
                        yield LLMResponse(
                            text=text_content,
                            tool_calls=tool_calls,
                            model=config.model,
                            stop_reason=final_message.stop_reason,
                            usage=usage,
                        )
        
        except Exception as e:
            logger.error("Anthropic streaming error", error=str(e))
            raise
    
    def _parse_response(self, response) -> LLMResponse:
        """Parse Anthropic API response"""
        
        # Extract text content
        text_content = ""
        tool_calls = []
        
        for block in response.content:
            if block.type == "text":
                text_content += block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    input=block.input,
                ))
        
        # Extract usage
        usage = Usage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
        
        return LLMResponse(
            text=text_content,
            tool_calls=tool_calls,
            model=response.model,
            stop_reason=response.stop_reason,
            usage=usage,
            raw={"id": response.id, "type": response.type},
        )
    
    async def close(self) -> None:
        """Close the client session"""
        if self._client and hasattr(self._client, "close"):
            await self._client.close()
            self._client = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
