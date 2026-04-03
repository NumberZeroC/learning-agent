#!/usr/bin/env python
"""Test connection to Aliyun DashScope"""

import asyncio
import os
import sys

async def test_connection():
    """Test Aliyun provider connection"""
    
    print("🔧 Testing Aliyun DashScope connection...")
    print()
    
    # Load config
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.config import get_api_config
    from src.llm.aliyun import AliyunProvider
    from src.types.llm import LLMConfig
    from src.types.messages import Message
    
    config = get_api_config()
    
    print(f"📋 Configuration:")
    print(f"   Provider: {config['provider']}")
    print(f"   API Key: {'✅ Set' if config['api_key'] else '❌ Not set'}")
    print(f"   Model: qwen3.5-plus")
    print()
    
    if not config['api_key']:
        print("❌ API Key not configured!")
        return False
    
    try:
        # Create provider
        provider = AliyunProvider(
            api_key=config['api_key'],
            config=LLMConfig(model="qwen3.5-plus"),
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
        print("1. Check API Key is correct")
        print("2. Ensure you have balance in Aliyun account")
        print("3. Check network connection")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
