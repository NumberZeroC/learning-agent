"""MCP Registry for managing MCP server configurations"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class MCPRegistry:
    """
    Registry for MCP server configurations.
    
    Features:
    - Server configuration storage
    - Load/Save configurations
    - Server discovery
    """
    
    DEFAULT_CONFIG_PATH = Path.home() / ".ccp" / "mcp_servers.json"
    
    def __init__(self, config_path: str | Path | None = None):
        self.config_path = Path(config_path) if config_path else self.DEFAULT_CONFIG_PATH
        self._servers: dict[str, dict[str, Any]] = {}
    
    @property
    def servers(self) -> list[str]:
        """List registered server names"""
        return list(self._servers.keys())
    
    def register(
        self,
        name: str,
        transport: str = "stdio",
        config: dict[str, Any] | None = None,
    ) -> None:
        """
        Register an MCP server.
        
        Args:
            name: Server name
            transport: Transport type (stdio/sse)
            config: Server configuration
        """
        self._servers[name] = {
            "transport": transport,
            "config": config or {},
        }
        logger.info("MCP server registered", name=name)
    
    def unregister(self, name: str) -> bool:
        """Unregister a server"""
        if name in self._servers:
            del self._servers[name]
            logger.info("MCP server unregistered", name=name)
            return True
        return False
    
    def get_config(self, name: str) -> dict[str, Any] | None:
        """Get server configuration"""
        return self._servers.get(name)
    
    def load(self, path: str | Path | None = None) -> int:
        """Load configurations from file"""
        
        load_path = Path(path) if path else self.config_path
        
        if not load_path.exists():
            logger.debug("No MCP config file found")
            return 0
        
        with open(load_path, "r") as f:
            data = json.load(f)
        
        count = 0
        for name, config in data.get("servers", {}).items():
            self._servers[name] = config
            count += 1
        
        logger.info("MCP configurations loaded", count=count)
        return count
    
    def save(self, path: str | Path | None = None) -> None:
        """Save configurations to file"""
        
        save_path = Path(path) if path else self.config_path
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "version": "1.0",
            "servers": self._servers,
        }
        
        with open(save_path, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info("MCP configurations saved", path=save_path)
    
    def clear(self) -> None:
        """Clear all registrations"""
        self._servers.clear()
        logger.info("MCP registry cleared")
    
    def __len__(self) -> int:
        return len(self._servers)
    
    def __repr__(self) -> str:
        return f"MCPRegistry(servers={len(self._servers)})"
