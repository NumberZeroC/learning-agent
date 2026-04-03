"""Base command classes"""

from __future__ import annotations

from abc import ABC, abstractmethod
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
class CommandContext:
    """Context for command execution"""
    
    output: OutputProvider | None = None
    input: InputProvider | None = None
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
class CommandResult:
    """Result of command execution"""
    
    success: bool
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    
    def __bool__(self) -> bool:
        return self.success


class Command(ABC):
    """Abstract base class for commands"""
    
    name: str
    aliases: list[str] = []
    description: str = ""
    
    @abstractmethod
    async def execute(self, args: list[str], context: CommandContext) -> CommandResult:
        """Execute the command"""
        pass
    
    def __repr__(self) -> str:
        return f"Command({self.name})"
