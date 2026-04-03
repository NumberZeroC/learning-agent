#!/usr/bin/env python
"""Test available models for Coding Plan"""

import asyncio
import os
import sys

async def test_model(model_name: str) -> bool:
    """Test a specific model"""
    
    try:
        from src.llm.anthropic import AnthropicProvider
        from src.types.llm import LLMConfig
        from src.types.messages import Message
        
        provider = AnthropicProvider(
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            base_url=os.environ.get("ANTHROPIC_BASE_URL"),
            config=LLMConfig(model=model_name),
        )
        
        messages = [Message(role="user", content="Hi")]
        response = await provider.chat(messages)
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        if "not supported" in error_msg:
            return False
        raise

async def main():
    """Test multiple models"""
    
    print("🔍 Testing available models for Coding Plan...")
    print()
    
    # Common model names to try
    models = [
        "qwen-coder",
        "qwen-coder-plus",
        "qwen2.5-coder",
        "qwen2.5-coder-plus",
        "qwen-2.5-coder",
        "qwen-code",
        "qwen-code-plus",
        "coding-plan",
        "coding-plan-plus",
        "claude-sonnet",
        "claude",
    ]
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    
    print(f"API Key: {api_key[:10]}...")
    print(f"Base URL: {base_url}")
    print()
    
    for model in models:
        print(f"Testing: {model}...", end=" ")
        sys.stdout.flush()
        
        try:
            result = await test_model(model)
            if result:
                print("✅ SUPPORTED!")
                print()
                print(f"🎉 Found supported model: {model}")
                print()
                print(f"Update .env with:")
                print(f"  ANTHROPIC_MODEL={model}")
                return True
            else:
                print("❌ Not supported")
        except Exception as e:
            # Other errors (API key, network, etc.)
            print(f"⚠️ Error: {str(e)[:50]}")
            break
    
    print()
    print("❌ No supported model found in the list.")
    print()
    print("Please check Coding Plan documentation for supported models.")
    return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
