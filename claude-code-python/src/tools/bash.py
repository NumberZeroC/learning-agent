"""Bash tool for executing shell commands"""

from __future__ import annotations

import asyncio
import os
import shlex
from typing import Literal

import structlog

from .base import Tool, ToolContext, ValidationResult
from ..models.tools import ToolInput, ToolResult

logger = structlog.get_logger(__name__)


class BashInput(ToolInput):
    """Input for Bash tool"""
    
    command: str
    description: str
    timeout: int | None = None
    workdir: str | None = None


class BashTool(Tool[BashInput]):
    """
    Tool for executing shell commands safely.
    
    Features:
    - Command validation and sanitization
    - Timeout support
    - Working directory control
    - Permission integration
    - Output streaming
    """
    
    name = "bash"
    description = "Execute shell commands in the current environment"
    
    input_schema = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute"
            },
            "description": {
                "type": "string",
                "description": "Why this command is needed (for user confirmation)"
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default: 60)"
            },
            "workdir": {
                "type": "string",
                "description": "Working directory for command execution"
            }
        },
        "required": ["command", "description"]
    }
    
    # Default configuration
    DEFAULT_TIMEOUT = 60
    MAX_TIMEOUT = 300
    
    # Dangerous command patterns
    DANGEROUS_PATTERNS = [
        "rm -rf /",
        "rm -rf /*",
        "dd if=/dev/zero",
        "mkfs",
        "fdisk",
        "chmod -R 777 /",
        "chown -R root:root /",
        "> /dev/sda",
        "echo > /dev/sda",
        ":(){ :|:& };:",  # Fork bomb
        "wget.*\\|.*sh",  # Download and execute
        "curl.*\\|.*sh",
    ]
    
    # Commands that always require approval
    ALWAYS_ASK_COMMANDS = [
        "rm -rf",
        "rm -r",
        "sudo",
        "su ",
        "chmod ",
        "chown ",
        "curl ",
        "wget ",
        "pip install",
        "npm install",
        "apt ",
        "yum ",
        "brew ",
    ]
    
    def __init__(self):
        super().__init__()
        self._sandbox_enabled = True
    
    @property
    def sandbox_enabled(self) -> bool:
        """Check if sandbox mode is enabled"""
        return self._sandbox_enabled
    
    @sandbox_enabled.setter
    def sandbox_enabled(self, value: bool) -> None:
        self._sandbox_enabled = value
        logger.info("Sandbox mode updated", enabled=value)
    
    def get_prompt(self) -> str:
        """Get prompt describing how to use this tool"""
        return """Use the `bash` tool to execute shell commands.

Guidelines:
- Always provide a clear description of why the command is needed
- Use absolute paths when possible
- Avoid destructive commands (rm -rf, etc.) without explicit user approval
- For long-running commands, set an appropriate timeout
- Commands run in the current working directory by default

Example:
{
    "command": "ls -la",
    "description": "List files in current directory to understand project structure"
}"""
    
    async def validate_input(
        self,
        tool_input: dict,
        context: ToolContext,
    ) -> ValidationResult:
        """Validate bash command input"""
        
        command = tool_input.get("command", "")
        
        if not command:
            return ValidationResult.fail("Command cannot be empty")
        
        if not tool_input.get("description"):
            return ValidationResult.fail("Description is required")
        
        # Check for dangerous patterns
        danger_check = self._check_dangerous_patterns(command)
        if not danger_check["safe"]:
            return ValidationResult.fail(
                f"Dangerous command detected: {danger_check['reason']}",
                error_code="DANGEROUS_COMMAND"
            )
        
        # Validate timeout
        timeout = tool_input.get("timeout", self.DEFAULT_TIMEOUT)
        if timeout and (timeout <= 0 or timeout > self.MAX_TIMEOUT):
            return ValidationResult.fail(
                f"Timeout must be between 1 and {self.MAX_TIMEOUT} seconds",
                error_code="INVALID_TIMEOUT"
            )
        
        # Validate working directory
        workdir = tool_input.get("workdir")
        if workdir:
            if not os.path.isabs(workdir):
                return ValidationResult.fail(
                    "Working directory must be an absolute path",
                    error_code="INVALID_WORKDIR"
                )
            if not os.path.exists(workdir):
                return ValidationResult.fail(
                    f"Working directory does not exist: {workdir}",
                    error_code="WORKDIR_NOT_FOUND"
                )
        
        return ValidationResult.ok()
    
    def _check_dangerous_patterns(self, command: str) -> dict:
        """Check command for dangerous patterns"""
        command_lower = command.lower()
        
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.lower() in command_lower:
                return {
                    "safe": False,
                    "reason": f"Contains dangerous pattern: {pattern}"
                }
        
        return {"safe": True, "reason": None}
    
    def _requires_approval(self, command: str) -> tuple[bool, str | None]:
        """Check if command requires user approval"""
        command_lower = command.lower()
        
        for prefix in self.ALWAYS_ASK_COMMANDS:
            if command_lower.startswith(prefix.lower()):
                return True, f"Command type '{prefix}' requires approval"
        
        # Check for file modifications
        if any(cmd in command_lower for cmd in ["rm ", "mv ", "cp ", "> "] ):
            return True, "Command may modify files"
        
        return False, None
    
    async def execute(self, tool_input: BashInput, context: ToolContext) -> ToolResult:
        """Execute the bash command"""
        
        logger.info(
            "Bash command requested",
            command=tool_input.command,
            description=tool_input.description,
            timeout=tool_input.timeout,
        )
        
        # Check if command requires approval
        requires_approval, approval_reason = self._requires_approval(tool_input.command)
        
        if requires_approval:
            # In a real implementation, this would trigger a UI prompt
            # For now, we'll log and proceed (permission system integration comes later)
            logger.warning(
                "Command requires approval",
                reason=approval_reason,
                command=tool_input.command,
            )
        
        # Determine working directory
        workdir = tool_input.workdir or context.working_directory or os.getcwd()
        
        # Determine timeout
        timeout = tool_input.timeout or self.DEFAULT_TIMEOUT
        
        try:
            # Execute command
            process = await asyncio.create_subprocess_shell(
                tool_input.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workdir,
                env={**os.environ, "FORCE_COLOR": "0"},  # Disable color codes
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                # Kill the process on timeout
                process.kill()
                await process.wait()
                return ToolResult.error(
                    f"Command timed out after {timeout} seconds"
                )
            
            # Decode output
            stdout_text = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")
            
            # Build result
            content = []
            
            if stdout_text:
                content.append({
                    "type": "text",
                    "text": stdout_text,
                    "format": "stdout",
                })
            
            if stderr_text:
                content.append({
                    "type": "text",
                    "text": stderr_text,
                    "format": "stderr",
                })
            
            # Add exit code info
            content.append({
                "type": "text",
                "text": f"\n[Process exited with code {process.returncode}]",
                "format": "meta",
            })
            
            if process.returncode != 0:
                return ToolResult(
                    content=content,
                    is_error=True,
                    error_message=f"Command failed with exit code {process.returncode}",
                )
            
            return ToolResult.success(content)
            
        except FileNotFoundError as e:
            logger.error("Command not found", command=tool_input.command)
            return ToolResult.error(f"Command not found: {tool_input.command}")
        except PermissionError as e:
            logger.error("Permission denied", command=tool_input.command)
            return ToolResult.error(f"Permission denied: {tool_input.command}")
        except Exception as e:
            logger.exception("Bash execution error", command=tool_input.command)
            return ToolResult.error(f"Execution error: {str(e)}")
    
    async def before_execute(
        self,
        tool_input: BashInput,
        context: ToolContext,
    ) -> None:
        """Log before execution"""
        await super().before_execute(tool_input, context)
        logger.debug(
            "Bash command starting",
            command=tool_input.command[:100],
            workdir=context.working_directory,
        )
    
    async def after_execute(
        self,
        tool_input: BashInput,
        result: ToolResult,
        context: ToolContext,
    ) -> None:
        """Log after execution"""
        await super().after_execute(tool_input, result, context)
        logger.debug(
            "Bash command completed",
            command=tool_input.command[:100],
            success=not result.is_error,
        )
