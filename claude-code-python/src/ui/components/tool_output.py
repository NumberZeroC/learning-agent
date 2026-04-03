"""Tool output display component"""

from __future__ import annotations

from textual.widgets import Static, RichLog
from textual.containers import Container
from rich.panel import Panel
from rich.syntax import Syntax


class ToolOutput(Static):
    """
    Display tool execution output.
    
    Features:
    - Syntax highlighting for code
    - Diff display
    - Error highlighting
    - Auto-scroll
    """
    
    DEFAULT_CSS = """
    ToolOutput {
        height: auto;
        max-height: 10;
        border: solid $secondary;
        margin: 0 2;
        padding: 1;
        background: $surface;
    }
    
    ToolOutput .output-content {
        width: 1fr;
        height: auto;
    }
    
    ToolOutput .success {
        color: $success;
    }
    
    ToolOutput .error {
        color: $error;
    }
    
    ToolOutput .warning {
        color: $warning;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._current_output = ""
        self._is_error = False
    
    def show(self, content: str, is_error: bool = False) -> None:
        """
        Show tool output.
        
        Args:
            content: Output content
            is_error: Whether this is an error output
        """
        self._current_output = content
        self._is_error = is_error
        
        if is_error:
            self.update(
                Panel(
                    content,
                    title="❌ Error",
                    border_style="red",
                )
            )
        else:
            self.update(
                Panel(
                    content,
                    title="🔧 Tool Output",
                    border_style="blue",
                )
            )
    
    def update(self, content: str) -> None:
        """Update displayed content"""
        self._current_output = content
        super().update(content)
    
    def show_diff(self, diff: str, filename: str | None = None) -> None:
        """
        Show a diff output with syntax highlighting.
        
        Args:
            diff: Unified diff content
            filename: Optional filename for title
        """
        from rich.panel import Panel
        from rich.syntax import Syntax
        
        # Create syntax highlighted diff
        syntax = Syntax(
            diff,
            "diff",
            theme="monokai",
            line_numbers=False,
        )
        
        title = f"📝 Diff: {filename}" if filename else "📝 Diff"
        
        self.update(
            Panel(
                syntax,
                title=title,
                border_style="cyan",
            )
        )
    
    def show_code(
        self,
        code: str,
        language: str = "python",
        filename: str | None = None,
    ) -> None:
        """
        Show code with syntax highlighting.
        
        Args:
            code: Code content
            language: Programming language
            filename: Optional filename for title
        """
        syntax = Syntax(
            code,
            language,
            theme="monokai",
            line_numbers=True,
        )
        
        title = f"📄 {filename}" if filename else f"💻 {language}"
        
        self.update(
            Panel(
                syntax,
                title=title,
                border_style="green",
            )
        )
    
    def show_success(self, message: str) -> None:
        """Show success message"""
        self.update(
            Panel(
                f"✅ {message}",
                border_style="green",
            )
        )
        self._is_error = False
    
    def show_error(self, message: str) -> None:
        """Show error message"""
        self.update(
            Panel(
                f"❌ {message}",
                border_style="red",
            )
        )
        self._is_error = True
    
    def show_warning(self, message: str) -> None:
        """Show warning message"""
        self.update(
            Panel(
                f"⚠️ {message}",
                border_style="yellow",
            )
        )
    
    def clear(self) -> None:
        """Clear the output"""
        self._current_output = ""
        self._is_error = False
        self.update("")
    
    def hide(self) -> None:
        """Hide the output display"""
        self.add_class("hidden")
    
    def show_widget(self) -> None:
        """Show the output display"""
        self.remove_class("hidden")
    
    @property
    def current_output(self) -> str:
        """Get current output content"""
        return self._current_output
    
    @property
    def is_error(self) -> bool:
        """Check if current output is an error"""
        return self._is_error
