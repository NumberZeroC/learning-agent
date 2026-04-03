"""Command history management"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class HistoryEntry:
    """A single history entry"""
    
    def __init__(
        self,
        command: str,
        timestamp: datetime | None = None,
        success: bool = True,
        duration_ms: int = 0,
        metadata: dict[str, Any] | None = None,
    ):
        self.command = command
        self.timestamp = timestamp or datetime.now()
        self.success = success
        self.duration_ms = duration_ms
        self.metadata = metadata or {}
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "command": self.command,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HistoryEntry":
        """Create from dictionary"""
        return cls(
            command=data["command"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            success=data.get("success", True),
            duration_ms=data.get("duration_ms", 0),
            metadata=data.get("metadata", {}),
        )
    
    def __str__(self) -> str:
        status = "✓" if self.success else "✗"
        time_str = self.timestamp.strftime("%H:%M:%S")
        return f"[{time_str}] {status} {self.command[:50]}"


class CommandHistory:
    """
    Command history manager.
    
    Features:
    - In-memory history
    - Persistent storage
    - Search functionality
    - Statistics
    """
    
    def __init__(
        self,
        max_entries: int = 1000,
        storage_path: str | Path | None = None,
    ):
        self.max_entries = max_entries
        self.storage_path = Path(storage_path) if storage_path else None
        self._entries: list[HistoryEntry] = []
        self._search_cache: dict[str, list[HistoryEntry]] = {}
    
    @property
    def entries(self) -> list[HistoryEntry]:
        """Get all entries"""
        return self._entries
    
    @property
    def recent(self) -> list[HistoryEntry]:
        """Get recent entries (last 10)"""
        return self._entries[-10:]
    
    @property
    def count(self) -> int:
        """Get entry count"""
        return len(self._entries)
    
    def add(
        self,
        command: str,
        success: bool = True,
        duration_ms: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> HistoryEntry:
        """Add a new entry"""
        
        entry = HistoryEntry(
            command=command,
            success=success,
            duration_ms=duration_ms,
            metadata=metadata,
        )
        
        self._entries.append(entry)
        
        # Trim if needed
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries:]
        
        # Clear search cache
        self._search_cache.clear()
        
        logger.debug("History entry added", command=command[:50])
        
        return entry
    
    def get(self, index: int) -> HistoryEntry | None:
        """Get entry by index"""
        if 0 <= index < len(self._entries):
            return self._entries[index]
        return None
    
    def search(self, query: str, limit: int = 20) -> list[HistoryEntry]:
        """Search history"""
        
        # Check cache
        cache_key = f"{query}:{limit}"
        if cache_key in self._search_cache:
            return self._search_cache[cache_key]
        
        # Search
        query_lower = query.lower()
        results = [
            entry for entry in self._entries
            if query_lower in entry.command.lower()
        ]
        
        # Sort by relevance (newer first)
        results = sorted(results, key=lambda e: e.timestamp, reverse=True)[:limit]
        
        # Cache results
        self._search_cache[cache_key] = results
        
        return results
    
    def get_statistics(self) -> dict[str, Any]:
        """Get history statistics"""
        
        if not self._entries:
            return {
                "total": 0,
                "success_rate": 0,
                "avg_duration_ms": 0,
            }
        
        total = len(self._entries)
        success_count = sum(1 for e in self._entries if e.success)
        total_duration = sum(e.duration_ms for e in self._entries)
        
        return {
            "total": total,
            "success_count": success_count,
            "failed_count": total - success_count,
            "success_rate": success_count / total if total > 0 else 0,
            "avg_duration_ms": total_duration / total if total > 0 else 0,
        }
    
    def save(self, path: str | Path | None = None) -> None:
        """Save history to file"""
        
        save_path = Path(path) if path else self.storage_path
        
        if not save_path:
            logger.warning("No storage path configured")
            return
        
        # Ensure directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "version": "1.0",
            "saved_at": datetime.now().isoformat(),
            "entries": [e.to_dict() for e in self._entries],
        }
        
        with open(save_path, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info("History saved", path=save_path, entries=len(self._entries))
    
    def load(self, path: str | Path | None = None) -> int:
        """Load history from file"""
        
        load_path = Path(path) if path else self.storage_path
        
        if not load_path or not load_path.exists():
            logger.debug("No history file to load")
            return 0
        
        with open(load_path, "r") as f:
            data = json.load(f)
        
        count = 0
        for entry_data in data.get("entries", []):
            try:
                entry = HistoryEntry.from_dict(entry_data)
                self._entries.append(entry)
                count += 1
            except Exception as e:
                logger.warning("Failed to load history entry", error=str(e))
        
        # Trim if needed
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries:]
        
        logger.info("History loaded", path=load_path, entries=count)
        
        return count
    
    def clear(self) -> None:
        """Clear all history"""
        self._entries.clear()
        self._search_cache.clear()
        logger.info("History cleared")
    
    def get_recent_commands(self, limit: int = 10) -> list[str]:
        """Get recent commands as strings"""
        return [e.command for e in self.recent[-limit:]]
    
    def export(self, path: str | Path, format: str = "json") -> None:
        """Export history to file"""
        
        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            data = [e.to_dict() for e in self._entries]
            with open(save_path, "w") as f:
                json.dump(data, f, indent=2)
        
        elif format == "text":
            with open(save_path, "w") as f:
                for entry in self._entries:
                    f.write(f"{entry}\n")
        
        logger.info("History exported", path=save_path, format=format)
    
    def __len__(self) -> int:
        return len(self._entries)
    
    def __iter__(self):
        return iter(self._entries)
    
    def __getitem__(self, index: int) -> HistoryEntry:
        return self._entries[index]
    
    def __repr__(self) -> str:
        return f"CommandHistory(entries={len(self._entries)}, max={self.max_entries})"
