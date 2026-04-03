"""CLI entry point for Claude Code Python"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import io

# Ensure UTF-8 encoding for Chinese input/output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import click
import structlog

from .. import __version__

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@click.group()
@click.version_option(version=__version__, prog_name="ccp")
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose output",
)
@click.option(
    "--config", "-c",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
@click.pass_context
def cli(ctx, verbose: bool, config: str | None):
    """
    Claude Code Python (CCP) - Terminal AI Programming Assistant
    
    A Python implementation of Claude Code CLI.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config_path"] = config
    
    # Set log level
    if verbose:
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        )
    
    logger.debug("CCP CLI started", version=__version__)


@cli.command()
@click.argument("task", required=False)
@click.option(
    "--interactive", "-i",
    is_flag=True,
    help="Run in interactive mode",
)
@click.option(
    "--model", "-m",
    default=None,
    help="Model to use (default: from ANTHROPIC_MODEL env or qwen3.5-plus)",
)
@click.option(
    "--workdir", "-w",
    default=None,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Working directory for file operations (default: current directory)",
)
@click.pass_context
def run(ctx, task: str | None, interactive: bool, model: str, workdir: str | None):
    """
    Run a task with Claude.
    
    TASK: The task to execute (optional in interactive mode)
    
    Examples:
    
        ccp run "Refactor the code in src/"
        
        ccp run -i  # Interactive mode
        
        ccp run -w /path/to/project "Analyze this project"
    
    Aliyun (通义千问) Support:
    
        export USE_ALIYUN=1
        export DASHSCOPE_API_KEY=your-key-here
        ccp run -m qwen-plus "Hello"
    """
    from ..llm import AnthropicProvider, AliyunProvider
    from ..models.llm import LLMConfig
    from ..models.messages import Message
    
    logger.info("Running task", task=task, model=model, interactive=interactive)
    
    # Determine provider
    use_aliyun = os.environ.get("USE_ALIYUN", "").lower() in ("1", "true", "yes")
    aliyun_key = os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("ALIYUN_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Auto-detect
    if not use_aliyun and not anthropic_key and aliyun_key:
        use_aliyun = True
    
    # Check API key
    if use_aliyun:
        if not aliyun_key:
            click.echo(
                click.style("Error: ", fg="red", bold=True) +
                "Aliyun API key not set. Set DASHSCOPE_API_KEY or ALIYUN_API_KEY."
            )
            click.echo()
            click.echo("Or use Anthropic:")
            click.echo("  export ANTHROPIC_API_KEY=your-key-here")
            sys.exit(1)
        api_key = aliyun_key
        provider_name = "Aliyun"
    else:
        if not anthropic_key:
            click.echo(
                click.style("Error: ", fg="red", bold=True) +
                "ANTHROPIC_API_KEY environment variable not set."
            )
            click.echo()
            click.echo("Set your API key:")
            click.echo("  export ANTHROPIC_API_KEY=your-key-here")
            click.echo()
            click.echo("Or use Aliyun (通义千问):")
            click.echo("  export USE_ALIYUN=1")
            click.echo("  export DASHSCOPE_API_KEY=your-key-here")
            sys.exit(1)
        api_key = anthropic_key
        provider_name = "Anthropic"
    
    click.echo(f"🤖 Using {provider_name} provider...")
    
    # Get model from env or use default
    if model is None:
        model = os.environ.get("ANTHROPIC_MODEL", "qwen3.5-plus")
    
    async def _run():
        config = LLMConfig(model=model)
        
        if use_aliyun:
            llm = AliyunProvider(api_key=api_key, config=config)
        else:
            llm = AnthropicProvider(api_key=api_key, config=config)
        
        try:
            if interactive or not task:
                # Interactive mode
                await run_interactive(llm, workdir=workdir)
            else:
                # Batch mode
                await run_batch(llm, task, workdir=workdir)
        finally:
            await llm.close()
    
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        click.echo()
        click.echo("Interrupted.")
        sys.exit(0)
    except Exception as e:
        logger.exception("Error running task")
        click.echo(click.style(f"Error: {e}", fg="red"))
        sys.exit(1)


async def run_batch(llm, task: str, workdir: str | None = None):
    """Run a single task in batch mode with full agent loop"""
    from ..tools.registry import ToolRegistry
    from ..tools.bash import BashTool
    from ..tools.file_read import FileReadTool
    from ..tools.file_edit import FileEditTool
    from ..tools.file_write import FileWriteTool
    from ..tools.file_write_batch import FileWriteBatchTool
    from ..tools.grep import GrepTool
    from ..tools.glob import GlobTool
    from ..tools.mkdir import MkdirTool
    from ..tools.project_template import ProjectTemplateTool
    from ..tools.base import ToolContext
    from ..core.agent import AgentLoop
    
    # Use specified workdir or current directory
    working_dir = workdir if workdir else os.getcwd()
    
    click.echo(click.style("🤖 ", bold=True) + f"Processing: {task}")
    click.echo(click.style(f"📁 Working directory: {working_dir}", dim=True))
    click.echo()
    
    # Create context
    context = ToolContext(
        session_id="batch-session",
        working_directory=working_dir,
    )
    
    # Initialize tool registry with all tools
    registry = ToolRegistry()
    registry.register(BashTool())
    registry.register(FileReadTool())
    registry.register(FileEditTool())
    registry.register(FileWriteTool())
    registry.register(FileWriteBatchTool())
    registry.register(GrepTool())
    registry.register(GlobTool())
    registry.register(MkdirTool())
    registry.register(ProjectTemplateTool())
    
    try:
        # Use full agent loop for autonomous execution
        agent = AgentLoop(llm, registry, context, max_iterations=20)
        final_answer = await agent.run(task)
        
        click.echo()
        click.echo(click.style("━" * 50, dim=True))
        click.echo(click.style("✅ Task completed", fg="green", bold=True))
        
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise


async def run_interactive(llm, workdir: str | None = None):
    """Run in interactive mode with full agent loop"""
    from ..tools.registry import ToolRegistry
    from ..tools.bash import BashTool
    from ..tools.file_read import FileReadTool
    from ..tools.file_edit import FileEditTool
    from ..tools.file_write import FileWriteTool
    from ..tools.file_write_batch import FileWriteBatchTool
    from ..tools.grep import GrepTool
    from ..tools.glob import GlobTool
    from ..tools.mkdir import MkdirTool
    from ..tools.project_template import ProjectTemplateTool
    from ..tools.base import ToolContext
    from ..core.agent import AgentLoop
    from ..models.messages import Message
    
    # Use specified workdir or current directory
    working_dir = workdir if workdir else os.getcwd()
    
    click.echo(click.style("🤖 ", bold=True) + "Claude Code Python (Interactive Mode)")
    click.echo(click.style("Type 'exit' or Ctrl+D to quit", dim=True))
    click.echo(click.style(f"📁 Working directory: {working_dir}", dim=True))
    click.echo(click.style("Tools: bash, file_*, grep, glob, mkdir, project_template", dim=True))
    click.echo(click.style("Try: 'Analyze this project' or 'Create a Python CLI project called my_project'", dim=True))
    click.echo()
    
    # Initialize tool registry
    registry = ToolRegistry()
    registry.register(BashTool())
    registry.register(FileReadTool())
    registry.register(FileEditTool())
    registry.register(FileWriteTool())
    registry.register(FileWriteBatchTool())
    registry.register(GrepTool())
    registry.register(GlobTool())
    registry.register(MkdirTool())
    registry.register(ProjectTemplateTool())
    
    tool_context = ToolContext(session_id="interactive", working_directory=working_dir)
    
    # Session message history (for multi-turn conversation)
    session_messages = []
    
    while True:
        try:
            # Get user input (with UTF-8 encoding support)
            import sys
            click.echo(click.style("You", bold=True, fg="blue") + ": ", nl=False)
            sys.stdout.flush()
            user_input = sys.stdin.readline().strip()
            
            if user_input.lower() in ("exit", "quit", "/quit"):
                click.echo("Goodbye!")
                break
            
            if not user_input.strip():
                continue
            
            click.echo()
            click.echo(click.style("Claude", bold=True, fg="green") + ":")
            click.echo()
            
            # Use full agent loop for autonomous execution
            agent = AgentLoop(llm, registry, tool_context, max_iterations=20)
            
            # Include session history for context
            if session_messages:
                click.echo(click.style(f"[Context: {len(session_messages)} prior messages]", dim=True))
                click.echo()
            
            final_answer = await agent.run(user_input)
            
            # Save to session history
            session_messages.append(Message(role="user", content=user_input))
            if final_answer:
                session_messages.append(Message(role="assistant", content=final_answer))
            
            # Keep history manageable (last 20 messages)
            if len(session_messages) > 20:
                session_messages = session_messages[-20:]
            
            click.echo()
            
        except KeyboardInterrupt:
            click.echo()
            click.echo(click.style("[Interrupted. Type 'exit' to quit.]", dim=True))
            continue
        except EOFError:
            click.echo("\nGoodbye!")
            break
        except Exception as e:
            logger.exception("Error in interactive mode")
            click.echo(click.style(f"Error: {e}", fg="red"))
            break


@cli.command()
@click.pass_context
def config(ctx):
    """Interactive configuration wizard"""
    click.echo("🔧 Configuration Wizard")
    click.echo()
    
    # Check current config
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if api_key:
        masked = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
        click.echo(f"✓ API key is set: {masked}")
    else:
        click.echo("✗ API key is not set")
    
    click.echo()
    click.echo("To configure:")
    click.echo("  1. Get your API key from: https://console.anthropic.com")
    click.echo("  2. Set the environment variable:")
    click.echo("     export ANTHROPIC_API_KEY=your-key-here")
    click.echo()
    click.echo("Or add to your shell config (~/.bashrc, ~/.zshrc):")
    click.echo("  echo 'export ANTHROPIC_API_KEY=your-key-here' >> ~/.bashrc")


@cli.command()
@click.pass_context
def tools(ctx):
    """List available tools"""
    from ..tools.registry import get_default_registry
    
    registry = get_default_registry()
    
    click.echo("🔧 Available Tools")
    click.echo()
    
    tools = registry.get_enabled_tools()
    
    if not tools:
        click.echo("No tools registered yet.")
        click.echo()
        click.echo("Tools will be registered as you use the system.")
        return
    
    for tool in tools:
        status = "✓" if tool.is_enabled else "✗"
        click.echo(f"{status} {tool.name}")
        click.echo(f"    {tool.description}")
        click.echo()
    
    click.echo(f"Total: {len(tools)} tools")


def main():
    """Main entry point"""
    cli(obj={})


if __name__ == "__main__":
    main()
