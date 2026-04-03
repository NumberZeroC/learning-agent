"""Permission engine for evaluating access requests"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog

from .policies import Policy, PermissionMode

logger = structlog.get_logger(__name__)


@dataclass
class PermissionResult:
    """
    Result of a permission check.
    
    Attributes:
        granted: Whether permission is granted
        requires_approval: Whether user approval is needed
        reason: Human-readable reason for the decision
        policy: Name of the policy that made the decision (if any)
        suggestions: Alternative suggestions (if denied)
    """
    
    granted: bool = False
    requires_approval: bool = False
    reason: str = ""
    policy: str | None = None
    suggestions: list[str] = field(default_factory=list)
    
    @classmethod
    def allow(cls, reason: str = "", policy: str | None = None) -> "PermissionResult":
        """Create an allow result"""
        return cls(granted=True, reason=reason or "Permission granted", policy=policy)
    
    @classmethod
    def deny(cls, reason: str = "", policy: str | None = None, suggestions: list[str] | None = None) -> "PermissionResult":
        """Create a deny result"""
        return cls(
            granted=False,
            reason=reason or "Permission denied",
            policy=policy,
            suggestions=suggestions or [],
        )
    
    @classmethod
    def ask(cls, reason: str = "") -> "PermissionResult":
        """Create an ask result (requires user approval)"""
        return cls(
            granted=False,
            requires_approval=True,
            reason=reason or "User approval required",
        )
    
    def __bool__(self) -> bool:
        return self.granted


@dataclass
class PermissionContext:
    """Context for permission evaluation"""
    
    # Tool info
    tool_name: str
    tool_input: dict[str, Any]
    
    # Resource info
    resource: str | None = None  # e.g., file path
    action: str | None = None  # read, write, execute, delete
    
    # Command info (for bash tool)
    command: str | None = None
    
    # Session info
    session_id: str | None = None
    user_id: str | None = None
    
    # Current mode
    mode: PermissionMode = PermissionMode.AUTO_SAFE
    
    # Extra context
    extras: dict[str, Any] = field(default_factory=dict)


class PermissionEngine:
    """
    Permission engine for evaluating tool access requests.
    
    The engine evaluates policies in priority order and makes decisions
    based on the first matching policy. If no policy matches, it falls
    back to the current permission mode.
    
    Usage:
        engine = PermissionEngine()
        engine.add_policy(create_safe_file_policy())
        engine.add_policy(create_dangerous_command_policy())
        
        result = engine.check(
            tool_name="bash",
            command="rm -rf test",
            mode=PermissionMode.AUTO_SAFE,
        )
        
        if result.granted:
            # Execute
        elif result.requires_approval:
            # Ask user
        else:
            # Deny
    """
    
    def __init__(self):
        self._policies: list[Policy] = []
        self._default_mode = PermissionMode.AUTO_SAFE
        
        # Statistics
        self._allow_count = 0
        self._deny_count = 0
        self._ask_count = 0
    
    @property
    def policies(self) -> list[Policy]:
        """Get all policies (sorted by priority)"""
        return sorted(self._policies, key=lambda p: p.priority, reverse=True)
    
    @property
    def stats(self) -> dict[str, int]:
        """Get permission statistics"""
        return {
            "policies": len(self._policies),
            "allows": self._allow_count,
            "denies": self._deny_count,
            "asks": self._ask_count,
        }
    
    def add_policy(self, policy: Policy) -> None:
        """Add a policy to the engine"""
        self._policies.append(policy)
        logger.info("Policy added", name=policy.name, priority=policy.priority)
    
    def remove_policy(self, name: str) -> bool:
        """Remove a policy by name"""
        for i, policy in enumerate(self._policies):
            if policy.name == name:
                removed = self._policies.pop(i)
                logger.info("Policy removed", name=name)
                return True
        return False
    
    def get_policy(self, name: str) -> Policy | None:
        """Get a policy by name"""
        for policy in self._policies:
            if policy.name == name:
                return policy
        return None
    
    def enable_policy(self, name: str) -> bool:
        """Enable a policy"""
        policy = self.get_policy(name)
        if policy:
            policy.enabled = True
            logger.info("Policy enabled", name=name)
            return True
        return False
    
    def disable_policy(self, name: str) -> bool:
        """Disable a policy"""
        policy = self.get_policy(name)
        if policy:
            policy.enabled = False
            logger.info("Policy disabled", name=name)
            return True
        return False
    
    def clear_policies(self) -> None:
        """Remove all policies"""
        self._policies.clear()
        logger.info("All policies cleared")
    
    def check(
        self,
        tool_name: str,
        tool_input: dict[str, Any] | None = None,
        resource: str | None = None,
        action: str | None = None,
        command: str | None = None,
        mode: PermissionMode | None = None,
        session_id: str | None = None,
    ) -> PermissionResult:
        """
        Check if a tool operation is permitted.
        
        Args:
            tool_name: Name of the tool
            tool_input: Tool input dictionary
            resource: Resource path (e.g., file path)
            action: Action type (read/write/execute/delete)
            command: Command string (for bash tool)
            mode: Permission mode (overrides default)
            session_id: Session identifier
        
        Returns:
            PermissionResult with decision
        """
        
        mode = mode or self._default_mode
        
        # Build context
        context = PermissionContext(
            tool_name=tool_name,
            tool_input=tool_input or {},
            resource=resource,
            action=action,
            command=command,
            session_id=session_id,
            mode=mode,
        )
        
        # Extract resource from tool_input if not provided
        if not resource and tool_input:
            resource = tool_input.get("file_path") or tool_input.get("path")
        
        # Extract command from tool_input if not provided
        if not command and tool_input:
            command = tool_input.get("command")
        
        # Infer action from tool name
        if not action:
            action = self._infer_action(tool_name, tool_input)
        
        logger.debug(
            "Permission check",
            tool=tool_name,
            resource=resource,
            action=action,
            command=command[:50] if command else None,
            mode=mode.value,
        )
        
        # Check policies in priority order
        for policy in self.policies:
            if policy.matches(
                tool_name=tool_name,
                resource=resource,
                command=command,
                action=action,
            ):
                result = self._evaluate_policy(policy, context)
                if result is not None:
                    return result
        
        # No policy matched - use mode-based decision
        result = self._mode_decision(mode, tool_name, action, command)
        
        # Update stats
        self._update_stats(result)
        
        return result
    
    def _evaluate_policy(
        self,
        policy: Policy,
        context: PermissionContext,
    ) -> PermissionResult | None:
        """Evaluate a single policy"""
        
        if policy.auto_allow:
            return PermissionResult.allow(
                reason=f"Allowed by policy: {policy.name}",
                policy=policy.name,
            )
        
        if policy.auto_deny:
            return PermissionResult.deny(
                reason=f"Denied by policy: {policy.name}",
                policy=policy.name,
                suggestions=self._get_suggestions(policy, context),
            )
        
        # Policy requires approval
        return PermissionResult.ask(
            reason=f"Policy {policy.name} requires approval",
        )
    
    def _mode_decision(
        self,
        mode: PermissionMode,
        tool_name: str,
        action: str | None,
        command: str | None,
    ) -> PermissionResult:
        """Make decision based on permission mode"""
        
        if mode == PermissionMode.FULL_AUTO:
            return PermissionResult.allow("Full auto mode")
        
        if mode == PermissionMode.ALWAYS_ASK:
            return PermissionResult.ask("Always ask mode")
        
        if mode == PermissionMode.AUTO_EDIT:
            if tool_name in ("file_read", "file_edit", "file_write"):
                return PermissionResult.allow("Auto-edit mode")
            return PermissionResult.ask("Command requires approval")
        
        if mode == PermissionMode.AUTO_SAFE:
            # Check if operation is safe
            if self._is_safe_operation(tool_name, action, command):
                return PermissionResult.allow("Safe operation")
            return PermissionResult.ask("Operation requires approval")
        
        # Default to asking
        return PermissionResult.ask("Default: approval required")
    
    def _is_safe_operation(
        self,
        tool_name: str,
        action: str | None,
        command: str | None,
    ) -> bool:
        """Check if operation is considered safe"""
        
        # Read operations are safe
        if tool_name == "file_read":
            return True
        
        # Safe bash commands
        if tool_name == "bash" and command:
            safe_prefixes = [
                "ls ", "pwd", "cat ", "head ", "tail ",
                "wc ", "grep ", "find ", "which ",
                "echo ", "true", "false",
            ]
            return any(command.startswith(p) for p in safe_prefixes)
        
        # File edits are generally safe (can be reverted)
        if tool_name in ("file_edit", "file_write"):
            return True
        
        return False
    
    def _infer_action(
        self,
        tool_name: str,
        tool_input: dict[str, Any] | None,
    ) -> str | None:
        """Infer action type from tool and input"""
        
        if tool_name == "file_read":
            return "read"
        elif tool_name == "file_write":
            return "write"
        elif tool_name == "file_edit":
            edit_type = tool_input.get("edit_type", "replace") if tool_input else "replace"
            if edit_type == "delete":
                return "delete"
            return "write"
        elif tool_name == "bash":
            return "execute"
        
        return None
    
    def _get_suggestions(
        self,
        policy: Policy,
        context: PermissionContext,
    ) -> list[str]:
        """Get suggestions for denied operations"""
        
        suggestions = []
        
        if policy.name == "dangerous-commands":
            suggestions.append("Consider using a safer alternative")
            suggestions.append("Run in a sandboxed environment")
            suggestions.append("Use file operations instead of shell commands")
        
        return suggestions
    
    def _update_stats(self, result: PermissionResult) -> None:
        """Update statistics"""
        if result.granted:
            self._allow_count += 1
        elif result.requires_approval:
            self._ask_count += 1
        else:
            self._deny_count += 1
    
    def reset_stats(self) -> None:
        """Reset statistics"""
        self._allow_count = 0
        self._deny_count = 0
        self._ask_count = 0
    
    def list_policies(self) -> list[dict[str, Any]]:
        """List all policies as dictionaries"""
        return [
            {
                "name": p.name,
                "description": p.description,
                "enabled": p.enabled,
                "priority": p.priority,
                "decision": "allow" if p.auto_allow else ("deny" if p.auto_deny else "ask"),
                "tool_pattern": p.tool_pattern,
                "resource_pattern": p.resource_pattern,
            }
            for p in self.policies
        ]
    
    def __repr__(self) -> str:
        return f"PermissionEngine(policies={len(self._policies)}, mode={self._default_mode.value})"
