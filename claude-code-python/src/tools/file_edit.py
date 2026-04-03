"""File edit tool for modifying file contents"""

from __future__ import annotations

import os
import difflib
from datetime import datetime
from pathlib import Path

import structlog

from .base import Tool, ToolContext, ValidationResult
from ..models.tools import ToolInput, ToolResult

logger = structlog.get_logger(__name__)


class FileEditInput(ToolInput):
    """Input for FileEdit tool"""
    
    file_path: str
    old_text: str | None = None
    new_text: str
    edit_type: str = "replace"  # replace, insert, delete
    insert_position: int | None = None  # For insert: line number


class FileEditTool(Tool[FileEditInput]):
    """
    Tool for editing files with fine-grained control.
    
    Features:
    - Search and replace
    - Insert at position
    - Delete sections
    - Diff generation
    - Backup creation
    """
    
    name = "file_edit"
    description = "Edit files with search/replace or positional operations"
    
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to edit"
            },
            "old_text": {
                "type": "string",
                "description": "Text to search for (required for replace/delete)"
            },
            "new_text": {
                "type": "string",
                "description": "New text to insert"
            },
            "edit_type": {
                "type": "string",
                "enum": ["replace", "insert", "delete"],
                "description": "Type of edit operation"
            },
            "insert_position": {
                "type": "integer",
                "description": "Line number for insert (0-indexed)"
            }
        },
        "required": ["file_path", "new_text", "edit_type"]
    }
    
    # Configuration
    MAX_EDIT_SIZE = 100000  # Maximum characters in a single edit
    BACKUP_ENABLED = True
    BACKUP_DIR = ".ccp_backups"
    
    def get_prompt(self) -> str:
        """Get prompt describing how to use this tool"""
        return """Use the `file_edit` tool to modify file contents.

Edit types:
1. replace: Find old_text and replace with new_text
2. insert: Insert new_text at insert_position line
3. delete: Remove old_text from file

Guidelines:
- For replace, old_text must match exactly (including whitespace)
- Use small, targeted edits rather than large rewrites
- The tool will show a diff before applying changes
- Backups are automatically created

Examples:

Replace:
{
    "file_path": "src/main.py",
    "old_text": "def old_function():\\n    pass",
    "new_text": "def new_function():\\n    return True",
    "edit_type": "replace"
}

Insert at line 10:
{
    "file_path": "src/main.py",
    "new_text": "# New comment",
    "edit_type": "insert",
    "insert_position": 10
}"""
    
    async def validate_input(
        self,
        tool_input: dict,
        context: ToolContext,
    ) -> ValidationResult:
        """Validate file edit input"""
        
        file_path = tool_input.get("file_path", "")
        edit_type = tool_input.get("edit_type", "replace")
        old_text = tool_input.get("old_text")
        new_text = tool_input.get("new_text", "")
        insert_position = tool_input.get("insert_position")
        
        # Validate file path
        if not file_path:
            return ValidationResult.fail("File path is required")
        
        # Resolve to absolute path
        if not os.path.isabs(file_path):
            file_path = os.path.join(context.working_directory, file_path)
        
        # Check if file exists (for replace/delete)
        if edit_type in ("replace", "delete"):
            if not os.path.exists(file_path):
                return ValidationResult.fail(
                    f"File does not exist: {file_path}",
                    error_code="FILE_NOT_FOUND"
                )
            
            if not os.path.isfile(file_path):
                return ValidationResult.fail(
                    f"Path is not a file: {file_path}",
                    error_code="NOT_A_FILE"
                )
            
            if not old_text:
                return ValidationResult.fail(
                    "old_text is required for replace/delete operations",
                    error_code="MISSING_OLD_TEXT"
                )
        
        # Validate edit size
        if len(new_text) > self.MAX_EDIT_SIZE:
            return ValidationResult.fail(
                f"Edit too large: {len(new_text)} chars (max: {self.MAX_EDIT_SIZE})",
                error_code="EDIT_TOO_LARGE"
            )
        
        if old_text and len(old_text) > self.MAX_EDIT_SIZE:
            return ValidationResult.fail(
                f"old_text too large: {len(old_text)} chars (max: {self.MAX_EDIT_SIZE})",
                error_code="OLD_TEXT_TOO_LARGE"
            )
        
        # Validate insert position
        if edit_type == "insert":
            if insert_position is None:
                return ValidationResult.fail(
                    "insert_position is required for insert operations",
                    error_code="MISSING_INSERT_POSITION"
                )
            if insert_position < 0:
                return ValidationResult.fail(
                    "insert_position must be non-negative",
                    error_code="INVALID_INSERT_POSITION"
                )
        
        return ValidationResult.ok()
    
    async def execute(self, tool_input: FileEditInput, context: ToolContext) -> ToolResult:
        """Execute file edit"""
        
        # Resolve path
        file_path = tool_input.file_path
        if not os.path.isabs(file_path):
            file_path = os.path.join(context.working_directory, file_path)
        
        file_path = os.path.normpath(file_path)
        
        logger.info(
            "File edit requested",
            file_path=file_path,
            edit_type=tool_input.edit_type,
        )
        
        try:
            # Read original content
            original_content = ""
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    original_content = f.read()
            
            # Perform edit
            if tool_input.edit_type == "replace":
                new_content = self._do_replace(
                    original_content,
                    tool_input.old_text,
                    tool_input.new_text,
                )
            elif tool_input.edit_type == "insert":
                new_content = self._do_insert(
                    original_content,
                    tool_input.new_text,
                    tool_input.insert_position,
                )
            elif tool_input.edit_type == "delete":
                new_content = self._do_delete(
                    original_content,
                    tool_input.old_text,
                )
            else:
                return ToolResult.error(f"Unknown edit type: {tool_input.edit_type}")
            
            # Check if content actually changed
            if new_content == original_content:
                return ToolResult.success([
                    {"type": "text", "text": "No changes made (content unchanged)"}
                ])
            
            # Create backup
            if self.BACKUP_ENABLED and original_content:
                await self._create_backup(file_path, original_content)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
            
            # Write new content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            # Generate diff
            diff = self._generate_diff(
                original_content,
                new_content,
                file_path,
            )
            
            # Build result
            content = [
                {"type": "text", "text": f"✅ File updated: {file_path}"},
                {"type": "diff", "text": diff},
            ]
            
            return ToolResult.success(content)
            
        except FileNotFoundError:
            return ToolResult.error(f"File not found: {file_path}")
        except PermissionError:
            return ToolResult.error(f"Permission denied: {file_path}")
        except Exception as e:
            logger.exception("File edit error", file_path=file_path)
            return ToolResult.error(f"Edit error: {str(e)}")
    
    def _do_replace(
        self,
        original: str,
        old_text: str,
        new_text: str,
    ) -> str:
        """Perform replace operation"""
        
        if old_text not in original:
            # Try to find similar text
            similar = self._find_similar_text(original, old_text)
            if similar:
                raise ValueError(
                    f"old_text not found. Did you mean: {similar[:50]}...?"
                )
            raise ValueError("old_text not found in file")
        
        # Replace only first occurrence
        return original.replace(old_text, new_text, 1)
    
    def _do_insert(
        self,
        original: str,
        new_text: str,
        position: int | None,
    ) -> str:
        """Perform insert operation"""
        
        lines = original.splitlines(keepends=True)
        
        if position is None:
            # Append to end
            if original and not original.endswith("\n"):
                original += "\n"
            return original + new_text
        
        # Insert at position
        if position > len(lines):
            position = len(lines)
        
        # Ensure new_text ends with newline if inserting in middle
        if position < len(lines) and not new_text.endswith("\n"):
            new_text += "\n"
        
        lines.insert(position, new_text)
        return "".join(lines)
    
    def _do_delete(
        self,
        original: str,
        old_text: str,
    ) -> str:
        """Perform delete operation"""
        
        if old_text not in original:
            raise ValueError("old_text not found in file")
        
        return original.replace(old_text, "", 1)
    
    def _find_similar_text(
        self,
        content: str,
        target: str,
        threshold: float = 0.8,
    ) -> str | None:
        """Find similar text in content"""
        
        # Simple line-by-line comparison
        content_lines = content.splitlines()
        target_lines = target.splitlines()
        
        for i, line in enumerate(content_lines):
            if target_lines[0] in line:
                # Found potential match, get surrounding context
                start = max(0, i - 1)
                end = min(len(content_lines), i + len(target_lines) + 1)
                return "\n".join(content_lines[start:end])
        
        return None
    
    def _generate_diff(
        self,
        original: str,
        new: str,
        filename: str,
    ) -> str:
        """Generate unified diff"""
        
        original_lines = original.splitlines(keepends=True)
        new_lines = new.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            new_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            n=3,  # Context lines
        )
        
        return "".join(diff)
    
    async def _create_backup(self, file_path: str, content: str) -> str:
        """Create backup of file"""
        
        # Create backup directory
        backup_dir = os.path.join(
            os.path.dirname(file_path) or ".",
            self.BACKUP_DIR,
        )
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        basename = os.path.basename(file_path)
        backup_path = os.path.join(backup_dir, f"{basename}.{timestamp}.bak")
        
        # Write backup
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.debug("Backup created", path=backup_path)
        return backup_path
