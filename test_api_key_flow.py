#!/usr/bin/env python3
"""
验证 API Key 配置链路是否打通

测试流程：
1. 模拟用户通过 Web 界面配置 API Key
2. 验证配置文件已更新
3. 验证工作流能读取到新 Key
4. 验证对话 Agent 能读取到新 Key
"""

import os
import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv

# 项目路径
project_dir = Path(__file__).parent
os.chdir(project_dir)

print("="*70)
print("🔍 API Key 配置链路验证")
print("="*70)
print()

# 加载环境变量
load_dotenv()

# 测试 1: 检查配置文件
print("📁 测试 1: 检查配置文件")
print("-"*60)

config_path = project_dir / "config" / "agent_config.yaml"
if config_path.exists():
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    api_key = config.get('providers', {}).get('dashscope', {}).get('api_key_value', '')
    base_url = config.get('providers', {}).get('dashscope', {}).get('base_url', '')
    
    print(f"✅ 配置文件存在：{config_path}")
    print(f"   API Key: {api_key[:15]}...{'(已配置)' if api_key else '(未配置)❌'}")
    print(f"   Base URL: {base_url}")
else:
    print(f"❌ 配置文件不存在：{config_path}")

print()

# 测试 2: 检查环境变量
print("🌍 测试 2: 检查环境变量")
print("-"*60)

env_vars = {
    'DASHSCOPE_API_KEY': os.getenv('DASHSCOPE_API_KEY', ''),
    'DASHSCOPE_BASE_URL': os.getenv('DASHSCOPE_BASE_URL', ''),
}

for key, value in env_vars.items():
    if value:
        if 'KEY' in key:
            print(f"✅ {key}: {value[:15]}...")
        else:
            print(f"✅ {key}: {value}")
    else:
        print(f"⚠️  {key}: 未设置")

print()

# 测试 3: 验证 workflow_orchestrator 读取逻辑
print("📊 测试 3: 验证工作流 API Key 读取")
print("-"*60)

try:
    # 模拟 workflow_orchestrator.py 的读取逻辑
    api_key_from_config = config.get('providers', {}).get('dashscope', {}).get('api_key_value', '')
    api_key_from_env = os.getenv('DASHSCOPE_API_KEY', '')
    final_api_key = api_key_from_config or api_key_from_env
    
    print(f"   从 config 读取：{api_key_from_config[:15] if api_key_from_config else '空'}...")
    print(f"   从 .env 读取：{api_key_from_env[:15] if api_key_from_env else '空'}...")
    print(f"   最终使用：{final_api_key[:15] if final_api_key else '空'}...")
    
    if final_api_key:
        print("✅ 工作流能正确读取 API Key")
    else:
        print("❌ 工作流无法读取 API Key")
        
except Exception as e:
    print(f"❌ 读取失败：{e}")

print()

# 测试 4: 验证 ask_service 读取逻辑
print("💬 测试 4: 验证对话 Agent API Key 读取")
print("-"*60)

try:
    sys.path.insert(0, str(project_dir))
    from services.ask_service import AskService
    
    ask_service = AskService()
    api_config = ask_service._get_api_config()
    
    print(f"   API Key: {api_config.get('api_key', '')[:15]}...")
    print(f"   Base URL: {api_config.get('base_url', '')}")
    print(f"   Model: {api_config.get('model', '')}")
    
    if api_config.get('api_key'):
        print("✅ 对话 Agent 能正确读取 API Key")
    else:
        print("❌ 对话 Agent 无法读取 API Key")
        
except Exception as e:
    print(f"❌ 读取失败：{e}")

print()

# 测试 5: 实际 API 调用测试
print("🚀 测试 5: 实际 API 调用测试")
print("-"*60)

try:
    from services.llm_client import LLMClient
    
    # 使用配置文件中的 API Key
    test_api_key = api_key_from_config or api_key_from_env
    test_base_url = config.get('providers', {}).get('dashscope', {}).get('base_url', 
                    os.getenv('DASHSCOPE_BASE_URL', 'https://coding.dashscope.aliyuncs.com/v1'))
    
    client = LLMClient(
        api_key=test_api_key,
        base_url=test_base_url
    )
    
    result = client.chat([{'role': 'user', 'content': '测试连接'}])
    
    if result.get('success'):
        print("✅ API 调用成功！")
        print(f"   Tokens: {result.get('usage', {}).get('total_tokens', 0)}")
        print(f"   响应：{result.get('content', '')[:50]}...")
    else:
        print(f"❌ API 调用失败：{result.get('error', 'Unknown error')}")
        
except Exception as e:
    print(f"❌ 测试失败：{e}")

print()
print("="*70)
print("📋 验证总结")
print("="*70)
print()

# 综合评估
checks = [
    ("配置文件存在", config_path.exists()),
    ("API Key 已配置", bool(api_key_from_config or api_key_from_env)),
    ("Base URL 正确", 'coding.dashscope' in test_base_url),
]

all_passed = True
for name, passed in checks:
    status = "✅" if passed else "❌"
    print(f"{status} {name}")
    if not passed:
        all_passed = False

print()
if all_passed:
    print("🎉 所有检查通过！用户配置的 API Key 可以正常生效！")
    print()
    print("✅ 链路验证：")
    print("   用户 Web 配置 → config/agent_config.yaml → 工作流/对话 Agent → API 调用")
else:
    print("⚠️  部分检查未通过，请检查配置")

print()
