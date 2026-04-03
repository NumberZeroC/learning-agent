"""File read tool for reading file contents"""

from __future__ import annotations

import os
from pathlib import Path

import structlog

from .base import Tool, ToolContext, ValidationResult
from ..models.tools import ToolInput, ToolResult

logger = structlog.get_logger(__name__)


class FileReadInput(ToolInput):
    """Input for FileRead tool"""
    
    file_path: str
    max_lines: int | None = None
    offset: int | None = None


class FileReadTool(Tool[FileReadInput]):
    """
    Tool for reading file contents safely.
    
    Features:
    - Line limits for large files
    - Offset support for pagination
    - Binary file detection
    - Path validation
    """
    
    name = "file_read"
    description = "Read contents of a file"
    
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to read"
            },
            "max_lines": {
                "type": "integer",
                "description": "Maximum number of lines to read (default: 1000)"
            },
            "offset": {
                "type": "integer",
                "description": "Line number to start reading from (0-indexed)"
            }
        },
        "required": ["file_path"]
    }
    
    # Configuration
    DEFAULT_MAX_LINES = 1000
    MAX_MAX_LINES = 10000
    LARGE_FILE_THRESHOLD = 10000  # lines
    
    # Blocked paths
    BLOCKED_PATHS = [
        "/etc/shadow",
        "/etc/passwd",
        "/etc/sudoers",
        "/proc/",
        "/sys/",
    ]
    
    def get_prompt(self) -> str:
        """Get prompt describing how to use this tool"""
        return """Use the `file_read` tool to read file contents.

Guidelines:
- Use absolute paths when possible
- For large files, use max_lines to limit output
- Use offset for pagination through large files
- Binary files will be detected and handled appropriately

Example:
{
    "file_path": "/path/to/file.py",
    "max_lines": 100,
    "offset": 0
}"""
    
    async def validate_input(
        self,
        tool_input: dict,
        context: ToolContext,
    ) -> ValidationResult:
        """Validate file read input"""
        
        file_path = tool_input.get("file_path", "")
        
        if not file_path:
            return ValidationResult.fail("File path is required")
        
        # Resolve to absolute path
        if not os.path.isabs(file_path):
            file_path = os.path.join(context.working_directory, file_path)
        
        # Check blocked paths
        for blocked in self.BLOCKED_PATHS:
            if file_path.startswith(blocked):
                return ValidationResult.fail(
                    f"Access to {blocked} is blocked for security",
                    error_code="BLOCKED_PATH"
                )
        
        # Check if file exists
        if not os.path.exists(file_path):
            return ValidationResult.fail(
                f"File does not exist: {file_path}",
                error_code="FILE_NOT_FOUND"
            )
        
        # Check if it's a file (not directory)
        if not os.path.isfile(file_path):
            return ValidationResult.fail(
                f"Path is not a file: {file_path}",
                error_code="NOT_A_FILE"
            )
        
        # Validate max_lines
        max_lines = tool_input.get("max_lines", self.DEFAULT_MAX_LINES)
        if max_lines <= 0 or max_lines > self.MAX_MAX_LINES:
            return ValidationResult.fail(
                f"max_lines must be between 1 and {self.MAX_MAX_LINES}",
                error_code="INVALID_MAX_LINES"
            )
        
        # Validate offset
        offset = tool_input.get("offset", 0)
        if offset < 0:
            return ValidationResult.fail(
                "offset must be non-negative",
                error_code="INVALID_OFFSET"
            )
        
        return ValidationResult.ok()
    
    async def execute(self, tool_input: FileReadInput, context: ToolContext) -> ToolResult:
        """Execute file read"""
        
        # Resolve path
        file_path = tool_input.file_path
        if not os.path.isabs(file_path):
            file_path = os.path.join(context.working_directory, file_path)
        
        file_path = os.path.normpath(file_path)
        
        logger.info(
            "File read requested",
            file_path=file_path,
            max_lines=tool_input.max_lines,
            offset=tool_input.offset,
        )
        
        max_lines = tool_input.max_lines or self.DEFAULT_MAX_LINES
        offset = tool_input.offset or 0
        
        try:
            # Check file size first
            file_size = os.path.getsize(file_path)
            
            # Try to detect if binary
            is_binary = await self._is_binary(file_path)
            
            if is_binary:
                # Handle binary files
                return await self._read_binary(file_path)
            
            # Read text file
            return await self._read_text(file_path, offset, max_lines)
            
        except PermissionError:
            logger.error("Permission denied", file_path=file_path)
            return ToolResult.error(f"Permission denied: {file_path}")
        except Exception as e:
            logger.exception("File read error", file_path=file_path)
            return ToolResult.error(f"Error reading file: {str(e)}")
    
    async def _read_text(
        self,
        file_path: str,
        offset: int,
        max_lines: int,
    ) -> ToolResult:
        """Read text file with limits"""
        
        lines = []
        total_lines = 0
        truncated = False
        
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                total_lines = i + 1
                if i < offset:
                    continue
                if len(lines) >= max_lines:
                    truncated = True
                    break
                lines.append(line)
        
        content = lines.copy()
        
        # Add metadata
        metadata = [
            f"\n---",
            f"File: {file_path}",
            f"Lines read: {len(lines)}",
            f"Total lines: {total_lines}",
        ]
        
        if truncated:
            metadata.append(f"⚠️ Output truncated (showing {len(lines)} of {total_lines} lines)")
            metadata.append(f"Use offset={offset + max_lines} to read more")
        
        content.append("\n".join(metadata))
        
        return ToolResult.success([
            {"type": "text", "text": "".join(content)}
        ])
    
    async def _read_binary(self, file_path: str) -> ToolResult:
        """Handle binary file"""
        
        # Read first 1KB for inspection
        with open(file_path, "rb") as f:
            header = f.read(1024)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        
        content = [
            {"type": "text", "text": f"[Binary file detected]"},
            {"type": "text", "text": f"File: {file_path}"},
            {"type": "text", "text": f"Size: {self._format_size(file_size)}"},
            {"type": "text", "text": f"Header (hex): {header[:64].hex()}"},
        ]
        
        return ToolResult.success(content)
    
    async def _is_binary(self, file_path: str) -> bool:
        """Detect if file is binary"""
        
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(8192)
                if b"\x00" in chunk:
                    return True
                # Try to decode as UTF-8
                try:
                    chunk.decode("utf-8")
                    return False
                except UnicodeDecodeError:
                    return True
        except Exception:
            return True
    
    def _format_size(self, size: int) -> str:
        """Format file size"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
