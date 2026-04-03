"""Grep tool for searching text in files"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Literal

import structlog

from .base import Tool, ToolContext, ValidationResult
from ..models.tools import ToolInput, ToolResult

logger = structlog.get_logger(__name__)


class GrepInput(ToolInput):
    """Input for Grep tool"""
    
    pattern: str
    path: str | None = None
    include: str | None = None
    exclude: str | None = None
    ignore_case: bool = False
    max_results: int | None = None
    context_lines: int = 0


class GrepTool(Tool[GrepInput]):
    """
    Tool for searching text in files using grep.
    
    Features:
    - Regex pattern matching
    - File type filtering
    - Context lines
    - Result limits
    - Cross-platform support
    """
    
    name = "grep"
    description = "Search for text patterns in files using grep"
    
    input_schema = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Regular expression pattern to search for"
            },
            "path": {
                "type": "string",
                "description": "Directory or file to search (default: current directory)"
            },
            "include": {
                "type": "string",
                "description": "Glob pattern for files to include (e.g., '*.py')"
            },
            "exclude": {
                "type": "string",
                "description": "Glob pattern for files to exclude (e.g., '*.log')"
            },
            "ignore_case": {
                "type": "boolean",
                "description": "Case-insensitive search"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (default: 100)"
            },
            "context_lines": {
                "type": "integer",
                "description": "Number of context lines to show (default: 0)"
            }
        },
        "required": ["pattern"]
    }
    
    # Configuration
    DEFAULT_MAX_RESULTS = 100
    MAX_MAX_RESULTS = 1000
    DEFAULT_CONTEXT_LINES = 0
    
    # Excluded directories
    EXCLUDED_DIRS = [
        ".git",
        ".svn",
        ".hg",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        "vendor",
        "dist",
        "build",
        ".min.",
    ]
    
    def get_prompt(self) -> str:
        """Get prompt describing how to use this tool"""
        return """Use the `grep` tool to search for text patterns in files.

Features:
- Regular expression pattern matching
- File type filtering (include/exclude)
- Context lines around matches
- Case-insensitive search option

Examples:

Search for a function definition:
{
    "pattern": "def main\\(",
    "include": "*.py"
}

Search with context:
{
    "pattern": "TODO",
    "context_lines": 2,
    "max_results": 50
}

