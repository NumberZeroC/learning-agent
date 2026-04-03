"""File write tool for creating new files"""

from __future__ import annotations

import os
from pathlib import Path

import structlog

from .base import Tool, ToolContext, ValidationResult
from ..models.tools import ToolInput, ToolResult

logger = structlog.get_logger(__name__)


class FileWriteInput(ToolInput):
    """Input for FileWrite tool"""
    
    file_path: str
    content: str
    overwrite: bool = False


class FileWriteTool(Tool[FileWriteInput]):
    """
    Tool for creating new files.
    
    Features:
    - Directory creation
    - Overwrite protection
    - Content validation
    """
    
    name = "file_write"
    description = "Create a new file with the given content"
    
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path where the file should be created"
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file"
            },
            "overwrite": {
                "type": "boolean",
                "description": "Whether to overwrite if file exists (default: false)"
            }
        },
        "required": ["file_path", "content"]
    }
    
    # Configuration
    MAX_FILE_SIZE = 1000000  # 1MB max
    BLOCKED_PATHS = [
        "/etc/",
        "/usr/",
        "/bin/",
        "/sbin/",
        "/var/",
        "/root/",
        "/proc/",
        "/sys/",
    ]
    
    def get_prompt(self) -> str:
        """Get prompt describing how to use this tool"""
        return """Use the `file_write` tool to create new files.

Guidelines:
- Use absolute paths when possible
- File must not exist (use overwrite=true to force)
- Directories will be created automatically
- Large files will be rejected for safety

Example:
{
    "file_path": "/path/to/new_file.py",
    "content": "print('Hello, World!')",
    "overwrite": false
}"""
    
    async def validate_input(
        self,
        tool_input: dict,
        context: ToolContext,
    ) -> ValidationResult:
        """Validate file write input"""
        
        file_path = tool_input.get("file_path", "")
        content = tool_input.get("content", "")
        overwrite = tool_input.get("overwrite", False)
        
        # Validate file path
        if not file_path:
            return ValidationResult.fail("File path is required")
        
        # Check for absolute path
        if not os.path.isabs(file_path):
            file_path = os.path.join(context.working_directory, file_path)
        
        file_path = os.path.normpath(file_path)
        
        # Check blocked paths
        for blocked in self.BLOCKED_PATHS:
            if file_path.startswith(blocked):
                return ValidationResult.fail(
                    f"Writing to {blocked} is blocked for security",
                    error_code="BLOCKED_PATH"
                )
        
        # Check content size
        if len(content) > self.MAX_FILE_SIZE:
            return ValidationResult.fail(
                f"Content too large: {len(content)} chars (max: {self.MAX_FILE_SIZE})",
                error_code="CONTENT_TOO_LARGE"
            )
        
        # Check if file exists
        if os.path.exists(file_path) and not overwrite:
            return ValidationResult.fail(
                f"File already exists: {file_path}. Use overwrite=true to force.",
                error_code="FILE_EXISTS"
            )
        
        return ValidationResult.ok()
    
    async def execute(self, tool_input: FileWriteInput, context: ToolContext) -> ToolResult:
        """Execute file write"""
        
        # Resolve path
        file_path = tool_input.file_path
        if not os.path.isabs(file_path):
            file_path = os.path.join(context.working_directory, file_path)
        
        file_path = os.path.normpath(file_path)
        
        logger.info(
            "File write requested",
            file_path=file_path,
            content_size=len(tool_input.content),
            overwrite=tool_input.overwrite,
        )
        
        # Check if file exists and overwrite is not enabled
        if os.path.exists(file_path) and not tool_input.overwrite:
            return ToolResult.error(
                f"File already exists: {file_path}. Use overwrite=true to force."
            )
        
        try:
            # Check if overwriting
            is_new = not os.path.exists(file_path)
            
            # Create directory if needed
            dir_path = os.path.dirname(file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
                logger.debug("Directory created/verified", path=dir_path)
            
            # Write content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(tool_input.content)
            
            # Build result
            content = [
                {"type": "text", "text": f"✅ File {'created' if is_new else 'updated'}: {file_path}"},
                {"type": "text", "text": f"Size: {len(tool_input.content)} characters"},
            ]
            
            return ToolResult.success(content)
            
        except PermissionError:
            logger.error("Permission denied", file_path=file_path)
            return ToolResult.error(f"Permission denied: {file_path}")
        except OSError as e:
            logger.exception("File write error", file_path=file_path)
            return ToolResult.error(f"Write error: {str(e)}")
        except Exception as e:
            logger.exception("File write error", file_path=file_path)
            return ToolResult.error(f"Error: {str(e)}")
    
    async def before_execute(
        self,
        tool_input: FileWriteInput,
        context: ToolContext,
    ) -> None:
        """Log before execution"""
        await super().before_execute(tool_input, context)
        logger.debug(
            "File write starting",
            file_path=tool_input.file_path,
            is_new=not os.path.exists(tool_input.file_path),
        )
    
    async def after_execute(
        self,
        tool_input: FileWriteInput,
        result: ToolResult,
        context: ToolContext,
    ) -> None:
        """Log after execution"""
        await super().after_execute(tool_input, result, context)
        logger.debug(
            "File write completed",
            file_path=tool_input.file_path,
            success=not result.is_error,
        )
