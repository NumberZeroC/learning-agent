"""Main Textual application for CCP"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header,
    Footer,
    Input,
    Static,
    Button,
    Label,
    LoadingIndicator,
    RichLog,
)
from textual.screen import ModalScreen
from textual.reactive import reactive

logger = structlog.get_logger(__name__)

from .components.chat import ChatBox
from .components.input import InputBox
from .components.tool_output import ToolOutput
from .components.permissions import ApprovalDialog
from .components.permissions_panel import PermissionsPanel, ModeSelectDialog


class StatusBar(Static):
    """Status bar showing current state"""
    
    status = reactive("Ready")
    model = reactive("claude-sonnet-4-20250514")
    tokens = reactive(0)
    mode = reactive("AUTO_SAFE")
    
    def render(self) -> str:
        """Render status bar"""
        time_str = datetime.now().strftime("%H:%M:%S")
        return f"│ 🤖 {self.model} │ 📊 {self.tokens} tokens │ 🔐 {self.mode} │ ⏰ {time_str} │ {self.status}"


class CCPApp(App):
    """
    Claude Code Python Terminal Application
    
    Features:
    - Chat interface with LLM
    - Tool output display
    - Permission approval dialogs
    - Status bar with metrics
    """
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        height: 1fr;
        padding: 0;
    }
    
    #chat-box {
        height: 1fr;
        border: solid $primary;
        margin: 1 2 0 2;
        padding: 1;
        background: $surface;
    }
    
    #tool-output {
        height: auto;
        max-height: 10;
        border: solid $secondary;
        margin: 0 2;
        padding: 1;
        background: $surface;
    }
    
    #input-container {
        height: auto;
        dock: bottom;
        padding: 1 2;
        background: $surface;
    }
    
    #input-box {
        width: 1fr;
    }
    
    #status-bar {
        height: 1;
        dock: bottom;
        background: $primary-background;
        color: $text;
        padding: 0 2;
    }
    
    .hidden {
        display: none;
    }
    
    /* Approval dialog styles */
    ApprovalDialog {
        align: center middle;
    }
    
    #approval-content {
        width: 80;
        height: auto;
        max-height: 20;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
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
    
    /* Syntax highlighting for code */
    .code-block {
        background: $surface;
        border: solid $primary;
        padding: 1;
        margin: 1 0;
    }
    
    /* Tool output colors */
    .tool-success {
        color: $success;
    }
    
    .tool-error {
        color: $error;
    }
    
    .tool-warning {
        color: $warning;
    }
    
    /* Diff colors */
    .diff-add {
        color: $success;
        background: #003300;
    }
    
    .diff-remove {
        color: $error;
        background: #330000;
    }
    
    .diff-header {
        color: $info;
        text-style: bold;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True, priority=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear_chat", "Clear", show=True),
        Binding("ctrl+p", "toggle_permissions", "Permissions", show=True),
        Binding("ctrl+t", "show_tools", "Tools", show=True),
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("f1", "help", "Help", show=True),
    ]
    
    # Application state
    is_processing: reactive[bool] = reactive(False)
    current_tool_request: Any | None = None
    
    def __init__(
        self,
        llm_provider=None,
        tool_registry=None,
        permission_engine=None,
        approval_manager=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        
        # Core components (injected or created)
        self.llm_provider = llm_provider
        self.tool_registry = tool_registry
        self.permission_engine = permission_engine
        self.approval_manager = approval_manager
        
        # State
        self.message_history: list[dict[str, Any]] = []
        self.token_count = 0
        self.permission_mode = "AUTO_SAFE"
    
    def compose(self) -> ComposeResult:
        """Compose the UI layout"""
        yield Header(show_clock=True)
        
        with Container(id="main-container"):
            # Main chat area
            yield ChatBox(id="chat-box")
            
            # Tool output (initially hidden)
            yield ToolOutput(id="tool-output")
        
        # Input area
        with Container(id="input-container"):
            yield InputBox(id="input-box", placeholder="Type your message...")
        
        # Status bar
        yield StatusBar(id="status-bar")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when app is mounted"""
        self.title = "Claude Code Python"
        self.sub_title = "Terminal AI Assistant"
        
        logger.info("CCP App mounted")
        
        # Focus input
        self.query_one("#input-box", InputBox).focus()
        
        # Welcome message
        chat = self.query_one("#chat-box", ChatBox)
        chat.add_message(
            role="assistant",
            content="🤖 **Claude Code Python** initialized.\n\nType your request or use commands:\n- `/help` - Show help\n- `/mode` - Change permission mode\n- `/tools` - List tools\n- `/clear` - Clear chat\n- `Ctrl+Q` - Quit",
        )
    
    def on_input_box_submitted(self, event: InputBox.Submitted) -> None:
        """Handle user input submission"""
        user_input = event.value.strip()
        
        if not user_input:
            return
        
        # Clear input
        event.input.value = ""
        
        # Check for commands
        if user_input.startswith("/"):
            self._handle_command(user_input)
            return
        
        # Add to chat
        chat = self.query_one("#chat-box", ChatBox)
        chat.add_message(role="user", content=user_input)
        
        # Store in history
        self.message_history.append({"role": "user", "content": user_input})
        
        # Process with LLM
        self._process_message(user_input)
    
    def _handle_command(self, command: str) -> None:
        """Handle slash commands"""
        chat = self.query_one("#chat-box", ChatBox)
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd == "/help":
            chat.add_message(
                role="assistant",
                content="""**Commands:**
- `/help` - Show this help
- `/mode [mode]` - Set permission mode (always_ask/auto_edit/auto_safe/full_auto)
- `/tools` - List available tools
- `/clear` - Clear chat history
- `/status` - Show status
- `/quit` - Exit

**Shortcuts:**
- `Ctrl+L` - Clear chat
- `Ctrl+P` - Permission settings
- `Ctrl+T` - Show tools
- `Ctrl+Q` - Quit""",
            )
        
        elif cmd == "/mode":
            if args:
                self.permission_mode = args.upper()
                chat.add_message(
                    role="assistant",
                    content=f"Permission mode set to: **{self.permission_mode}**",
                )
            else:
                chat.add_message(
                    role="assistant",
                    content=f"Current permission mode: **{self.permission_mode}**",
                )
        
        elif cmd == "/tools":
            if self.tool_registry:
                tools = self.tool_registry.list_tools()
                chat.add_message(
                    role="assistant",
                    content=f"**Available Tools:**\n" + "\n".join(f"- `{t}`" for t in tools),
                )
            else:
                chat.add_message(role="assistant", content="Tool registry not initialized.")
        
        elif cmd == "/clear":
            chat.clear()
            self.message_history.clear()
            chat.add_message(
                role="assistant",
                content="Chat cleared.",
            )
        
        elif cmd == "/status":
            status_bar = self.query_one("#status-bar", StatusBar)
            chat.add_message(
                role="assistant",
                content=f"""**Status:**
- Model: {status_bar.model}
- Tokens: {status_bar.tokens}
- Mode: {status_bar.mode}
- Messages: {len(self.message_history)}""",
            )
        
        elif cmd == "/quit":
            self.exit()
        
        else:
            chat.add_message(
                role="assistant",
                content=f"Unknown command: `{cmd}`. Use `/help` for available commands.",
            )
    
    async def _process_message(self, message: str) -> None:
        """Process message with LLM"""
        self.is_processing = True
        chat = self.query_one("#chat-box", ChatBox)
        
        # Show thinking indicator
        chat.add_message(
            role="assistant",
            content="*Thinking...*",
            message_id="thinking",
        )
        
        try:
            if not self.llm_provider:
                raise RuntimeError("LLM provider not initialized")
            
            # Get tools
            tools = None
            if self.tool_registry:
                tools = self.tool_registry.get_definitions()
            
            # Call LLM
            from src.models.messages import Message
            
            messages = [Message(role=m["role"], content=m["content"]) for m in self.message_history]
            
            response = await self.llm_provider.chat(
                messages=messages,
                tools=tools,
            )
            
            # Remove thinking message
            chat.remove_message("thinking")
            
            # Update token count
            self.token_count += response.usage.total_tokens
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.tokens = self.token_count
            
            # Handle response
            if response.text:
                chat.add_message(role="assistant", content=response.text)
                self.message_history.append({"role": "assistant", "content": response.text})
            
            # Handle tool calls
            if response.tool_calls:
                await self._handle_tool_calls(response.tool_calls)
            
        except Exception as e:
            logger.exception("Error processing message")
            chat.remove_message("thinking")
            chat.add_message(
                role="assistant",
                content=f"❌ **Error:** {str(e)}",
                style="tool-error",
            )
        
        finally:
            self.is_processing = False
    
    async def _handle_tool_calls(self, tool_calls: list) -> None:
        """Handle tool calls from LLM"""
        chat = self.query_one("#chat-box", ChatBox)
        tool_output = self.query_one("#tool-output", ToolOutput)
        
        for tool_call in tool_calls:
            logger.info("Tool call requested", tool=tool_call.name)
            
            # Check permissions
            if self.permission_engine:
                perm_result = self.permission_engine.check(
                    tool_name=tool_call.name,
                    tool_input=tool_call.input,
                    command=tool_call.input.get("command"),
                )
                
                if perm_result.requires_approval:
                    # Show approval dialog
                    approved = await self._show_approval_dialog(tool_call, perm_result)
                    if not approved:
                        chat.add_message(
                            role="assistant",
                            content=f"❌ Tool `{tool_call.name}` was denied.",
                        )
                        continue
            
            # Execute tool
            tool_output.show(f"Executing: {tool_call.name}")
            
            if self.tool_registry:
                from src.tools.base import ToolContext
                
                context = ToolContext(
                    session_id="ui-session",
                    working_directory=".",
                )
                
                result = await self.tool_registry.execute_tool(
                    tool_call.name,
                    tool_call.input,
                    context,
                )
                
                tool_output.update(result.to_text())
                
                # Add result to conversation
                from src.models.messages import ToolResultMessage, ContentBlock
                
                self.message_history.append({
                    "role": "user",
                    "content": f"[Tool {tool_call.name} result]: {result.to_text()[:500]}",
                })
    
    async def _show_approval_dialog(self, tool_call, perm_result) -> bool:
        """Show approval dialog and wait for response"""
        dialog = ApprovalDialog(
            tool_name=tool_call.name,
            tool_input=tool_call.input,
            reason=perm_result.reason,
        )
        
        result = await self.push_screen_wait(dialog)
        return result
    
    def action_quit(self) -> None:
        """Quit the application"""
        self.exit()
    
    def action_clear_chat(self) -> None:
        """Clear chat history"""
        self.query_one("#chat-box", ChatBox).clear()
        self.message_history.clear()
    
    def action_toggle_permissions(self) -> None:
        """Toggle permission settings"""
        from src.permissions.manager import PermissionManager
        
        if self.permission_engine:
            # Create manager from engine
            manager = PermissionManager(self.permission_engine)
            self.push_screen(PermissionsPanel(permission_manager=manager))
    
    def action_show_tools(self) -> None:
        """Show tools list"""
        self._handle_command("/tools")
    
    def action_help(self) -> None:
        """Show help"""
        self._handle_command("/help")
    
    def action_cancel(self) -> None:
        """Cancel current operation"""
        if self.is_processing:
            # TODO: Cancel LLM request
            pass
