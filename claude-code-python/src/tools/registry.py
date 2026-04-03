"""Tool registry for managing available tools"""

from __future__ import annotations

from typing import TypeVar

import structlog

from ..models.tools import ToolDefinition
from .base import Tool, ToolContext, ToolInput, ToolResult

logger = structlog.get_logger(__name__)

T = TypeVar("T", bound=Tool)


class ToolRegistry:
    """
    Registry for managing available tools.
    
    The registry allows tools to be dynamically registered and retrieved,
    making it easy to extend the system with new capabilities.
    """
    
    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._aliases: dict[str, str] = {}
    
    def register(self, tool: Tool, aliases: list[str] | None = None) -> None:
        """
        Register a tool in the registry.
        
        Args:
            tool: The tool instance to register
            aliases: Optional list of alternative names
        """
        name = tool.name
        
        if name in self._tools:
            logger.warning("Replacing existing tool", name=name)
        
        self._tools[name] = tool
        logger.info("Tool registered", name=name, type=type(tool).__name__)
        
        # Register aliases
        if aliases:
            for alias in aliases:
                self._aliases[alias] = name
                logger.debug("Tool alias registered", alias=alias, target=name)
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a tool by name.
        
        Args:
            name: Tool name or alias
        
        Returns:
            True if tool was found and removed
        """
        # Resolve alias if needed
        actual_name = self._resolve_name(name)
        
        if actual_name in self._tools:
            del self._tools[actual_name]
            logger.info("Tool unregistered", name=actual_name)
            return True
        
        return False
    
    def get(self, name: str) -> Tool | None:
        """
        Get a tool by name.
        
        Args:
            name: Tool name or alias
        
        Returns:
            Tool instance or None if not found
        """
        actual_name = self._resolve_name(name)
        return self._tools.get(actual_name)
    
    def get_required(self, name: str) -> Tool:
        """
        Get a tool by name, raising an error if not found.
        
        Args:
            name: Tool name or alias
        
        Returns:
            Tool instance
        
        Raises:
            KeyError: If tool not found
        """
        tool = self.get(name)
        if tool is None:
            raise KeyError(f"Tool not found: {name}")
        return tool
    
    def has(self, name: str) -> bool:
        """Check if a tool is registered"""
        return self._resolve_name(name) in self._tools
    
    def list_tools(self) -> list[str]:
        """Get list of all registered tool names"""
        return list(self._tools.keys())
    
    def get_definitions(self) -> list[ToolDefinition]:
        """Get definitions for all enabled tools"""
        return [
            tool.get_definition()
            for tool in self._tools.values()
            if tool.is_enabled
        ]
    
    def get_enabled_tools(self) -> list[Tool]:
        """Get all enabled tools"""
        return [tool for tool in self._tools.values() if tool.is_enabled]
    
    def enable(self, name: str) -> bool:
        """Enable a tool by name"""
        tool = self.get(name)
        if tool:
            tool.enable()
            return True
        return False
    
    def disable(self, name: str) -> bool:
        """Disable a tool by name"""
        tool = self.get(name)
        if tool:
            tool.disable()
            return True
        return False
    
    def _resolve_name(self, name: str) -> str:
        """Resolve alias to actual tool name"""
        return self._aliases.get(name, name)
    
    async def execute_tool(
        self,
        name: str,
        tool_input: dict,
        context: ToolContext,
    ) -> ToolResult:
        """
        Execute a tool by name.
        
        Args:
            name: Tool name or alias
            tool_input: Raw input dictionary
            context: Execution context
        
        Returns:
            ToolResult from execution
        """
        tool = self.get_required(name)
        
        # Validate input
        validation = await tool.validate_input(tool_input, context)
        if not validation.valid:
            return ToolResult.error(
                f"Invalid input: {validation.message}",
            )
        
        # Convert dict to tool's input model
        from ..tools.bash import BashInput
        from ..tools.file_read import FileReadInput
        from ..tools.file_edit import FileEditInput
        from ..tools.file_write import FileWriteInput
        from ..tools.grep import GrepInput
        from ..tools.glob import GlobInput
        from ..tools.mkdir import MkdirInput
        from ..tools.project_template import ProjectTemplateInput
        from ..tools.file_write_batch import FileWriteBatchInput
        
        # Map tool names to input classes
        input_classes = {
            'bash': BashInput,
            'file_read': FileReadInput,
            'file_edit': FileEditInput,
            'file_write': FileWriteInput,
            'file_write_batch': FileWriteBatchInput,
            'grep': GrepInput,
            'glob': GlobInput,
            'mkdir': MkdirInput,
            'project_template': ProjectTemplateInput,
        }
        
        input_class = input_classes.get(name)
        if input_class:
            try:
                typed_input = input_class(**tool_input)
            except Exception as e:
                return ToolResult.error(f"Invalid input format: {e}")
        else:
            typed_input = tool_input  # type: ignore
        
        # Execute with hooks
        return await tool.execute_with_hooks(typed_input, context)
    
    def clear(self) -> None:
        """Clear all registered tools"""
        self._tools.clear()
        self._aliases.clear()
        logger.info("Tool registry cleared")
    
    def __len__(self) -> int:
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        return self.has(name)
    
    def __repr__(self) -> str:
        tools = ", ".join(sorted(self._tools.keys()))
        return f"ToolRegistry(tools=[{tools}])"


# Global default registry
_default_registry: ToolRegistry | None = None


def get_default_registry() -> ToolRegistry:
    """Get or create the default tool registry"""
    global _default_registry
    if _default_registry is None:
        _default_registry = ToolRegistry()
    return _default_registry


def reset_default_registry() -> None:
    """Reset the default registry"""
    global _default_registry
    _default_registry = ToolRegistry()