Case-insensitive search:
{
    "pattern": "error",
    "ignore_case": true,
    "exclude": "*.log"
}"""
    
    async def validate_input(
        self,
        tool_input: dict,
        context: ToolContext,
    ) -> ValidationResult:
        """Validate grep input"""
        
        pattern = tool_input.get("pattern", "")
        
        if not pattern:
            return ValidationResult.fail("Pattern is required")
        
        # Validate regex pattern
        try:
            re.compile(pattern)
        except re.error as e:
            return ValidationResult.fail(
                f"Invalid regex pattern: {e}",
                error_code="INVALID_REGEX"
            )
        
        # Validate max_results
        max_results = tool_input.get("max_results", self.DEFAULT_MAX_RESULTS)
        if max_results <= 0 or max_results > self.MAX_MAX_RESULTS:
            return ValidationResult.fail(
                f"max_results must be between 1 and {self.MAX_MAX_RESULTS}",
                error_code="INVALID_MAX_RESULTS"
            )
        
        # Validate context_lines
        context_lines = tool_input.get("context_lines", 0)
        if context_lines < 0 or context_lines > 10:
            return ValidationResult.fail(
                "context_lines must be between 0 and 10",
                error_code="INVALID_CONTEXT_LINES"
            )
        
        return ValidationResult.ok()
    
    async def execute(self, tool_input: GrepInput, context: ToolContext) -> ToolResult:
        """Execute grep search"""
        
        # Determine search path
        search_path = tool_input.path or context.working_directory or "."
        
        if not os.path.isabs(search_path):
            search_path = os.path.join(context.working_directory, search_path)
        
        search_path = os.path.normpath(search_path)
        
        logger.info(
            "Grep search requested",
            pattern=tool_input.pattern,
            path=search_path,
            include=tool_input.include,
            exclude=tool_input.exclude,
        )
        
        try:
            # Build grep command
            cmd = self._build_command(tool_input, search_path)
            
            # Execute grep
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            # Parse results
            matches = self._parse_results(result.stdout, tool_input.context_lines)
            
            # Limit results
            max_results = tool_input.max_results or self.DEFAULT_MAX_RESULTS
            if len(matches) > max_results:
                matches = matches[:max_results]
                truncated = True
            else:
                truncated = False
            
            # Build output
            if not matches:
                return ToolResult.success([
                    {"type": "text", "text": f"No matches found for pattern: {tool_input.pattern}"}
                ])
            
            output = self._format_output(matches, tool_input, search_path, truncated)
            
            return ToolResult.success([
                {"type": "text", "text": output}
            ])
            
        except subprocess.TimeoutExpired:
            logger.warning("Grep search timed out", pattern=tool_input.pattern)
            return ToolResult.error("Search timed out. Try narrowing your search.")
        except FileNotFoundError:
            # Fallback to Python implementation if grep not available
            return await self._python_grep(tool_input, search_path, context)
        except Exception as e:
            logger.exception("Grep error", pattern=tool_input.pattern)
            return ToolResult.error(f"Search error: {str(e)}")
    
    def _build_command(self, tool_input: GrepInput, search_path: str) -> list[str]:
        """Build grep command"""
        cmd = ["grep"]
        
        # Options
        cmd.append("-n")  # Line numbers
        cmd.append("-H")  # File names
        cmd.append("-P")  # Perl regex
        
        if tool_input.ignore_case:
            cmd.append("-i")
        
        if tool_input.context_lines > 0:
            cmd.append(f"-C{tool_input.context_lines}")
        
        # Include/exclude patterns
        if tool_input.include:
            cmd.append("--include=" + tool_input.include)
        
        if tool_input.exclude:
            cmd.append("--exclude=" + tool_input.exclude)
        
        # Exclude directories
        for excluded in self.EXCLUDED_DIRS:
            cmd.append("--exclude-dir=" + excluded)
        
        # Pattern and path
        cmd.append(tool_input.pattern)
        cmd.append(search_path)
        
        return cmd
    
    def _parse_results(self, output: str, context_lines: int) -> list[dict]:
        """Parse grep output"""
        matches = []
        
        if not output.strip():
            return matches
        
        current_file = None
        current_line = None
        
        for line in output.split("\n"):
            if not line.strip():
                continue
            
            # Check for context line markers
            if context_lines > 0 and line.startswith("--"):
                continue
            
            # Parse grep output: file:line:content or file-line-content (for context)
            parts = line.split(":", 2)
            
            if len(parts) >= 3:
                file_path = parts[0]
                try:
                    line_num = int(parts[1])
                    content = parts[2]
                except ValueError:
                    # Context line
                    continue
                
                if file_path != current_file:
                    current_file = file_path
                
                matches.append({
                    "file": file_path,
                    "line": line_num,
                    "content": content,
                })
            elif len(parts) == 2 and context_lines > 0:
                # Context line
                try:
                    line_num = int(parts[0])
                    content = parts[1]
                    matches.append({
                        "file": current_file,
                        "line": line_num,
                        "content": content,
                        "is_context": True,
                    })
                except ValueError:
                    pass
        
        return matches
    
    def _format_output(
        self,
        matches: list[dict],
        tool_input: GrepInput,
        search_path: str,
        truncated: bool,
    ) -> str:
        """Format grep results for display"""
        lines = [
            f"🔍 Search results for: `{tool_input.pattern}`",
            f"📁 Path: {search_path}",
            "",
            f"**{len(matches)} matches found**",
            "",
        ]
        
        # Group by file
        by_file: dict[str, list] = {}
        for match in matches:
            file_path = match["file"]
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(match)
        
        for file_path, file_matches in by_file.items():
            lines.append(f"📄 {file_path}")
            
            for match in file_matches:
                line_num = match["line"]
                content = match["content"].strip()
                
                if match.get("is_context"):
                    lines.append(f"  {line_num}: {content}")
                else:
                    # Highlight match
                    try:
                        highlighted = self._highlight_match(
                            content,
                            tool_input.pattern,
                            tool_input.ignore_case,
                        )
                    except re.error:
                        highlighted = content
                    
                    lines.append(f"  {line_num}: {highlighted}")
            
            lines.append("")
        
        if truncated:
            max_results = tool_input.max_results or self.DEFAULT_MAX_RESULTS
            lines.append(f"⚠️ Results truncated. Showing first {max_results} matches.")
        
        return "\n".join(lines)
    
    def _highlight_match(self, text: str, pattern: str, ignore_case: bool) -> str:
        """Highlight matched text"""
        flags = re.IGNORECASE if ignore_case else 0
        regex = re.compile(f"({pattern})", flags)
        return regex.sub(r"[bold green]\1[/bold green]", text)
    
    async def _python_grep(
        self,
        tool_input: GrepInput,
        search_path: str,
        context: ToolContext,
    ) -> ToolResult:
        """Fallback Python implementation when grep is not available"""
        
        import fnmatch
        
        pattern = re.compile(
            tool_input.pattern,
            re.IGNORECASE if tool_input.ignore_case else 0,
        )
        
        matches = []
        max_results = tool_input.max_results or self.DEFAULT_MAX_RESULTS
        
        # Walk directory
        for root, dirs, files in os.walk(search_path):
            # Filter excluded directories
            dirs[:] = [
                d for d in dirs
                if not any(excluded in d for excluded in self.EXCLUDED_DIRS)
            ]
            
            for filename in files:
                # Check include/exclude patterns
                if tool_input.include and not fnmatch.fnmatch(filename, tool_input.include):
                    continue
                if tool_input.exclude and fnmatch.fnmatch(filename, tool_input.exclude):
                    continue
                
                file_path = os.path.join(root, filename)
                
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line_num, line in enumerate(f, 1):
                            if pattern.search(line):
                                matches.append({
                                    "file": file_path,
                                    "line": line_num,
                                    "content": line.strip(),
                                })
                                
                                if len(matches) >= max_results:
                                    break
                except (IOError, OSError):
                    continue
            
            if len(matches) >= max_results:
                break
        
        if not matches:
            return ToolResult.success([
                {"type": "text", "text": f"No matches found for pattern: {tool_input.pattern}"}
            ])
        
        output = self._format_output(
            matches,
            tool_input,
            search_path,
            len(matches) >= max_results,
        )
        
        return ToolResult.success([{"type": "text", "text": output}])
