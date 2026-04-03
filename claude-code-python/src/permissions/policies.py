"""Permission policies and modes"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

import structlog

logger = structlog.get_logger(__name__)


class PermissionMode(Enum):
    """Permission modes controlling approval behavior"""
    
    ALWAYS_ASK = "always_ask"
    """Ask for approval on every tool use"""
    
    AUTO_EDIT = "auto_edit"
    """Auto-approve file edits, ask for commands"""
    
    AUTO_SAFE = "auto_safe"
    """Auto-approve safe operations, ask for potentially dangerous ones"""
    
    FULL_AUTO = "full_auto"
    """Auto-approve everything (not recommended)"""
    
    @classmethod
    def from_string(cls, value: str) -> "PermissionMode":
        """Create PermissionMode from string"""
        try:
            return cls(value.lower())
        except ValueError:
            logger.warning(f"Invalid permission mode: {value}, defaulting to AUTO_SAFE")
            return cls.AUTO_SAFE


@dataclass
class Policy:
    """
    Permission policy for matching and controlling tool access.
    
    Policies can match on:
    - Tool name (exact or pattern)
    - Resource path (glob pattern)
    - Command patterns (for bash tool)
    
    Example:
        Policy(
            name="allow-src-edits",
            tool_pattern="file_*",
            resource_pattern="src/**",
            auto_allow=True,
        )
    """
    
    name: str
    description: str = ""
    
    # Tool matching
    tool_pattern: str = "*"  # Glob pattern for tool names
    tool_names: list[str] = field(default_factory=list)  # Exact names
    
    # Resource matching (file paths)
    resource_pattern: str | None = None  # Glob pattern
    resource_paths: list[str] = field(default_factory=list)  # Exact paths
    
    # Command matching (for bash tool)
    command_pattern: str | None = None  # Regex pattern
    
    # Actions
    actions: list[Literal["read", "write", "execute", "delete"]] = field(
        default_factory=lambda: ["read", "write", "execute", "delete"]
    )
    
    # Decision
    auto_allow: bool = False
    auto_deny: bool = False
    
    # Metadata
    priority: int = 0  # Higher priority policies are checked first
    enabled: bool = True
    
    def matches(
        self,
        tool_name: str,
        resource: str | None = None,
        command: str | None = None,
        action: str | None = None,
    ) -> bool:
        """
        Check if this policy matches the given context.
        
        Args:
            tool_name: Name of the tool being used
            resource: Resource path (e.g., file path)
            command: Command string (for bash tool)
            action: Action type (read/write/execute/delete)
        
        Returns:
            True if policy matches
        """
        if not self.enabled:
            return False
        
        # Check tool name
        if not self._matches_tool(tool_name):
            return False
        
        # Check resource
        if resource and not self._matches_resource(resource):
            return False
        
        # Check command
        if command and not self._matches_command(command):
            return False
        
        # Check action
        if action and action not in self.actions:
            return False
        
        return True
    
    def _matches_tool(self, tool_name: str) -> bool:
        """Check if tool name matches"""
        # If tool_names is explicitly set, only match those
        if self.tool_names:
            return tool_name in self.tool_names
        
        # Otherwise, use pattern matching
        return fnmatch.fnmatch(tool_name, self.tool_pattern)
    
    def _matches_resource(self, resource: str) -> bool:
        """Check if resource matches"""
        if not self.resource_pattern and not self.resource_paths:
            return True  # No resource constraint
        
        # Check exact paths
        if resource in self.resource_paths:
            return True
        
        # Check pattern
        if self.resource_pattern:
            if fnmatch.fnmatch(resource, self.resource_pattern):
                return True
            # Also check with ** expansion
            if "**" in self.resource_pattern:
                regex = self._glob_to_regex(self.resource_pattern)
                if re.match(regex, resource):
                    return True
        
        return False
    
    def _matches_command(self, command: str) -> bool:
        """Check if command matches"""
        if not self.command_pattern:
            return True  # No command constraint
        
        try:
            return bool(re.search(self.command_pattern, command))
        except re.error:
            logger.warning(f"Invalid regex in policy {self.name}: {self.command_pattern}")
            return False
    
    def _glob_to_regex(self, glob_pattern: str) -> str:
        """Convert glob pattern to regex"""
        # Escape special regex chars except * and ?
        pattern = re.escape(glob_pattern)
        # Convert glob wildcards to regex
        pattern = pattern.replace(r"\*\*", ".*")  # ** matches anything
        pattern = pattern.replace(r"\*", "[^/]*")  # * matches within path segment
        pattern = pattern.replace(r"\?", ".")  # ? matches single char
        return f"^{pattern}$"
    
    def __str__(self) -> str:
        status = "✓" if self.enabled else "✗"
        decision = "allow" if self.auto_allow else ("deny" if self.auto_deny else "ask")
        return f"Policy({self.name}, {decision}, priority={self.priority}) [{status}]"


# Pre-built policies for common scenarios

def create_safe_file_policy() -> Policy:
    """Create a policy that allows safe file operations"""
    return Policy(
        name="safe-file-ops",
        description="Allow safe file read/edit operations",
        tool_pattern="file_*",
        resource_pattern="**/*",
        auto_allow=True,
        priority=10,
    )


def create_dangerous_command_policy() -> Policy:
    """Create a policy that requires approval for dangerous commands"""
    return Policy(
        name="dangerous-commands",
        description="Require approval for dangerous shell commands",
        tool_pattern="bash",
        command_pattern=r"(rm\s+-rf|sudo|dd\s+if=|chmod\s+-R|chown\s+-R)",
        auto_deny=True,
        priority=100,  # High priority
    )


def create_src_auto_edit_policy() -> Policy:
    """Create a policy for auto-editing source files"""
    return Policy(
        name="src-auto-edit",
        description="Auto-approve edits to source code",
        tool_pattern="file_edit",
        resource_pattern="**/*.{py,js,ts,go,rs,java,c,cpp,h,hpp}",
        auto_allow=True,
        priority=20,
    )


def create_config_readonly_policy() -> Policy:
    """Create a policy that makes config files read-only"""
    return Policy(
        name="config-readonly",
        description="Prevent modification of config files",
        tool_pattern="file_*",
        resource_pattern="**/*.{yaml,yml,json,toml,ini,env}",
        actions=["read"],  # Only allow read
        auto_deny=True,
        priority=50,
    )
