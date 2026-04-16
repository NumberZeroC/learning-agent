#!/usr/bin/env python3
"""
LLM 调用测试 - 检查模型身份幻觉问题

测试不同prompt下模型回复是否正确
"""

import sys

sys.path.insert(0, "/home/admin/.openclaw/workspace/learning-agent")

from services.llm_client import LLMClient

api_key = "sk-sp-1103f012953e45d984ab8fbd486e6e16"

client = LLMClient(
    api_key=api_key,
    base_url="https://coding.dashscope.aliyuncs.com/v1",
    model="qwen3.5-plus",
    agent_name="identity_test",
    enable_cache=False,
)

print("=" * 60)
print("LLM 身份测试")
print("=" * 60)

# 测试1: 模糊prompt
print("\n测试1: 模糊prompt (可能出现幻觉)")
print("Prompt: '你好，请用一句话介绍你自己'")
result1 = client.chat(
    messages=[{"role": "user", "content": "你好，请用一句话介绍你自己"}], max_retries=2
)
if result1.get("success"):
    print(f"回复: {result1['content']}")
    print(f"Tokens: {result1['usage']['total_tokens']}")
else:
    print(f"失败: {result1.get('error')}")

# 测试2: 明确prompt
print("\n测试2: 明确prompt")
print("Prompt: '你好，请用一句话介绍你自己，说明你是什么模型'")
result2 = client.chat(
    messages=[
        {"role": "user", "content": "你好，请用一句话介绍你自己，说明你是什么模型"}
    ],
    max_retries=2,
)
if result2.get("success"):
    print(f"回复: {result2['content']}")
    print(f"Tokens: {result2['usage']['total_tokens']}")
else:
    print(f"失败: {result2.get('error')}")

# 测试3: 有system_prompt约束
print("\n测试3: 有system_prompt约束")
print("System: '你是阿里巴巴的通义千问(Qwen)大语言模型'")
result3 = client.chat(
    messages=[{"role": "user", "content": "你好，请用一句话介绍你自己"}],
    system_prompt="你是阿里巴巴的通义千问(Qwen)大语言模型，由阿里巴巴团队开发。回答时要准确说明自己的身份。",
    max_retries=2,
)
if result3.get("success"):
    print(f"回复: {result3['content']}")
    print(f"Tokens: {result3['usage']['total_tokens']}")
else:
    print(f"失败: {result3.get('error')}")

print("\n" + "=" * 60)
print("统计:")
stats = LLMClient.get_stats()
print(f"  总调用: {stats['total_calls']}")
print(f"  成功: {stats['success_calls']}")
print(f"  总成本: {stats['total_cost']}")
print("=" * 60)
