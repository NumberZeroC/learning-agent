"""Permission approval dialog"""

from __future__ import annotations

from typing import Any

from textual.screen import ModalScreen
from textual.widgets import (
    Static,
    Button,
    Label,
    Input,
)
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding
from rich.panel import Panel
from rich.markdown import Markdown


class ApprovalDialog(ModalScreen[bool]):
    """
    Modal dialog for requesting user approval.
    
    Features:
    - Display tool information
    - Show command/details
    - Approve/Deny buttons
    - Optional user note
    - Keyboard shortcuts
    """
    
    DEFAULT_CSS = """
    ApprovalDialog {
        align: center middle;
    }
    
    #approval-dialog {
        width: 90;
        height: auto;
        max-height: 25;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    
    #approval-title {
        text-style: bold;
        color: $primary;
        text-align: center;
        margin-bottom: 1;
    }
    
    #approval-content {
        height: auto;
        max-height: 12;
        margin: 1 0;
        padding: 1;
        background: $surface;
        border: solid $secondary;
    }
    
    #approval-reason {
        color: $warning;
        margin: 1 0;
    }
    
    #approval-buttons {
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    
    #approval-buttons Button {
        margin: 0 1;
        min-width: 15;
    }
    
    #approval-buttons Button#approve-btn {
        background: $success;
    }
    
    #approval-buttons Button#deny-btn {
        background: $error;
    }
    
    #approval-note {
        height: 3;
        margin: 1 0;
    }
    """
    
    BINDINGS = [
        Binding("enter", "approve", "Approve", show=True),
        Binding("escape", "deny", "Deny", show=True),
        Binding("a", "approve", "Approve", show=False),
        Binding("d", "deny", "Deny", show=False),
    ]
    
    def __init__(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        reason: str = "",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.tool_name = tool_name
        self.tool_input = tool_input
        self.reason = reason
        self._user_note = ""
    
    def compose(self):
        """Compose the dialog"""
        with Container(id="approval-dialog"):
            # Title
            yield Static("🔐 Permission Required", id="approval-title")
            
            # Content
            content = self._build_content()
            yield Static(content, id="approval-content", markup=True)
            
            # Reason
            if self.reason:
                yield Static(f"⚠️ {self.reason}", id="approval-reason")
            
            # Optional note input
            yield Input(
                placeholder="Add a note (optional)...",
                id="approval-note",
            )
            
            # Buttons
            with Horizontal(id="approval-buttons"):
                yield Button("✅ Approve", id="approve-btn", variant="success")
                yield Button("❌ Deny", id="deny-btn", variant="error")
    
    def _build_content(self) -> str:
        """Build the content display"""
        lines = [
            f"**Tool:** `{self.tool_name}`",
            "",
            "**Details:**",
            "```",
        ]
        
        # Format tool input
        for key, value in self.tool_input.items():
            if key == "command":
                lines.append(f"Command: {value}")
            elif key == "file_path":
                lines.append(f"File: {value}")
            elif key == "description":
                lines.append(f"Reason: {value}")
            else:
                lines.append(f"{key}: {value}")
        
        lines.append("```")
        
        return "\n".join(lines)
    
    def on_mount(self) -> None:
        """Called when dialog is mounted"""
        # Focus note input
        try:
            self.query_one("#approval-note", Input).focus()
        except Exception:
            pass
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press"""
        if event.button.id == "approve-btn":
            self._approve()
        elif event.button.id == "deny-btn":
            self._deny()
    
    def action_approve(self) -> None:
        """Approve action"""
        self._approve()
    
    def action_deny(self) -> None:
        """Deny action"""
        self._deny()
    
    def _approve(self) -> None:
        """Handle approval"""
        # Get user note
        try:
            note_input = self.query_one("#approval-note", Input)
            self._user_note = note_input.value
        except Exception:
            self._user_note = ""
        
        self.dismiss(True)
    
    def _deny(self) -> None:
        """Handle denial"""
        # Get user note
        try:
            note_input = self.query_one("#approval-note", Input)
            self._user_note = note_input.value
        except Exception:
            self._user_note = ""
        
        self.dismiss(False)
    
    @property
    def user_note(self) -> str:
        """Get the user's note"""
        return self._user_note
