"""Session management for CCP"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from ..models.messages import Message

logger = structlog.get_logger(__name__)


@dataclass
class Session:
    """
    Represents a conversation session.
    
    Attributes:
        id: Unique session identifier
        created_at: Session creation time
        updated_at: Last update time
        messages: Conversation history
        metadata: Additional session data
        working_directory: Working directory for the session
        permission_mode: Permission mode used
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    messages: list[Message] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    working_directory: str = field(default_factory=lambda: ".")
    permission_mode: str = field(default="auto_safe")
    
    @property
    def message_count(self) -> int:
        """Get message count"""
        return len(self.messages)
    
    @property
    def duration(self) -> float:
        """Get session duration in seconds"""
        return (self.updated_at - self.created_at).total_seconds()
    
    def add_message(self, message: Message) -> None:
        """Add a message to the session"""
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def clear_messages(self) -> None:
        """Clear all messages"""
        self.messages.clear()
        self.updated_at = datetime.now()
    
    def get_summary(self) -> str:
        """Get a brief summary of the session"""
        if not self.messages:
            return "Empty session"
        
        first_msg = self.messages[0]
        last_msg = self.messages[-1]
        
        return (
            f"Session {self.id}\n"
            f"Created: {self.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"Messages: {self.message_count}\n"
            f"First: {first_msg.content[:50]}...\n"
            f"Last: {last_msg.content[:50]}..."
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat(),
                }
                for m in self.messages
            ],
            "metadata": self.metadata,
            "working_directory": self.working_directory,
            "permission_mode": self.permission_mode,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        """Create from dictionary"""
        session = cls(
            id=data["id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            working_directory=data.get("working_directory", "."),
            permission_mode=data.get("permission_mode", "auto_safe"),
            metadata=data.get("metadata", {}),
        )
        
        for msg_data in data.get("messages", []):
            session.messages.append(Message(
                role=msg_data["role"],
                content=msg_data["content"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
            ))
        
        return session
    
    def __str__(self) -> str:
        return f"Session({self.id}, {self.message_count} messages)"


class SessionManager:
    """
    Manages multiple sessions.
    
    Features:
    - Create new sessions
    - Switch between sessions
    - Save/load sessions
    - List sessions
    - Delete sessions
    """
    
    def __init__(
        self,
        storage_path: str | Path | None = None,
        max_sessions: int = 100,
    ):
        self.storage_path = Path(storage_path) if storage_path else None
        self.max_sessions = max_sessions
        self._sessions: dict[str, Session] = {}
        self._current_session_id: str | None = None
    
    @property
    def current_session(self) -> Session | None:
        """Get current session"""
        if self._current_session_id:
            return self._sessions.get(self._current_session_id)
        return None
    
    @property
    def sessions(self) -> list[Session]:
        """Get all sessions"""
        return list(self._sessions.values())
    
    @property
    def session_count(self) -> int:
        """Get session count"""
        return len(self._sessions)
    
    def create_session(
        self,
        working_directory: str | None = None,
        permission_mode: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Session:
        """Create a new session"""
        
        session = Session(
            working_directory=working_directory or ".",
            permission_mode=permission_mode or "auto_safe",
            metadata=metadata or {},
        )
        
        self._sessions[session.id] = session
        self._current_session_id = session.id
        
        # Trim old sessions if needed
        if len(self._sessions) > self.max_sessions:
            self._trim_old_sessions()
        
        logger.info("Session created", id=session.id)
        
        return session
    
    def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID"""
        return self._sessions.get(session_id)
    
    def switch_session(self, session_id: str) -> bool:
        """Switch to a different session"""
        
        if session_id not in self._sessions:
            logger.warning("Session not found", id=session_id)
            return False
        
        self._current_session_id = session_id
        logger.info("Session switched", id=session_id)
        
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        
        if session_id not in self._sessions:
            return False
        
        # Don't delete current session
        if self._current_session_id == session_id:
            self._current_session_id = None
        
        del self._sessions[session_id]
        logger.info("Session deleted", id=session_id)
        
        return True
    
    def list_sessions(self) -> list[dict[str, Any]]:
        """List all sessions with summary"""
        
        sessions = sorted(
            self._sessions.values(),
            key=lambda s: s.updated_at,
            reverse=True,
        )
        
        return [
            {
                "id": s.id,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
                "message_count": s.message_count,
                "working_directory": s.working_directory,
                "permission_mode": s.permission_mode,
                "is_current": s.id == self._current_session_id,
            }
            for s in sessions
        ]
    
    def save_session(self, session_id: str | None = None) -> bool:
        """Save a session to disk"""
        
        if not self.storage_path:
            logger.warning("No storage path configured")
            return False
        
        session_id = session_id or self._current_session_id
        
        if not session_id or session_id not in self._sessions:
            logger.warning("Session not found", id=session_id)
            return False
        
        session = self._sessions[session_id]
        
        # Ensure directory exists
        save_dir = self.storage_path / "sessions"
        save_dir.mkdir(parents=True, exist_ok=True)
        
        save_path = save_dir / f"{session_id}.json"
        
        with open(save_path, "w") as f:
            json.dump(session.to_dict(), f, indent=2)
        
        logger.info("Session saved", id=session_id, path=save_path)
        
        return True
    
    def load_session(self, session_id: str) -> Session | None:
        """Load a session from disk"""
        
        if not self.storage_path:
            return None
        
        load_path = self.storage_path / "sessions" / f"{session_id}.json"
        
        if not load_path.exists():
            logger.warning("Session file not found", path=load_path)
            return None
        
        with open(load_path, "r") as f:
            data = json.load(f)
        
        session = Session.from_dict(data)
        self._sessions[session.id] = session
        
        logger.info("Session loaded", id=session_id)
        
        return session
    
    def save_all(self) -> int:
        """Save all sessions"""
        
        count = 0
        for session_id in self._sessions:
            if self.save_session(session_id):
                count += 1
        
        logger.info("All sessions saved", count=count)
        
        return count
    
    def load_all(self) -> int:
        """Load all sessions from disk"""
        
        if not self.storage_path:
            return 0
        
        sessions_dir = self.storage_path / "sessions"
        
        if not sessions_dir.exists():
            return 0
        
        count = 0
        for session_file in sessions_dir.glob("*.json"):
            session_id = session_file.stem
            
            with open(session_file, "r") as f:
                data = json.load(f)
            
            session = Session.from_dict(data)
            self._sessions[session.id] = session
            count += 1
        
        logger.info("Sessions loaded", count=count)
        
        return count
    
    def export_session(
        self,
        session_id: str | None = None,
        path: str | Path | None = None,
        format: str = "json",
    ) -> bool:
        """Export a session to file"""
        
        session_id = session_id or self._current_session_id
        
        if not session_id or session_id not in self._sessions:
            return False
        
        session = self._sessions[session_id]
        
        if not path:
            path = f"session_{session_id}.{format}"
        
        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            with open(save_path, "w") as f:
                json.dump(session.to_dict(), f, indent=2)
        
        elif format == "text":
            with open(save_path, "w") as f:
                for msg in session.messages:
                    role = msg.role.upper()
                    time = msg.timestamp.strftime("%H:%M:%S")
                    f.write(f"[{time}] {role}: {msg.content}\n\n")
        
        elif format == "markdown":
            with open(save_path, "w") as f:
                f.write(f"# Session {session.id}\n\n")
                f.write(f"**Created:** {session.created_at}\n")
                f.write(f"**Messages:** {session.message_count}\n\n")
                f.write("---\n\n")
                
                for msg in session.messages:
                    role = "👤 User" if msg.role == "user" else "🤖 Assistant"
                    time = msg.timestamp.strftime("%H:%M:%S")
                    f.write(f"### {role} • {time}\n\n")
                    f.write(f"{msg.content}\n\n")
                    f.write("---\n\n")
        
        logger.info("Session exported", id=session_id, path=save_path, format=format)
        
        return True
    
    def _trim_old_sessions(self) -> None:
        """Remove oldest sessions"""
        
        sessions = sorted(
            self._sessions.values(),
            key=lambda s: s.updated_at,
        )
        
        # Keep the most recent sessions
        to_remove = sessions[:len(sessions) - self.max_sessions + 1]
        
        for session in to_remove:
            del self._sessions[session.id]
            logger.info("Session trimmed", id=session.id)
    
    def get_statistics(self) -> dict[str, Any]:
        """Get session statistics"""
        
        if not self._sessions:
            return {
                "total_sessions": 0,
                "total_messages": 0,
                "avg_messages_per_session": 0,
            }
        
        total_messages = sum(s.message_count for s in self._sessions.values())
        
        return {
            "total_sessions": len(self._sessions),
            "total_messages": total_messages,
            "avg_messages_per_session": total_messages / len(self._sessions),
            "current_session": self._current_session_id,
        }
    
    def clear_all(self) -> int:
        """Clear all sessions"""
        
        count = len(self._sessions)
        self._sessions.clear()
        self._current_session_id = None
        
        logger.info("All sessions cleared", count=count)
        
        return count
    
    def __len__(self) -> int:
        return len(self._sessions)
    
    def __repr__(self) -> str:
        return f"SessionManager(sessions={len(self._sessions)}, current={self._current_session_id})"
