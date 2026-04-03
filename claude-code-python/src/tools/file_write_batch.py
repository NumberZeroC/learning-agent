"""Batch file write tool for creating multiple files at once"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import structlog

from .base import Tool, ToolContext, ValidationResult
from ..models.tools import ToolInput, ToolResult

logger = structlog.get_logger(__name__)


class FileWriteBatchInput(ToolInput):
    """Input for batch file write"""
    
    files: list[dict[str, Any]]
    overwrite: bool = False


class FileWriteBatchTool(Tool[FileWriteBatchInput]):
    """
    Tool for creating multiple files in one operation.
    
    Features:
    - Create multiple files at once
    - Create parent directories automatically
    - Progress reporting
    - Error handling per file
    """
    
    name = "file_write_batch"
    description = "Create multiple files in one operation"
    
    input_schema = {
        "type": "object",
        "properties": {
            "files": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path"
                        },
                        "content": {
                            "type": "string",
                            "description": "File content"
                        }
                    },
                    "required": ["path", "content"]
                },
                "description": "List of files to create"
            },
            "overwrite": {
                "type": "boolean",
                "description": "Overwrite existing files (default: false)"
            }
        },
        "required": ["files"]
    }
    
    def get_prompt(self) -> str:
        """Get prompt describing how to use this tool"""
        return """Use the `file_write_batch` tool to create multiple files at once.

Example:

Create a project structure:
{
    "files": [
        {
            "path": "src/__init__.py",
            "content": "# Package init"
        },
        {
            "path": "src/main.py",
            "content": "def main():\\n    print('Hello')"
        },
        {
            "path": "README.md",
            "content": "# Project Title\\n\\nDescription..."
        }
    ]
}"""
    
    async def validate_input(
        self,
        tool_input: dict,
        context: ToolContext,
    ) -> ValidationResult:
        """Validate batch input"""
        
        files = tool_input.get("files", [])
        
        if not files:
            return ValidationResult.fail("Files list is required")
        
        if len(files) > 50:
            return ValidationResult.fail(
                f"Too many files: {len(files)} (max: 50)",
                error_code="TOO_MANY_FILES"
            )
        
        # Validate each file
        for i, file in enumerate(files):
            if "path" not in file:
                return ValidationResult.fail(f"File {i}: path is required")
            if "content" not in file:
                return ValidationResult.fail(f"File {i}: content is required")
        
        return ValidationResult.ok()
    
    async def execute(self, tool_input: FileWriteBatchInput, context: ToolContext) -> ToolResult:
        """Execute batch file write"""
        
        results = []
        success_count = 0
        error_count = 0
        
        for file_info in tool_input.files:
            path = file_info["path"]
            content = file_info["content"]
            
            # Resolve path
            if not os.path.isabs(path):
                path = os.path.join(context.working_directory, path)
            
            path = os.path.normpath(path)
            
            try:
                # Check if exists
                if os.path.exists(path) and not tool_input.overwrite:
                    results.append(f"⏭️ Skipped: {path} (exists)")
                    error_count += 1
                    continue
                
                # Create parent directories
                parent = Path(path).parent
                if parent and not parent.exists():
                    parent.mkdir(parents=True, exist_ok=True)
                
                # Write file
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                results.append(f"✅ Created: {path}")
                success_count += 1
                
                logger.info("File created", path=path)
                
            except Exception as e:
                results.append(f"❌ Error: {path} - {e}")
                error_count += 1
                logger.error("File creation failed", path=path, error=str(e))
        
        # Build summary
        summary = [
            f"📁 Batch file creation complete",
            f"✅ Success: {success_count}",
            f"❌ Errors: {error_count}",
            "",
        ]
        summary.extend(results[:20])  # Limit output
        
        if len(results) > 20:
            summary.append(f"... and {len(results) - 20} more")
        
        is_error = error_count > 0 and error_count == len(tool_input.files)
        
        return ToolResult(
            content=[{"type": "text", "text": "\n".join(summary)}],
            is_error=is_error,
        )
