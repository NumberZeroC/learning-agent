#!/usr/bin/env python3

import httpx
import json

api_key = "sk-sp-1103f012953e45d984ab8fbd486e6e16"
base_url = "https://coding.dashscope.aliyuncs.com/v1"

payload = {
    "model": "qwen3.5-plus",
    "messages": [{"role": "user", "content": "你好，请用一句话介绍你自己"}],
}

headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}


with httpx.Client(timeout=60) as client:
    resp = client.post(f"{base_url}/chat/completions", json=payload, headers=headers)
    print("状态:", resp.status_code)

    if resp.status_code == 200:
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        print("回复:", content)
        print("模型:", data.get("model"))
        print("Tokens:", data.get("usage"))
    else:
        print("错误:", resp.text)
