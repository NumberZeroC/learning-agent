"""Plan Mode UI and logic"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from textual.screen import ModalScreen
from textual.widgets import Static, Button, Label
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.binding import Binding
from textual.app import ComposeResult
from textual.reactive import reactive
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


@dataclass
class PlanStep:
    """A step in the execution plan"""
    id: str
    description: str
    status: str = "pending"  # pending, in_progress, completed, skipped
    tool: str | None = None
    result: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def icon(self) -> str:
        """Get status icon"""
        icons = {
            "pending": "⏳",
            "in_progress": "🔄",
            "completed": "✅",
            "skipped": "⏭️",
        }
        return icons.get(self.status, "❓")
    
    @property
    def status_color(self) -> str:
        """Get status color for display"""
        colors = {
            "pending": "dim",
            "in_progress": "blue",
            "completed": "green",
            "skipped": "yellow",
        }
        return colors.get(self.status, "white")


@dataclass
class Plan:
    """Execution plan"""
    id: str
    goal: str
    steps: list[PlanStep] = field(default_factory=list)
    status: str = "draft"  # draft, approved, executing, completed, cancelled
    
    @property
    def progress(self) -> float:
        """Get completion progress (0-1)"""
        if not self.steps:
            return 0.0
        completed = sum(1 for s in self.steps if s.status == "completed")
        return completed / len(self.steps)
    
    @property
    def progress_percent(self) -> int:
        """Get progress as percentage"""
        return int(self.progress * 100)


class PlanDisplay(ScrollableContainer):
    """Display an execution plan"""
    
    DEFAULT_CSS = """
    PlanDisplay {
        height: 1fr;
        background: $surface;
    }
    
    .plan-header {
        text-style: bold;
        padding: 1;
        margin-bottom: 1;
    }
    
    .plan-step {
        margin: 1 0;
        padding: 1;
        background: $surface;
        border: solid $secondary;
    }
    
    .plan-step-completed {
        border: solid green;
    }
    
    .plan-step-in-progress {
        border: solid blue;
    }
    
    .progress-bar {
        height: 1;
        margin: 1 0;
    }
    """
    
    current_plan = reactive(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._plan: Plan | None = None
    
    def set_plan(self, plan: Plan) -> None:
        """Set the plan to display"""
        self._plan = plan
        self.refresh_display()
    
    def refresh_display(self) -> None:
        """Refresh the display"""
        if not self._plan:
            self.update("No plan")
            return
        
        lines = []
        
        # Header
        lines.append(f"[bold]📋 Execution Plan[/bold]")
        lines.append(f"Goal: {self._plan.goal}")
        lines.append(f"Status: {self._plan.status}")
        lines.append(f"Progress: {self._plan.progress_percent}%")
        lines.append("")
        
        # Progress bar
        filled = int(self._plan.progress * 40)
        bar = "█" * filled + "░" * (40 - filled)
        lines.append(f"[green]{bar}[/green]")
        lines.append("")
        
        # Steps
        lines.append("[bold]Steps:[/bold]")
        
        for i, step in enumerate(self._plan.steps, 1):
            icon = step.icon
            status_style = step.status_color
            
            lines.append(f"\n{icon} [bold]Step {i}[/bold]: {step.description}")
            
            if step.tool:
                lines.append(f"   Tool: `{step.tool}`")
            
            if step.result:
                result_preview = step.result[:100] + "..." if len(step.result) > 100 else step.result
                lines.append(f"   Result: {result_preview}")
        
        self.update("\n".join(lines))


class PlanModeDialog(ModalScreen[Plan | None]):
    """
    Dialog for creating and approving execution plans.
    
    Features:
    - Display proposed plan
    - Edit steps
    - Approve/Reject
    - Modify on the fly
    """
    
    DEFAULT_CSS = """
    PlanModeDialog {
        align: center middle;
    }
    
    #plan-dialog {
        width: 100;
        height: 35;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    
    #plan-title {
        text-style: bold;
        color: $primary;
        text-align: center;
        margin-bottom: 1;
    }
    
    #plan-content {
        height: 1fr;
        margin: 1 0;
        padding: 1;
        background: $surface;
        border: solid $secondary;
    }
    
    #plan-buttons {
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    
    #plan-buttons Button {
        margin: 0 1;
        min-width: 15;
    }
    """
    
    BINDINGS = [
        Binding("enter", "approve", "Approve", show=True),
        Binding("escape", "reject", "Reject", show=True),
        Binding("e", "edit", "Edit", show=False),
    ]
    
    def __init__(
        self,
        goal: str,
        steps: list[dict[str, Any]],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.goal = goal
        self.steps_data = steps
        self._plan: Plan | None = None
    
    def compose(self) -> ComposeResult:
        """Compose the dialog"""
        with Container(id="plan-dialog"):
            # Title
            yield Static("📋 Execution Plan", id="plan-title")
            
            # Content
            with ScrollableContainer(id="plan-content"):
                yield self._render_plan()
            
            # Buttons
            with Horizontal(id="plan-buttons"):
                yield Button("✅ Approve", id="approve-btn", variant="success")
                yield Button("✏️ Edit", id="edit-btn")
                yield Button("❌ Reject", id="reject-btn", variant="error")
    
    def _render_plan(self) -> Static:
        """Render plan content"""
        lines = [
            f"[bold]Goal:[/bold] {self.goal}",
            "",
            f"[bold]Proposed Steps:[/bold]",
            "",
        ]
        
        for i, step in enumerate(self.steps_data, 1):
            description = step.get("description", "Unknown step")
            tool = step.get("tool", "")
            
            lines.append(f"⏳ [bold]Step {i}[/bold]: {description}")
            if tool:
                lines.append(f"   Tool: `{tool}`")
            lines.append("")
        
        return Static("\n".join(lines), markup=True)
    
    def on_mount(self) -> None:
        """Called when dialog is mounted"""
        # Create plan object
        self._plan = Plan(
            id="plan-1",
            goal=self.goal,
            steps=[
                PlanStep(
                    id=f"step-{i}",
                    description=step.get("description", ""),
                    tool=step.get("tool"),
                )
                for i, step in enumerate(self.steps_data, 1)
            ],
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press"""
        if event.button.id == "approve-btn":
            self._approve()
        elif event.button.id == "reject-btn":
            self._reject()
        elif event.button.id == "edit-btn":
            self._edit()
    
    def action_approve(self) -> None:
        """Approve action"""
        self._approve()
    
    def action_reject(self) -> None:
        """Reject action"""
        self._reject()
    
    def action_edit(self) -> None:
        """Edit action"""
        self._edit()
    
    def _approve(self) -> None:
        """Handle approval"""
        if self._plan:
            self._plan.status = "approved"
        self.dismiss(self._plan)
    
    def _reject(self) -> None:
        """Handle rejection"""
        self.dismiss(None)
    
    def _edit(self) -> None:
        """Handle edit (placeholder)"""
        self.notify("Edit functionality coming soon")


class PlanPanel(ModalScreen):
    """Panel for viewing plan execution progress"""
    
    DEFAULT_CSS = """
    PlanPanel {
        align: center middle;
    }
    
    #plan-panel {
        width: 100;
        height: 30;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    """
    
    def __init__(self, plan: Plan, **kwargs):
        super().__init__(**kwargs)
        self.plan = plan
    
    def compose(self) -> ComposeResult:
        """Compose the panel"""
        with Container(id="plan-panel"):
            yield Static("📋 Plan Execution", markup=True)
            yield PlanDisplay()
            yield Button("Close", id="close-btn", variant="error")
    
    def on_mount(self) -> None:
        """Initialize display"""
        display = self.query_one(PlanDisplay)
        display.set_plan(self.plan)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press"""
        if event.button.id == "close-btn":
            self.dismiss()
