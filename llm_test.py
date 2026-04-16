# Test with qwen3.5-plus model
import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace/learning-agent')

from services.llm_client import LLMClient

api_key = 'sk-sp-1103f012953e45d984ab8fbd486e6e16'

client = LLMClient(
    api_key=api_key,
    base_url='https://coding.dashscope.aliyuncs.com/v1',
    model='qwen3.5-plus',
    agent_name='test'
)

result = client.chat(
    messages=[{'role': 'user', 'content': '你好，请用一句话介绍你自己'}],
    max_retries=2
)

if result.get('success'):
    print('✅ 大模型调用成功！')
    print(result)
else:
    print(f'❌ 失败：{result.get("error")}')
