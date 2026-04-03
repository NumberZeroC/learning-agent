"""Glob tool for finding files by pattern"""

from __future__ import annotations

import os
import fnmatch
from pathlib import Path
from typing import Any

import structlog

from .base import Tool, ToolContext, ValidationResult
from ..models.tools import ToolInput, ToolResult

logger = structlog.get_logger(__name__)


class GlobInput(ToolInput):
    """Input for Glob tool"""
    
    pattern: str
    path: str | None = None
    include_dirs: bool = False
    recursive: bool = True
    max_results: int | None = None


class GlobTool(Tool[GlobInput]):
    """
    Tool for finding files by glob pattern.
    
    Features:
    - Glob pattern matching
    - Recursive search
    - Directory filtering
    - Result limits
    """
    
    name = "glob"
    description = "Find files matching a glob pattern"
    
    input_schema = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Glob pattern to match (e.g., '*.py', '**/*.txt')"
            },
            "path": {
                "type": "string",
                "description": "Directory to search (default: current directory)"
            },
            "include_dirs": {
                "type": "boolean",
                "description": "Include directories in results"
            },
            "recursive": {
                "type": "boolean",
                "description": "Search recursively (default: true)"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results (default: 100)"
            }
        },
        "required": ["pattern"]
    }
    
    # Configuration
    DEFAULT_MAX_RESULTS = 100
    MAX_MAX_RESULTS = 1000
    
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
        ".tox",
        ".eggs",
        "*.egg-info",
    ]
    
    def get_prompt(self) -> str:
        """Get prompt describing how to use this tool"""
        return """Use the `glob` tool to find files matching a pattern.

Glob patterns:
- `*` matches everything except path separators
- `**` matches everything including path separators
- `?` matches a single character
- `[seq]` matches any character in seq
- `[!seq]` matches any character not in seq

Examples:

Find all Python files:
{
    "pattern": "**/*.py"
}

Find all test files:
{
    "pattern": "**/test_*.py"
}

Find config files in current directory:
{
    "pattern": "*.{json,yaml,yml,toml}",
    "recursive": false
}

Find all markdown documentation:
{
    "pattern": "**/*.md",
    "exclude": "node_modules"
}"""
    
    async def validate_input(
        self,
        tool_input: dict,
        context: ToolContext,
    ) -> ValidationResult:
        """Validate glob input"""
        
        pattern = tool_input.get("pattern", "")
        
        if not pattern:
            return ValidationResult.fail("Pattern is required")
        
        # Validate max_results
        max_results = tool_input.get("max_results", self.DEFAULT_MAX_RESULTS)
        if max_results <= 0 or max_results > self.MAX_MAX_RESULTS:
            return ValidationResult.fail(
                f"max_results must be between 1 and {self.MAX_MAX_RESULTS}",
                error_code="INVALID_MAX_RESULTS"
            )
        
        return ValidationResult.ok()
    
    async def execute(self, tool_input: GlobInput, context: ToolContext) -> ToolResult:
        """Execute glob search"""
        
        # Determine search path
        search_path = tool_input.path or context.working_directory or "."
        
        if not os.path.isabs(search_path):
            search_path = os.path.join(context.working_directory, search_path)
        
        search_path = os.path.normpath(search_path)
        
        logger.info(
            "Glob search requested",
            pattern=tool_input.pattern,
            path=search_path,
            recursive=tool_input.recursive,
        )
        
        try:
            # Perform glob search
            matches = await self._find_files(
                search_path,
                tool_input.pattern,
                recursive=tool_input.recursive,
                include_dirs=tool_input.include_dirs,
                max_results=tool_input.max_results or self.DEFAULT_MAX_RESULTS,
            )
            
            # Build output
            if not matches:
                return ToolResult.success([
                    {"type": "text", "text": f"No files found matching: {tool_input.pattern}"}
                ])
            
            output = self._format_output(matches, tool_input, search_path)
            
            return ToolResult.success([
                {"type": "text", "text": output}
            ])
            
        except Exception as e:
            logger.exception("Glob error", pattern=tool_input.pattern)
            return ToolResult.error(f"Search error: {str(e)}")
    
    async def _find_files(
        self,
        search_path: str,
        pattern: str,
        recursive: bool = True,
        include_dirs: bool = False,
        max_results: int = 100,
    ) -> list[dict[str, Any]]:
        """Find files matching the pattern"""
        
        matches = []
        
        if recursive:
            # Use pathlib for recursive glob
            path = Path(search_path)
            
            try:
                # Try pathlib glob first
                if "**" in pattern:
                    # Recursive pattern
                    glob_results = path.glob(pattern)
                else:
                    # Non-recursive
                    glob_results = path.glob(pattern)
                
                for match in glob_results:
                    if len(matches) >= max_results:
                        break
                    
                    # Skip excluded directories
                    if match.is_dir():
                        if any(excluded in str(match) for excluded in self.EXCLUDED_DIRS):
                            continue
                        if not include_dirs:
                            continue
                    
                    try:
                        stat = match.stat()
                        matches.append({
                            "path": str(match),
                            "name": match.name,
                            "is_dir": match.is_dir(),
                            "size": stat.st_size if not match.is_dir() else 0,
                            "modified": stat.st_mtime,
                        })
                    except (OSError, IOError):
                        continue
                        
            except Exception as e:
                logger.warning("pathlib glob failed, using fallback", error=str(e))
                # Fallback to manual walk
                matches = await self._find_files_fallback(
                    search_path,
                    pattern,
                    recursive,
                    include_dirs,
                    max_results,
                )
        else:
            # Non-recursive: use os.listdir
            try:
                for entry in os.listdir(search_path):
                    if len(matches) >= max_results:
                        break
                    
                    if fnmatch.fnmatch(entry, pattern):
                        full_path = os.path.join(search_path, entry)
                        
                        try:
                            stat = os.stat(full_path)
                            matches.append({
                                "path": full_path,
                                "name": entry,
                                "is_dir": os.path.isdir(full_path),
                                "size": stat.st_size if os.path.isfile(full_path) else 0,
                                "modified": stat.st_mtime,
                            })
                        except (OSError, IOError):
                            continue
            except (OSError, IOError) as e:
                logger.warning("os.listdir failed", error=str(e))
        
        return matches
    
    async def _find_files_fallback(
        self,
        search_path: str,
        pattern: str,
        recursive: bool,
        include_dirs: bool,
        max_results: int,
    ) -> list[dict[str, Any]]:
        """Fallback manual file finding"""
        
        matches = []
        
        for root, dirs, files in os.walk(search_path):
            if len(matches) >= max_results:
                break
            
            # Filter excluded directories
            dirs[:] = [
                d for d in dirs
                if not any(excluded in d for excluded in self.EXCLUDED_DIRS)
            ]
            
            # Check directories
            if include_dirs:
                for d in dirs:
                    if len(matches) >= max_results:
                        break
                    
                    if fnmatch.fnmatch(d, pattern):
                        full_path = os.path.join(root, d)
                        try:
                            stat = os.stat(full_path)
                            matches.append({
                                "path": full_path,
                                "name": d,
                                "is_dir": True,
                                "size": 0,
                                "modified": stat.st_mtime,
                            })
                        except (OSError, IOError):
                            continue
            
            # Check files
            for f in files:
                if len(matches) >= max_results:
                    break
                
                if fnmatch.fnmatch(f, pattern):
                    full_path = os.path.join(root, f)
                    try:
                        stat = os.stat(full_path)
                        matches.append({
                            "path": full_path,
                            "name": f,
                            "is_dir": False,
                            "size": stat.st_size,
                            "modified": stat.st_mtime,
                        })
                    except (OSError, IOError):
                        continue
            
            if not recursive:
                break
        
        return matches
    
    def _format_output(
        self,
        matches: list[dict[str, Any]],
        tool_input: GlobInput,
        search_path: str,
    ) -> str:
        """Format glob results for display"""
        lines = [
            f"📁 File search results for: `{tool_input.pattern}`",
            f"📍 Path: {search_path}",
            f"🔢 Recursive: {'Yes' if tool_input.recursive else 'No'}",
            "",
            f"**{len(matches)} files found**",
            "",
        ]
        
        # Group by directory
        by_dir: dict[str, list] = {}
        for match in matches:
            dir_path = os.path.dirname(match["path"])
            if dir_path not in by_dir:
                by_dir[dir_path] = []
            by_dir[dir_path].append(match)
        
        for dir_path, files in sorted(by_dir.items()):
            lines.append(f"📂 {dir_path}/")
            
            for f in sorted(files, key=lambda x: x["name"]):
                icon = "📁" if f["is_dir"] else "📄"
                size = ""
                if not f["is_dir"] and f["size"] > 0:
                    size = f" ({self._format_size(f['size'])})"
                lines.append(f"   {icon} {f['name']}{size}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_size(self, size: int) -> str:
        """Format file size"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"
