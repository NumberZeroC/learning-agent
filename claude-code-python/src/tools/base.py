"""Base tool class and related types"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

import structlog

from ..models.llm import LLMConfig
from ..models.tools import ToolDefinition, ToolInput, ToolResult

logger = structlog.get_logger(__name__)

T = TypeVar("T", bound=ToolInput)


@dataclass
class ToolContext:
    """Context available to tools during execution"""
    
    # Session info
    session_id: str
    working_directory: str
    
    # Configuration
    llm_config: LLMConfig | None = None
    
    # Runtime state
    request_id: str | None = None
    user_id: str | None = None
    
    # Extra context (extensible)
    extras: dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get extra context value"""
        return self.extras.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set extra context value"""
        self.extras[key] = value


@dataclass
class ValidationResult:
    """Result of tool input validation"""
    
    valid: bool
    message: str | None = None
    error_code: str | None = None
    
    @classmethod
    def ok(cls) -> "ValidationResult":
        """Create a successful validation result"""
        return cls(valid=True)
    
    @classmethod
    def fail(cls, message: str, error_code: str | None = None) -> "ValidationResult":
        """Create a failed validation result"""
        return cls(valid=False, message=message, error_code=error_code)


class Tool(ABC, Generic[T]):
    """
    Abstract base class for all tools.
    
    Tools are the primary way Claude Code interacts with the external world.
    Each tool defines:
    - A name and description (for the LLM)
    - An input schema (for validation)
    - Execution logic
    - A prompt describing how to use the tool
    """
    
    # Class-level attributes (must be overridden)
    name: str
    description: str
    input_schema: dict[str, Any]
    
    def __init__(self):
        self._enabled = True
        self._call_count = 0
        self._error_count = 0
    
    @property
    def is_enabled(self) -> bool:
        """Check if tool is enabled"""
        return self._enabled
    
    @property
    def call_count(self) -> int:
        """Get number of times tool has been called"""
        return self._call_count
    
    @property
    def error_count(self) -> int:
        """Get number of errors"""
        return self._error_count
    
    @property
    def success_rate(self) -> float:
        """Get success rate percentage"""
        if self._call_count == 0:
            return 100.0
        return (1 - self._error_count / self._call_count) * 100
    
    def enable(self) -> None:
        """Enable the tool"""
        self._enabled = True
        logger.info("Tool enabled", name=self.name)
    
    def disable(self) -> None:
        """Disable the tool"""
        self._enabled = False
        logger.info("Tool disabled", name=self.name)
    
    def get_definition(self) -> ToolDefinition:
        """Get tool definition for LLM"""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
        )
    
    @abstractmethod
    async def execute(self, tool_input: T, context: ToolContext) -> ToolResult:
        """
        Execute the tool with the given input.
        
        Args:
            tool_input: Validated tool input
            context: Execution context
        
        Returns:
            ToolResult with execution output
        """
        pass
    
    def get_prompt(self) -> str:
        """
        Get prompt describing how to use this tool.
        
        This is included in the system prompt to help the LLM understand
        when and how to use the tool.
        """
        return f"Use the `{self.name}` tool to {self.description.lower()}."
    
    async def validate_input(
        self,
        tool_input: dict[str, Any],
        context: ToolContext,
    ) -> ValidationResult:
        """
        Validate tool input before execution.
        
        Override this method to add custom validation logic.
        
        Args:
            tool_input: Raw input dictionary
            context: Execution context
        
        Returns:
            ValidationResult indicating validity
        """
        # Default: accept all input (schema validation happens elsewhere)
        return ValidationResult.ok()
    
    async def before_execute(
        self,
        tool_input: T,
        context: ToolContext,
    ) -> None:
        """
        Hook called before tool execution.
        
        Override for preprocessing, logging, etc.
        """
        self._call_count += 1
        logger.debug("Tool executing", name=self.name, input=tool_input)
    
    async def after_execute(
        self,
        tool_input: T,
        result: ToolResult,
        context: ToolContext,
    ) -> None:
        """
        Hook called after tool execution.
        
        Override for postprocessing, cleanup, etc.
        """
        if result.is_error:
            self._error_count += 1
            logger.warning(
                "Tool execution failed",
                name=self.name,
                error=result.error_message,
            )
        else:
            logger.debug("Tool executed successfully", name=self.name)
    
    async def execute_with_hooks(
        self,
        tool_input: T,
        context: ToolContext,
    ) -> ToolResult:
        """
        Execute tool with before/after hooks.
        
        This is the main entry point for tool execution.
        """
        if not self._enabled:
            return ToolResult.error(f"Tool {self.name} is disabled")
        
        await self.before_execute(tool_input, context)
        
        try:
            result = await self.execute(tool_input, context)
        except Exception as e:
            logger.exception("Tool execution error", name=self.name, error=str(e))
            result = ToolResult.error(str(e))
        
        await self.after_execute(tool_input, result, context)
        return result
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, enabled={self._enabled})"
