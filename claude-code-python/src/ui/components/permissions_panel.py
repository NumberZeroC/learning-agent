"""Permission management panel UI"""

from __future__ import annotations

from textual.screen import ModalScreen
from textual.widgets import (
    Static,
    Button,
    Label,
    Select,
    Input,
)
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.binding import Binding
from textual.app import ComposeResult
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class PermissionsPanel(ModalScreen):
    """
    Panel for managing permissions and policies.
    
    Features:
    - View current mode
    - List all policies
    - Add/remove policies
    - Import/Export
    - Apply presets
    """
    
    DEFAULT_CSS = """
    PermissionsPanel {
        align: center middle;
    }
    
    #permissions-dialog {
        width: 100;
        height: 30;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    
    #permissions-title {
        text-style: bold;
        color: $primary;
        text-align: center;
        margin-bottom: 1;
    }
    
    #permissions-content {
        height: 1fr;
        margin: 1 0;
        padding: 1;
        background: $surface;
        border: solid $secondary;
    }
    
    #permissions-buttons {
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    
    #permissions-buttons Button {
        margin: 0 1;
        min-width: 12;
    }
    
    .policy-item {
        margin: 1 0;
        padding: 1;
        background: $surface;
        border: solid $secondary;
    }
    
    .mode-display {
        text-style: bold;
        color: $success;
    }
    """
    
    BINDINGS = [
        Binding("escape", "close", "Close", show=True),
        Binding("q", "close", "Close", show=False),
    ]
    
    def __init__(
        self,
        permission_manager=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.permission_manager = permission_manager
    
    def compose(self) -> ComposeResult:
        """Compose the panel"""
        with Container(id="permissions-dialog"):
            # Title
            yield Static("🔐 Permission Management", id="permissions-title")
            
            # Content (scrollable)
            with ScrollableContainer(id="permissions-content"):
                # Current mode
                yield self._render_mode_section()
                
                # Statistics
                yield self._render_stats_section()
                
                # Policies list
                yield self._render_policies_section()
                
                # Presets
                yield self._render_presets_section()
            
            # Buttons
            with Horizontal(id="permissions-buttons"):
                yield Button("💾 Export", id="export-btn", variant="primary")
                yield Button("📂 Import", id="import-btn")
                yield Button("❌ Close", id="close-btn", variant="error")
    
    def _render_mode_section(self) -> Static:
        """Render mode selection section"""
        mode = self.permission_manager.mode.value if self.permission_manager else "AUTO_SAFE"
        
        content = f"""[bold]Current Mode:[/bold] [{mode}]

[dim]Modes:[/dim]
• [green]always_ask[/green] - Ask for every operation
• [blue]auto_edit[/blue] - Auto-approve file edits
• [cyan]auto_safe[/cyan] - Auto-approve safe operations (recommended)
• [yellow]full_auto[/yellow] - Auto-approve everything
"""
        
        return Static(content, markup=True)
    
    def _render_stats_section(self) -> Static:
        """Render statistics section"""
        if not self.permission_manager:
            return Static("No statistics available")
        
        stats = self.permission_manager.get_stats()
        
        content = f"""
[bold]Statistics:[/bold]
├─ Allowed: {stats.get('allowed', 0)}
├─ Denied: {stats.get('denied', 0)}
├─ Asked: {stats.get('asked', 0)}
└─ Policies: {stats.get('policies', 0)}
"""
        
        return Static(content, markup=True)
    
    def _render_policies_section(self) -> Static:
        """Render policies list section"""
        if not self.permission_manager:
            return Static("No policies available")
        
        policies = self.permission_manager.list_policies()
        
        if not policies:
            return Static("No policies configured")
        
        lines = ["[bold]Active Policies:[/bold]", ""]
        
        for p in policies:
            status = "✓" if p["enabled"] else "✗"
            decision = p["decision"]
            priority = p["priority"]
            
            lines.append(f"{status} [bold]{p['name']}[/bold]")
            lines.append(f"  Decision: {decision} | Priority: {priority}")
            
            if p.get("description"):
                lines.append(f"  {p['description']}")
            
            tool = p.get("tool_pattern", "*")
            if p.get("resource_pattern"):
                tool += f" on {p['resource_pattern']}"
            lines.append(f"  Pattern: {tool}")
            lines.append("")
        
        return Static("\n".join(lines), markup=True)
    
    def _render_presets_section(self) -> Static:
        """Render presets section"""
        content = """
[bold]Quick Presets:[/bold]
• [green]strict[/green] - Maximum security, ask for everything
• [blue]development[/blue] - Balanced for coding (recommended)
• [yellow]sandbox[/yellow] - Full auto (sandboxed environments only)
"""
        return Static(content, markup=True)
    
    def on_mount(self) -> None:
        """Called when panel is mounted"""
        self.refresh_display()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press"""
        if event.button.id == "close-btn":
            self.dismiss()
        elif event.button.id == "export-btn":
            self._export_policies()
        elif event.button.id == "import-btn":
            self._import_policies()
    
    def action_close(self) -> None:
        """Close action"""
        self.dismiss()
    
    def refresh_display(self) -> None:
        """Refresh the display"""
        # Could be used to update dynamic content
        pass
    
    def _export_policies(self) -> None:
        """Handle export"""
        if not self.permission_manager:
            return
        
        # TODO: Show file dialog
        from pathlib import Path
        default_path = Path.home() / ".ccp" / "policies.json"
        default_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.permission_manager.export_policies(default_path)
        
        # Show success message
        self.notify(f"Policies exported to {default_path}")
    
    def _import_policies(self) -> None:
        """Handle import"""
        if not self.permission_manager:
            return
        
        # TODO: Show file dialog
        from pathlib import Path
        default_path = Path.home() / ".ccp" / "policies.json"
        
        if default_path.exists():
            count = self.permission_manager.import_policies(default_path, merge=True)
            self.notify(f"Imported {count} policies")
            self.refresh_display()
        else:
            self.notify("No policies file found", severity="warning")


class ModeSelectDialog(ModalScreen[str]):
    """Dialog for selecting permission mode"""
    
    DEFAULT_CSS = """
    ModeSelectDialog {
        align: center middle;
    }
    
    #mode-dialog {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    
    #mode-dialog Button {
        margin: 1 0;
        width: 100%;
    }
    """
    
    MODES = [
        ("always_ask", "Always Ask", "Ask for every operation"),
        ("auto_edit", "Auto Edit", "Auto-approve file edits"),
        ("auto_safe", "Auto Safe", "Auto-approve safe operations"),
        ("full_auto", "Full Auto", "Auto-approve everything"),
    ]
    
    def compose(self) -> ComposeResult:
        """Compose the dialog"""
        with Container(id="mode-dialog"):
            yield Static("🔐 Select Permission Mode", markup=True)
            yield Static("")  # Spacer
            
            for mode_id, name, desc in self.MODES:
                btn = Button(
                    f"[bold]{name}[/bold]\n[dim]{desc}[/dim]",
                    id=f"mode-{mode_id}",
                    variant="default",
                )
                btn.data_mode = mode_id  # type: ignore
                yield btn
            
            yield Button("Cancel", id="cancel-btn", variant="error")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press"""
        if event.button.id == "cancel-btn":
            self.dismiss(None)
        elif event.button.id and event.button.id.startswith("mode-"):
            mode = event.button.id.replace("mode-", "")
            self.dismiss(mode)
