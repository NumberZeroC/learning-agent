"""Chat box component for displaying conversation"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from textual.widgets import Static, RichLog
from textual.containers import ScrollableContainer
from textual.reactive import reactive
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text


class MessageDisplay(Static):
    """Display a single chat message"""
    
    def __init__(
        self,
        role: str,
        content: str,
        message_id: str | None = None,
        timestamp: datetime | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.role = role
        self.content = content
        self.message_id = message_id
        self.timestamp = timestamp or datetime.now()
    
    def on_mount(self) -> None:
        """Render message on mount"""
        self.update_display()
    
    def update_display(self) -> None:
        """Update the message display"""
        time_str = self.timestamp.strftime("%H:%M")
        
        if self.role == "user":
            # User message style
            self.update(
                Panel(
                    Markdown(self.content),
                    title=f"[bold blue]You[/bold blue] • {time_str}",
                    border_style="blue",
                )
            )
        elif self.role == "assistant":
            # Assistant message style
            self.update(
                Panel(
                    Markdown(self.content),
                    title=f"[bold green]Claude[/bold green] • {time_str}",
                    border_style="green",
                )
            )
        else:
            # System message
            self.update(
                Panel(
                    self.content,
                    title="[bold yellow]System[/bold yellow]",
                    border_style="yellow",
                )
            )


class ChatBox(ScrollableContainer):
    """
    Chat box for displaying conversation history.
    
    Features:
    - Markdown rendering
    - Syntax highlighting
    - Message management
    - Auto-scroll
    """
    
    DEFAULT_CSS = """
    ChatBox {
        height: 1fr;
        background: $surface;
    }
    
    ChatBox MessageDisplay {
        margin: 1 0;
        width: 100%;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._messages: dict[str, MessageDisplay] = {}
        self._message_order: list[str] = []
    
    def add_message(
        self,
        role: str,
        content: str,
        message_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> str:
        """
        Add a message to the chat.
        
        Args:
            role: Message role (user/assistant/system)
            content: Message content (Markdown supported)
            message_id: Optional unique ID for the message
            timestamp: Optional timestamp (defaults to now)
        
        Returns:
            Message ID
        """
        import uuid
        
        if message_id is None:
            message_id = str(uuid.uuid4())[:8]
        
        # Create message display
        msg = MessageDisplay(
            role=role,
            content=content,
            message_id=message_id,
            timestamp=timestamp,
        )
        
        # Store message
        self._messages[message_id] = msg
        self._message_order.append(message_id)
        
        # Add to display
        self.mount(msg)
        
        # Auto-scroll to bottom
        self.scroll_end(animate=False)
        
        return message_id
    
    def remove_message(self, message_id: str) -> bool:
        """
        Remove a message by ID.
        
        Args:
            message_id: ID of message to remove
        
        Returns:
            True if message was found and removed
        """
        if message_id not in self._messages:
            return False
        
        msg = self._messages[message_id]
        msg.remove()
        
        del self._messages[message_id]
        self._message_order.remove(message_id)
        
        return True
    
    def update_message(
        self,
        message_id: str,
        content: str,
    ) -> bool:
        """
        Update a message's content.
        
        Args:
            message_id: ID of message to update
            content: New content
        
        Returns:
            True if message was found and updated
        """
        if message_id not in self._messages:
            return False
        
        msg = self._messages[message_id]
        msg.content = content
        msg.update_display()
        
        return True
    
    def clear(self) -> None:
        """Clear all messages"""
        for msg in self._messages.values():
            msg.remove()
        
        self._messages.clear()
        self._message_order.clear()
    
    def get_messages(self) -> list[dict[str, Any]]:
        """Get all messages as list of dicts"""
        return [
            {
                "id": mid,
                "role": self._messages[mid].role,
                "content": self._messages[mid].content,
                "timestamp": self._messages[mid].timestamp,
            }
            for mid in self._message_order
        ]
    
    def get_message_count(self) -> int:
        """Get number of messages"""
        return len(self._messages)
    
    def scroll_to_bottom(self, animate: bool = True) -> None:
        """Scroll to the bottom of the chat"""
        self.scroll_end(animate=animate)
    
    def add_code_block(
        self,
        code: str,
        language: str = "python",
        title: str | None = None,
    ) -> None:
        """Add a syntax-highlighted code block"""
        from rich.panel import Panel
        from rich.syntax import Syntax
        
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        
        panel = Panel(
            syntax,
            title=title or f"{language} code",
            border_style="dim",
        )
        
        msg_id = self.add_message(
            role="assistant",
            content="",  # Will be replaced
        )
        
        # Custom render for code block
        self.update_message(msg_id, f"```{language}\n{code}\n```")
