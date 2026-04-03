"""Permission manager with UI integration"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import structlog

from .engine import PermissionEngine, PermissionResult
from .policies import Policy, PermissionMode

logger = structlog.get_logger(__name__)


class PermissionManager:
    """
    High-level permission manager combining engine and UI.
    
    Features:
    - Policy management
    - Statistics tracking
    - Import/Export
    - Preset policies
    """
    
    def __init__(self, engine: PermissionEngine | None = None):
        self.engine = engine or PermissionEngine()
        self._stats = {
            "allowed": 0,
            "denied": 0,
            "asked": 0,
        }
    
    @property
    def mode(self) -> PermissionMode:
        """Get current permission mode"""
        return self.engine._default_mode
    
    @mode.setter
    def mode(self, value: PermissionMode) -> None:
        """Set permission mode"""
        self.engine._default_mode = value
        logger.info("Permission mode changed", mode=value.value)
    
    def check(
        self,
        tool_name: str,
        tool_input: dict[str, Any] | None = None,
        resource: str | None = None,
        action: str | None = None,
        command: str | None = None,
        mode: PermissionMode | None = None,
    ) -> PermissionResult:
        """Check permission"""
        result = self.engine.check(
            tool_name=tool_name,
            tool_input=tool_input,
            resource=resource,
            action=action,
            command=command,
            mode=mode,
        )
        
        # Update stats
        if result.granted:
            self._stats["allowed"] += 1
        elif result.requires_approval:
            self._stats["asked"] += 1
        else:
            self._stats["denied"] += 1
        
        return result
    
    def add_policy(
        self,
        name: str,
        description: str = "",
        tool_pattern: str = "*",
        resource_pattern: str | None = None,
        command_pattern: str | None = None,
        auto_allow: bool = False,
        auto_deny: bool = False,
        priority: int = 0,
    ) -> Policy:
        """Add a new policy"""
        policy = Policy(
            name=name,
            description=description,
            tool_pattern=tool_pattern,
            resource_pattern=resource_pattern,
            command_pattern=command_pattern,
            auto_allow=auto_allow,
            auto_deny=auto_deny,
            priority=priority,
        )
        
        self.engine.add_policy(policy)
        return policy
    
    def remove_policy(self, name: str) -> bool:
        """Remove a policy by name"""
        return self.engine.remove_policy(name)
    
    def list_policies(self) -> list[dict[str, Any]]:
        """List all policies"""
        return self.engine.list_policies()
    
    def get_stats(self) -> dict[str, Any]:
        """Get permission statistics"""
        engine_stats = self.engine.stats
        return {
            **self._stats,
            "policies": engine_stats["policies"],
            "mode": self.mode.value,
        }
    
    def reset_stats(self) -> None:
        """Reset statistics"""
        self._stats = {"allowed": 0, "denied": 0, "asked": 0}
        self.engine.reset_stats()
    
    def export_policies(self, path: str | Path) -> None:
        """Export policies to JSON file"""
        path = Path(path)
        
        data = {
            "version": "1.0",
            "mode": self.mode.value,
            "policies": [
                {
                    "name": p.name,
                    "description": p.description,
                    "tool_pattern": p.tool_pattern,
                    "tool_names": p.tool_names,
                    "resource_pattern": p.resource_pattern,
                    "resource_paths": p.resource_paths,
                    "command_pattern": p.command_pattern,
                    "actions": p.actions,
                    "auto_allow": p.auto_allow,
                    "auto_deny": p.auto_deny,
                    "priority": p.priority,
                    "enabled": p.enabled,
                }
                for p in self.engine.policies
            ],
        }
        
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info("Policies exported", path=path)
    
    def import_policies(self, path: str | Path, merge: bool = False) -> int:
        """Import policies from JSON file"""
        path = Path(path)
        
        with open(path, "r") as f:
            data = json.load(f)
        
        if not merge:
            self.engine.clear_policies()
        
        count = 0
        for policy_data in data.get("policies", []):
            policy = Policy(
                name=policy_data["name"],
                description=policy_data.get("description", ""),
                tool_pattern=policy_data.get("tool_pattern", "*"),
                tool_names=policy_data.get("tool_names", []),
                resource_pattern=policy_data.get("resource_pattern"),
                resource_paths=policy_data.get("resource_paths", []),
                command_pattern=policy_data.get("command_pattern"),
                actions=policy_data.get("actions", ["read", "write", "execute", "delete"]),
                auto_allow=policy_data.get("auto_allow", False),
                auto_deny=policy_data.get("auto_deny", False),
                priority=policy_data.get("priority", 0),
                enabled=policy_data.get("enabled", True),
            )
            self.engine.add_policy(policy)
            count += 1
        
        # Import mode if present
        if "mode" in data and not merge:
            self.mode = PermissionMode.from_string(data["mode"])
        
        logger.info("Policies imported", path=path, count=count)
        return count
    
    def apply_preset(self, preset: str) -> None:
        """Apply a preset configuration"""
        
        if preset == "strict":
            # Strict mode: ask for everything
            self.mode = PermissionMode.ALWAYS_ASK
            self.engine.clear_policies()
            self.add_policy(
                name="dangerous-deny",
                description="Always deny dangerous commands",
                tool_pattern="bash",
                command_pattern=r"(rm\s+-rf|sudo|dd\s+if=|chmod\s+-R)",
                auto_deny=True,
                priority=100,
            )
        
        elif preset == "development":
            # Development mode: auto-approve safe ops
            self.mode = PermissionMode.AUTO_SAFE
            self.engine.clear_policies()
            self.add_policy(
                name="src-auto-edit",
                description="Auto-approve source code edits",
                tool_pattern="file_edit",
                resource_pattern="**/*.{py,js,ts,go,rs}",
                auto_allow=True,
                priority=20,
            )
            self.add_policy(
                name="dangerous-deny",
                description="Deny dangerous commands",
                tool_pattern="bash",
                command_pattern=r"(rm\s+-rf|sudo|dd\s+if=/)",
                auto_deny=True,
                priority=100,
            )
        
        elif preset == "sandbox":
            # Sandbox mode: full auto
            self.mode = PermissionMode.FULL_AUTO
            self.engine.clear_policies()
        
        logger.info("Preset applied", preset=preset)
    
    def get_policy_summary(self) -> str:
        """Get human-readable policy summary"""
        lines = [
            "**Permission Configuration**",
            "",
            f"Mode: `{self.mode.value}`",
            f"Policies: {len(self.engine.policies)}",
            "",
            "**Statistics:**",
            f"- Allowed: {self._stats['allowed']}",
            f"- Denied: {self._stats['denied']}",
            f"- Asked: {self._stats['asked']}",
            "",
            "**Policies:**",
        ]
        
        for policy in self.engine.policies:
            status = "✓" if policy.enabled else "✗"
            decision = "allow" if policy.auto_allow else ("deny" if policy.auto_deny else "ask")
            lines.append(
                f"- {status} `{policy.name}` ({decision}, priority={policy.priority})"
            )
        
        return "\n".join(lines)
