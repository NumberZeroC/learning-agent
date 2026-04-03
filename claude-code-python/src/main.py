"""Main entry point for CCP"""

from __future__ import annotations

import asyncio
import os

import structlog

from .cli.entry import cli

logger = structlog.get_logger(__name__)


def run_interactive():
    """Run CCP in interactive mode"""
    from .ui.app import CCPApp
    from .llm import AnthropicProvider, AliyunProvider
    from .tools import BashTool, FileReadTool, FileEditTool, FileWriteTool, ToolRegistry
    from .permissions import PermissionEngine, ApprovalManager
    from .permissions.policies import (
        create_safe_file_policy,
        create_dangerous_command_policy,
        create_src_auto_edit_policy,
    )
    from .config import get_api_config
    
    # Load configuration
    api_config = get_api_config()
    
    use_aliyun = api_config["use_aliyun"]
    api_key = api_config["api_key"]
    provider_name = api_config["provider"].title()
    
    # Check API key
    if not api_key:
        print("❌ Error: API key not set")
        print()
        if use_aliyun:
            print("Set Aliyun API key:")
            print("  export DASHSCOPE_API_KEY=your-key-here")
            print("  # Or add to ~/.bashrc or project .env file")
            print()
            print("Get one at: https://dashscope.console.aliyun.com/")
        else:
            print("Set Anthropic API key:")
            print("  export ANTHROPIC_API_KEY=your-key-here")
            print("  # Or use Aliyun:")
            print("  export USE_ALIYUN=1")
            print("  export DASHSCOPE_API_KEY=your-key-here")
            print()
            print("Get one at: https://console.anthropic.com")
        return 1
    
    print(f"🤖 Using {provider_name} provider...")
    
    # Initialize components
    if use_aliyun:
        llm_provider = AliyunProvider(api_key=api_key)
    else:
        llm_provider = AnthropicProvider(api_key=api_key)
    
    # Setup tool registry
    tool_registry = ToolRegistry()
    tool_registry.register(BashTool())
    tool_registry.register(FileReadTool())
    tool_registry.register(FileEditTool())
    tool_registry.register(FileWriteTool())
    
    # Setup permission engine
    permission_engine = PermissionEngine()
    permission_engine.add_policy(create_safe_file_policy())
    permission_engine.add_policy(create_dangerous_command_policy())
    permission_engine.add_policy(create_src_auto_edit_policy())
    
    # Setup approval manager
    approval_manager = ApprovalManager()
    
    # Create and run app
    app = CCPApp(
        llm_provider=llm_provider,
        tool_registry=tool_registry,
        permission_engine=permission_engine,
        approval_manager=approval_manager,
    )
    
    try:
        app.run()
    finally:
        asyncio.run(llm_provider.close())
        asyncio.run(approval_manager.stop())
    
    return 0


def main():
    """Main entry point"""
    cli()


if __name__ == "__main__":
    main()
