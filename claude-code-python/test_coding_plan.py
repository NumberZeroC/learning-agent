#!/usr/bin/env python
"""Test Aliyun Coding Plan connection"""

import asyncio
import os
import sys

async def test_coding_plan():
    """Test Coding Plan connection"""
    
    print("🔧 Testing Aliyun Coding Plan connection...")
    print()
    
    # Check environment
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    model = os.environ.get("ANTHROPIC_MODEL", "qwen-coder-plus")
    
    print("📋 Configuration:")
    print(f"   API Key: {'✅ ' + api_key[:10] + '...' if api_key else '❌ Not set'}")
    print(f"   Base URL: {base_url or '❌ Not set'}")
    print(f"   Model: {model}")
    print()
    
    if not api_key:
        print("❌ API Key not configured!")
        return False
    
    if not base_url:
        print("❌ Base URL not configured!")
        print()
        print("Set ANTHROPIC_BASE_URL:")
        print("  export ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic")
        return False
    
    try:
        from src.llm.anthropic import AnthropicProvider
        from src.types.llm import LLMConfig
        from src.types.messages import Message
        
        # Create provider
        provider = AnthropicProvider(
            api_key=api_key,
            base_url=base_url,
            config=LLMConfig(model=model),
        )
        
        print(f"🤖 Provider created: {provider}")
        print()
        
        # Test connection
        print("📡 Sending test request...")
        messages = [
            Message(role="user", content="你好，请简单回复我")
        ]
        
        response = await provider.chat(messages)
        
        print()
        print("✅ Connection successful!")
        print()
        print(f"📝 Response:")
        print(f"   {response.text[:100]}")
        print()
        print(f"📊 Usage:")
        print(f"   Input tokens: {response.usage.input_tokens}")
        print(f"   Output tokens: {response.usage.output_tokens}")
        print(f"   Total: {response.usage.total_tokens}")
        
        await provider.close()
        
        return True
        
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check API Key is correct (Coding Plan key)")
        print("2. Check Base URL is correct")
        print("3. Ensure you have balance in Aliyun account")
        print("4. Check network connection")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_coding_plan())
    sys.exit(0 if success else 1)
