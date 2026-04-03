"""Context management for CCP"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

import structlog

logger = structlog.get_logger(__name__)


class OutputProvider(Protocol):
    """Protocol for output providers"""
    
    async def display(self, content: str, clear_line: bool = False) -> None:
        """Display content"""
        ...
    
    async def clear_last_line(self) -> None:
        """Clear last line"""
        ...


class InputProvider(Protocol):
    """Protocol for input providers"""
    
    async def get(self) -> str:
        """Get user input"""
        ...


@dataclass
class SimpleOutput:
    """Simple console output provider"""
    
    async def display(self, content: str, clear_line: bool = False) -> None:
        """Display content to console"""
        if clear_line:
            print("\r" + " " * 80 + "\r", end="")
        print(content)
    
    async def clear_last_line(self) -> None:
        """Clear last line (ANSI escape)"""
        print("\033[A\033[K", end="")


@dataclass
class SimpleInput:
    """Simple console input provider"""
    
    prompt: str = "> "
    
    async def get(self) -> str:
        """Get input from console"""
        try:
            return input(self.prompt)
        except EOFError:
            return ""


@dataclass
class CommandContext:
    """
    Context for command execution.
    
    Provides access to:
    - Input/output providers
    - Working directory
    - Session state
    - Extra context
    """
    
    output: OutputProvider = field(default_factory=SimpleOutput)
    input: InputProvider = field(default_factory=SimpleInput)
    working_directory: str = "."
    session_id: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get extra context value"""
        return self.extras.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set extra context value"""
        self.extras[key] = value


@dataclass
class ToolContext:
    """
    Context for tool execution.
    
    Similar to CommandContext but specialized for tools.
    """
    
    session_id: str
    working_directory: str
    request_id: str | None = None
    user_id: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get extra context value"""
        return self.extras.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set extra context value"""
        self.extras[key] = value


class ContextManager:
    """
    Manages execution contexts.
    
    Features:
    - Context stack
    - Context inheritance
    - Context cleanup
    """
    
    def __init__(self):
        self._stack: list[CommandContext] = []
        self._default_context = CommandContext()
    
    @property
    def current(self) -> CommandContext:
        """Get current context"""
        if self._stack:
            return self._stack[-1]
        return self._default_context
    
    def push(self, context: CommandContext) -> None:
        """Push a context onto the stack"""
        self._stack.append(context)
        logger.debug("Context pushed", stack_size=len(self._stack))
    
    def pop(self) -> CommandContext | None:
        """Pop the current context"""
        if self._stack:
            context = self._stack.pop()
            logger.debug("Context popped", stack_size=len(self._stack))
            return context
        return None
    
    def create_child(
        self,
        **overrides: Any,
    ) -> CommandContext:
        """Create a child context with overrides"""
        
        parent = self.current
        
        # Create new context with parent values
        child = CommandContext(
            output=parent.output,
            input=parent.input,
            working_directory=overrides.get("working_directory", parent.working_directory),
            session_id=overrides.get("session_id", parent.session_id),
            extras={**parent.extras, **overrides.get("extras", {})},
        )
        
        return child
    
    def clear(self) -> None:
        """Clear the context stack"""
        self._stack.clear()
        logger.info("Context stack cleared")
    
    def __len__(self) -> int:
        return len(self._stack)
