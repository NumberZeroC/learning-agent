"""Batch command mode for non-interactive execution"""

from __future__ import annotations

import asyncio
from typing import Any

import structlog

from .base import Command, CommandContext, CommandResult
from ..models.messages import Message

logger = structlog.get_logger(__name__)


class BatchCommand(Command):
    """
    Batch command mode for non-interactive task execution.
    
    Features:
    - Single task execution
    - No conversation history
    - Optimized for scripts
    - Return output for piping
    """
    
    name = "batch"
    aliases = ["run", "exec", "b"]
    description = "Execute a single task in batch mode"
    
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
    
    async def execute(self, args: list[str], context: CommandContext) -> CommandResult:
        """Execute batch mode"""
        
        if not args:
            return CommandResult(
                success=False,
                message="Error: No task specified. Usage: ccp run <task>"
            )
        
        task = " ".join(args)
        
        logger.info("Batch mode started", task=task)
        
        if not self.llm_provider:
            return CommandResult(
                success=False,
                message="Error: LLM provider not initialized"
            )
        
        try:
            # Get tools
            tools = None
            if self.tool_registry:
                tools = self.tool_registry.get_definitions()
            
            # Create message history
            history: list[Message] = [
                Message(
                    role="system",
                    content="You are a helpful coding assistant. Be concise and direct. Focus on completing the task efficiently.",
                ),
                Message(role="user", content=task),
            ]
            
            # Call LLM
            response = await self.llm_provider.chat(
                messages=history,
                tools=tools,
            )
            
            # Display response
            if response.text:
                await context.output.display(response.text)
            
            # Handle tool calls
            if response.tool_calls:
                await self._handle_tool_calls(response.tool_calls, context)
            
            return CommandResult(
                success=True,
                message="Task completed",
                data={
                    "response": response.text,
                    "tool_calls": len(response.tool_calls),
                    "tokens": response.usage.total_tokens,
                }
            )
        
        except Exception as e:
            logger.exception("Batch execution error")
            return CommandResult(
                success=False,
                message=f"Error: {str(e)}"
            )
    
    async def _handle_tool_calls(
        self,
        tool_calls: list,
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
                    # In batch mode, we can't wait for user approval
                    # So we skip or auto-deny based on configuration
                    await context.output.display(
                        f"⚠️ Skipped `{tool_call.name}`: requires approval"
                    )
                    continue
            
            # Execute tool
            await context.output.display(f"🔧 Executing: `{tool_call.name}`...")
            
            if self.tool_registry:
                from src.tools.base import ToolContext
                
                tool_context = ToolContext(
                    session_id="batch",
                    working_directory=".",
                )
                
                result = await self.tool_registry.execute_tool(
                    tool_call.name,
                    tool_call.input,
                    tool_context,
                )
                
                # Display result
                output = result.to_text()
                await context.output.display(output)


class ScriptCommand(Command):
    """
    Execute a script of multiple commands.
    
    Features:
    - Read commands from file
    - Execute sequentially
    - Stop on error (optional)
    """
    
    name = "script"
    aliases = ["batch-file", "s"]
    description = "Execute commands from a script file"
    
    def __init__(
        self,
        llm_provider=None,
        tool_registry=None,
        permission_engine=None,
    ):
        self.llm_provider = llm_provider
        self.tool_registry = tool_registry
        self.permission_engine = permission_engine
    
    async def execute(self, args: list[str], context: CommandContext) -> CommandResult:
        """Execute script mode"""
        
        if not args:
            return CommandResult(
                success=False,
                message="Error: No script file specified. Usage: ccp script <file>"
            )
        
        script_file = args[0]
        stop_on_error = "--stop" in args or "-e" in args
        
        logger.info("Script mode started", file=script_file)
        
        try:
            # Read script file
            with open(script_file, "r") as f:
                lines = f.readlines()
            
            # Filter comments and empty lines
            commands = [
                line.strip()
                for line in lines
                if line.strip() and not line.strip().startswith("#")
            ]
            
            if not commands:
                return CommandResult(
                    success=False,
                    message="Error: No commands found in script"
                )
            
            await context.output.display(f"📜 Executing {len(commands)} commands from {script_file}\n")
            
            # Execute commands
            results = []
            for i, command in enumerate(commands, 1):
                await context.output.display(f"[{i}/{len(commands)}] {command}")
                
                result = await self._execute_command(command, context)
                results.append(result)
                
                if not result.success and stop_on_error:
                    await context.output.display(f"\n❌ Stopped at command {i}: {command}")
                    break
                
                await context.output.display("")  # Empty line
            
            success_count = sum(1 for r in results if r.success)
            await context.output.display(
                f"\n✅ Completed: {success_count}/{len(commands)} commands"
            )
            
            return CommandResult(
                success=True,
                message=f"Executed {success_count}/{len(commands)} commands"
            )
        
        except FileNotFoundError:
            return CommandResult(
                success=False,
                message=f"Error: Script file not found: {script_file}"
            )
        except Exception as e:
            logger.exception("Script execution error")
            return CommandResult(
                success=False,
                message=f"Error: {str(e)}"
            )
    
    async def _execute_command(
        self,
        command: str,
        context: CommandContext,
    ) -> CommandResult:
        """Execute a single command"""
        
        if not self.llm_provider:
            return CommandResult(success=False, message="LLM not initialized")
        
        try:
            history = [Message(role="user", content=command)]
            
            response = await self.llm_provider.chat(
                messages=history,
                tools=self.tool_registry.get_definitions() if self.tool_registry else None,
            )
            
            if response.text:
                await context.output.display(response.text)
            
            return CommandResult(success=True, message=response.text)
        
        except Exception as e:
            return CommandResult(success=False, message=str(e))
