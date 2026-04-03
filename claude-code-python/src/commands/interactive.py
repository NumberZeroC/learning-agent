"""Interactive command mode"""

from __future__ import annotations

import asyncio
from typing import Any

import structlog

from .base import Command, CommandContext, CommandResult
from ..models.messages import Message

logger = structlog.get_logger(__name__)


class InteractiveCommand(Command):
    """
    Interactive command mode for real-time conversation.
    
    Features:
    - Continuous conversation loop
    - Message history
    - Tool integration
    - Permission handling
    - Graceful exit
    """
    
    name = "interactive"
    aliases = ["i", "chat", "repl"]
    description = "Run in interactive mode with real-time conversation"
    
    def __init__(
        self,
        llm_provider=None,
        tool_registry=None,
        permission_engine=None,
        approval_manager=None,
    ):
        self.llm_provider = llm_provider
        self.tool_registry = tool_registry
        self.permission_engine = permission_engine
        self.approval_manager = approval_manager
        self._running = False
    
    async def execute(self, args: list[str], context: CommandContext) -> CommandResult:
        """Execute interactive mode"""
        
        self._running = True
        
        logger.info("Interactive mode started")
        
        # Welcome message
        await context.output.display(
            "🤖 **Claude Code Python** - Interactive Mode\n\n"
            "Type your message or use commands:\n"
            "- `/help` - Show help\n"
            "- `/mode` - Change permission mode\n"
            "- `/tools` - List tools\n"
            "- `/clear` - Clear history\n"
            "- `/quit` - Exit\n"
            "- `Ctrl+C/D` - Quit\n"
        )
        
        # Message history
        history: list[Message] = []
        
        try:
            while self._running:
                # Get user input
                user_input = await context.input.get()
                
                if not user_input:
                    continue
                
                user_input = user_input.strip()
                
                # Handle commands
                if user_input.startswith("/"):
                    result = await self._handle_command(
                        user_input,
                        context,
                        history,
                    )
                    if result == "exit":
                        break
                    continue
                
                # Add to history
                history.append(Message(role="user", content=user_input))
                
                # Process with LLM
                await self._process_message(user_input, history, context)
        
        except KeyboardInterrupt:
            logger.info("Interactive mode interrupted")
            await context.output.display("\n👋 Goodbye!")
        
        return CommandResult(success=True, message="Interactive mode ended")
    
    async def _handle_command(
        self,
        command: str,
        context: CommandContext,
        history: list[Message],
    ) -> str | None:
        """Handle slash command"""
        
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd in ("/quit", "/exit", "/q"):
            await context.output.display("👋 Goodbye!")
            self._running = False
            return "exit"
        
        elif cmd == "/help":
            help_text = """
**Commands:**
- `/help` - Show this help
- `/mode [mode]` - Set permission mode
- `/tools` - List available tools
- `/clear` - Clear chat history
- `/history` - Show message history
- `/status` - Show status
- `/quit` - Exit

**Shortcuts:**
- `Ctrl+C` - Interrupt current operation
- `Ctrl+D` - Exit
"""
            await context.output.display(help_text)
        
        elif cmd == "/mode":
            if args:
                from src.permissions.policies import PermissionMode
                try:
                    mode = PermissionMode.from_string(args)
                    if self.permission_engine:
                        self.permission_engine._default_mode = mode
                    await context.output.display(f"✅ Mode set to: **{mode.value}**")
                except ValueError:
                    await context.output.display(
                        f"❌ Invalid mode. Valid modes: always_ask, auto_edit, auto_safe, full_auto"
                    )
            else:
                if self.permission_engine:
                    mode = self.permission_engine._default_mode
                    await context.output.display(f"Current mode: **{mode.value}**")
        
        elif cmd == "/tools":
            if self.tool_registry:
                tools = self.tool_registry.list_tools()
                tool_list = "\n".join(f"- `{t}`" for t in tools)
                await context.output.display(f"**Available Tools:**\n{tool_list}")
            else:
                await context.output.display("Tool registry not initialized.")
        
        elif cmd == "/clear":
            history.clear()
            await context.output.display("✅ Chat history cleared.")
        
        elif cmd == "/history":
            if not history:
                await context.output.display("No history.")
            else:
                lines = [f"**History ({len(history)} messages):**"]
                for i, msg in enumerate(history[-10:], 1):  # Last 10 messages
                    preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
                    lines.append(f"{i}. [{msg.role}] {preview}")
                await context.output.display("\n".join(lines))
        
        elif cmd == "/status":
            stats = await self._get_status()
            await context.output.display(stats)
        
        else:
            await context.output.display(f"❌ Unknown command: `{cmd}`. Use `/help` for available commands.")
        
        return None
    
    async def _process_message(
        self,
        message: str,
        history: list[Message],
        context: CommandContext,
    ) -> None:
        """Process message with LLM"""
        
        if not self.llm_provider:
            await context.output.display("❌ LLM provider not initialized.")
            return
        
        try:
            # Show thinking indicator
            await context.output.display("🤔 *Thinking...*", clear_line=True)
            
            # Get tools
            tools = None
            if self.tool_registry:
                tools = self.tool_registry.get_definitions()
            
            # Call LLM
            response = await self.llm_provider.chat(
                messages=history,
                tools=tools,
            )
            
            # Clear thinking indicator
            await context.output.clear_last_line()
            
            # Display response
            if response.text:
                await context.output.display(response.text)
                history.append(Message(role="assistant", content=response.text))
            
            # Handle tool calls
            if response.tool_calls:
                await self._handle_tool_calls(response.tool_calls, history, context)
        
        except Exception as e:
            logger.exception("Error processing message")
            await context.output.display(f"❌ **Error:** {str(e)}")
    
    async def _handle_tool_calls(
        self,
        tool_calls: list,
        history: list[Message],
        context: CommandContext,
    ) -> None:
        """Handle tool calls from LLM"""
        
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
                    # Handle approval
                    if self.approval_manager:
                        request = self.approval_manager.create_request(
                            tool_name=tool_call.name,
                            tool_input=tool_call.input,
                            reason=perm_result.reason,
                        )
                        
                        await context.output.display(
                            f"🔐 **Approval Required:** {perm_result.reason}\n"
                            f"Tool: `{tool_call.name}`"
                        )
                        
                        # Wait for approval
                        result = await self.approval_manager.wait_for_approval(request.id)
                        
                        if result.status.value != "approved":
                            await context.output.display(
                                f"❌ Tool `{tool_call.name}` was denied."
                            )
                            continue
            
            # Execute tool
            await context.output.display(f"🔧 Executing: `{tool_call.name}`...")
            
            if self.tool_registry:
                from src.tools.base import ToolContext
                
                tool_context = ToolContext(
                    session_id="interactive",
                    working_directory=".",
                )
                
                result = await self.tool_registry.execute_tool(
                    tool_call.name,
                    tool_call.input,
                    tool_context,
                )
                
                # Display result
                output = result.to_text()
                if len(output) > 500:
                    output = output[:500] + "... (truncated)"
                await context.output.display(f"```\n{output}\n```")
                
                # Add to history
                history.append(Message(
                    role="user",
                    content=f"[Tool {tool_call.name} result]: {output[:200]}",
                ))
    
    async def _get_status(self) -> str:
        """Get status information"""
        
        stats = {
            "LLM": "Not initialized",
            "Tools": 0,
            "Permission Mode": "Unknown",
        }
        
        if self.llm_provider:
            stats["LLM"] = self.llm_provider.model
        
        if self.tool_registry:
            stats["Tools"] = len(self.tool_registry)
        
        if self.permission_engine:
            stats["Permission Mode"] = self.permission_engine._default_mode.value
        
        lines = ["**Status:**"]
        for key, value in stats.items():
            lines.append(f"- {key}: {value}")
        
        return "\n".join(lines)
    
    def stop(self) -> None:
        """Stop interactive mode"""
        self._running = False
