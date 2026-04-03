"""Mkdir tool for creating directories"""

from __future__ import annotations

import os
from pathlib import Path

import structlog

from .base import Tool, ToolContext, ValidationResult
from ..models.tools import ToolInput, ToolResult

logger = structlog.get_logger(__name__)


class MkdirInput(ToolInput):
    """Input for Mkdir tool"""
    
    path: str
    parents: bool = True
    exist_ok: bool = True


class MkdirTool(Tool[MkdirInput]):
    """
    Tool for creating directories.
    
    Features:
    - Create single directory
    - Create parent directories
    - Handle existing directories
    """
    
    name = "mkdir"
    description = "Create a directory or directory tree"
    
    input_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Directory path to create"
            },
            "parents": {
                "type": "boolean",
                "description": "Create parent directories if needed (default: true)"
            },
            "exist_ok": {
                "type": "boolean",
                "description": "Don't error if directory exists (default: true)"
            }
        },
        "required": ["path"]
    }
    
    def get_prompt(self) -> str:
        """Get prompt describing how to use this tool"""
        return """Use the `mkdir` tool to create directories.

Examples:

Create a single directory:
{
    "path": "src/utils"
}

Create directory tree:
{
    "path": "project/src/utils",
    "parents": true
}"""
    
    async def validate_input(
        self,
        tool_input: dict,
        context: ToolContext,
    ) -> ValidationResult:
        """Validate mkdir input"""
        
        path = tool_input.get("path", "")
        
        if not path:
            return ValidationResult.fail("Path is required")
        
        # Check for dangerous paths
        dangerous_paths = ["/", "/etc", "/usr", "/bin", "/root", "/home"]
        if path in dangerous_paths or path.startswith("/etc/") or path.startswith("/root/"):
            return ValidationResult.fail(
                f"Cannot create directory in protected path: {path}",
                error_code="DANGEROUS_PATH"
            )
        
        return ValidationResult.ok()
    
    async def execute(self, tool_input: MkdirInput, context: ToolContext) -> ToolResult:
        """Execute mkdir"""
        
        # Resolve path
        path = tool_input.path
        if not os.path.isabs(path):
            path = os.path.join(context.working_directory, path)
        
        path = os.path.normpath(path)
        
        logger.info(
            "Mkdir requested",
            path=path,
            parents=tool_input.parents,
            exist_ok=tool_input.exist_ok,
        )
        
        try:
            # Create directory
            Path(path).mkdir(
                parents=tool_input.parents,
                exist_ok=tool_input.exist_ok,
            )
            
            return ToolResult.success([
                {"type": "text", "text": f"✅ Created directory: {path}"}
            ])
            
        except FileExistsError:
            return ToolResult.error(f"Directory already exists: {path}")
        except PermissionError:
            return ToolResult.error(f"Permission denied: {path}")
        except OSError as e:
            return ToolResult.error(f"Error creating directory: {e}")
