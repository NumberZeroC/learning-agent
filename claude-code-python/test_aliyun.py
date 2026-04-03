#!/usr/bin/env python
"""Test script for Aliyun provider"""

import asyncio
import os
import sys

async def test_aliyun():
    """Test Aliyun provider connection"""
    
    # Check API key
    api_key = os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("ALIYUN_API_KEY")
    
    if not api_key:
        print("❌ API Key not set")
        print()
        print("Set your API key:")
        print("  export DASHSCOPE_API_KEY=sk-xxxxxxxx")
        print("  # or")
        print("  export ALIYUN_API_KEY=sk-xxxxxxxx")
        return False
    
    print("🔑 API Key found")
    
    try:
        from src.llm.aliyun import AliyunProvider
        from src.types.llm import LLMConfig
        from src.types.messages import Message
        
        print("📦 Importing AliyunProvider...")
        
        # Create provider
        provider = AliyunProvider(
            api_key=api_key,
            config=LLMConfig(model="qwen-turbo"),
        )
        
        print(f"🤖 Provider created (model: {provider.model})")
        
        # Test connection
        print("📡 Testing connection...")
        
        messages = [
            Message(role="user", content="你好，请回复'测试成功'")
        ]
        
        response = await provider.chat(messages)
        
        print(f"✅ Response received!")
        print(f"   Text: {response.text[:50]}...")
        print(f"   Tokens: {response.usage.total_tokens}")
        
        await provider.close()
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_aliyun())
    sys.exit(0 if success else 1)
