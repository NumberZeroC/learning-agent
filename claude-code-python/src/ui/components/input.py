"""Input box component for user input"""

from __future__ import annotations

from textual.widgets import Input, Button
from textual.containers import Horizontal
from textual.binding import Binding
from textual.message import Message


class InputBox(Horizontal):
    """
    Input box with submit button.
    
    Features:
    - Text input field
    - Submit button
    - Keyboard shortcuts (Enter to submit)
    - Command history
    """
    
    DEFAULT_CSS = """
    InputBox {
        height: auto;
        width: 1fr;
        align: center middle;
    }
    
    InputBox Input {
        width: 1fr;
        margin-right: 1;
    }
    
    InputBox Button {
        width: auto;
        min-width: 10;
    }
    """
    
    BINDINGS = [
        Binding("enter", "submit", "Submit", show=False),
        Binding("up", "history_up", "Previous", show=False),
        Binding("down", "history_down", "Next", show=False),
    ]
    
    class Submitted(Message):
        """Emitted when input is submitted"""
        
        def __init__(self, value: str, input: Input) -> None:
            super().__init__()
            self.value = value
            self.input = input
    
    def __init__(
        self,
        placeholder: str = "Type your message...",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.placeholder = placeholder
        self._history: list[str] = []
        self._history_index: int = -1
    
    def compose(self):
        """Compose the input box"""
        yield Input(
            placeholder=self.placeholder,
            id="main-input",
        )
        yield Button("Send", id="submit-btn", variant="primary")
    
    def on_mount(self) -> None:
        """Called when widget is mounted"""
        # Focus input by default
        self.query_one("#main-input", Input).focus()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press"""
        if event.button.id == "submit-btn":
            self._submit()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input"""
        self._submit()
    
    def _submit(self) -> None:
        """Submit the current input"""
        input_widget = self.query_one("#main-input", Input)
        value = input_widget.value.strip()
        
        if value:
            # Add to history
            if not self._history or self._history[-1] != value:
                self._history.append(value)
            self._history_index = len(self._history)
            
            # Emit submitted message
            self.post_message(self.Submitted(value, input_widget))
            
            # Clear input
            input_widget.value = ""
    
    def action_submit(self) -> None:
        """Submit action"""
        self._submit()
    
    def action_history_up(self) -> None:
        """Navigate to previous history item"""
        if self._history and self._history_index > 0:
            self._history_index -= 1
            input_widget = self.query_one("#main-input", Input)
            input_widget.value = self._history[self._history_index]
    
    def action_history_down(self) -> None:
        """Navigate to next history item or clear"""
        if self._history and self._history_index < len(self._history) - 1:
            self._history_index += 1
            input_widget = self.query_one("#main-input", Input)
            input_widget.value = self._history[self._history_index]
        elif self._history_index >= len(self._history) - 1:
            self._history_index = len(self._history)
            input_widget = self.query_one("#main-input", Input)
            input_widget.value = ""
    
    @property
    def value(self) -> str:
        """Get current input value"""
        return self.query_one("#main-input", Input).value
    
    @value.setter
    def value(self, value: str) -> None:
        """Set input value"""
        self.query_one("#main-input", Input).value = value
    
    def focus_input(self) -> None:
        """Focus the input field"""
        self.query_one("#main-input", Input).focus()
    
    def clear_history(self) -> None:
        """Clear input history"""
        self._history.clear()
        self._history_index = -1
