#!/usr/bin/env python3
"""
Ask Service - Web 问答助手服务（精简版）

核心功能：
- 对话历史管理
- Agent 回复生成
- 多轮对话支持
- 流式响应
"""

import os
import sys
import json
import threading
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import urllib.request
import urllib.error

# 项目路径
web_dir = Path(__file__).parent
project_dir = web_dir.parent


class AskService:
    """
    Ask 服务 - Web 问答助手
    """
    
    def __init__(self, config_path: str = "config/agent_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # 对话历史存储
        self._histories: Dict[str, List[Dict]] = {}
        
        # API 配置
        self.api_key = os.getenv('DASHSCOPE_API_KEY', '')
        self.base_url = "https://coding.dashscope.aliyuncs.com/v1"
        self.model = "qwen3.5-plus"
        
        # Agent 配置
        self.agents = self._init_agents()
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        import yaml
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def _init_agents(self) -> Dict[str, Dict]:
        """初始化 Agent 列表"""
        agents_config = self.config.get('agents', {})
        agents = {}
        
        for name, conf in agents_config.items():
            if conf.get('enabled', False):
                agents[name] = {
                    "name": name,
                    "role": conf.get('role', '助手'),
                    "system_prompt": conf.get('system_prompt', ''),
                    "layer": conf.get('layer', 0)
                }
        
        return agents
    
    def get_available_agents(self) -> List[Dict]:
        """获取可用 Agent 列表"""
        return list(self.agents.values())
    
    def chat(self, message: str, agent_name: str = "master_agent") -> Dict:
        """
        发送消息并获取回复
        
        Args:
            message: 用户消息
            agent_name: Agent 名称
            
        Returns:
            Dict: {success, reply, agent, timestamp}
        """
        try:
            # 获取 Agent 配置
            agent = self.agents.get(agent_name, {})
            system_prompt = agent.get('system_prompt', '你是一个有帮助的 AI 助手。')
            
            # 调用 LLM API
            reply = self._call_llm(message, system_prompt)
            
            # 保存历史
            self._save_history(agent_name, message, reply)
            
            return {
                "success": True,
                "reply": reply,
                "agent": agent_name,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent": agent_name,
                "timestamp": datetime.now().isoformat()
            }
    
    def _call_llm(self, user_message: str, system_prompt: str, timeout: int = 120) -> str:
        """调用大模型 API（非流式）"""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4000,
            "stream": False
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            else:
                return "抱歉，我无法回答这个问题。"
    
    def chat_stream(self, user_message: str, system_prompt: str, timeout: int = 120):
        """
        流式调用大模型 API
        
        Yields:
            Dict: {type: 'token', content: '...'} 或 {type: 'error', error: '...'}
        """
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4000,
            "stream": True
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                full_content = ""
                
                # 读取 SSE 流
                while True:
                    line = response.readline()
                    if not line:
                        break
                    
                    line = line.decode('utf-8').strip()
                    
                    # 跳过空行和注释
                    if not line or line.startswith(':'):
                        continue
                    
                    # 解析 SSE 数据
                    if line.startswith('data: '):
                        data_str = line[6:]
                        
                        # 检查结束标记
                        if data_str.strip() == '[DONE]':
                            break
                        
                        try:
                            chunk = json.loads(data_str)
                            
                            # 提取 token 内容
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                
                                if content:
                                    full_content += content
                                    yield {
                                        "type": "token",
                                        "content": content
                                    }
                        except json.JSONDecodeError:
                            continue
                
                # 保存完整回复到历史
                if full_content:
                    self._save_history_to_file(user_message, full_content)
                
                # 发送结束事件
                yield {
                    "type": "end",
                    "timestamp": datetime.now().isoformat()
                }
                    
        except Exception as e:
            yield {
                "type": "error",
                "error": str(e)
            }
            # 出错时也发送结束事件
            yield {
                "type": "end",
                "timestamp": datetime.now().isoformat()
            }
    
    def _save_history(self, agent_name: str, user_msg: str, reply: str):
        """保存对话历史到内存"""
        if agent_name not in self._histories:
            self._histories[agent_name] = []
        
        self._histories[agent_name].append({
            "role": "user",
            "content": user_msg,
            "timestamp": datetime.now().isoformat()
        })
        self._histories[agent_name].append({
            "role": "assistant",
            "content": reply,
            "timestamp": datetime.now().isoformat()
        })
        
        # 限制历史长度（最多 20 条）
        if len(self._histories[agent_name]) > 20:
            self._histories[agent_name] = self._histories[agent_name][-20:]
    
    def _save_history_to_file(self, user_msg: str, reply: str, agent_name: str = "master_agent"):
        """保存对话历史到文件（用于流式模式）"""
        # 保存到内存
        self._save_history(agent_name, user_msg, reply)
        
        # 保存到文件
        history_file = project_dir / "data" / "chat_history" / f"{agent_name}.json"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        
        history = []
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except:
                history = []
        
        history.append({
            "role": "user",
            "content": user_msg,
            "timestamp": datetime.now().isoformat()
        })
        history.append({
            "role": "assistant",
            "content": reply,
            "timestamp": datetime.now().isoformat()
        })
        
        # 限制长度
        if len(history) > 100:
            history = history[-100:]
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    def get_history(self, agent_name: str = "master_agent", limit: int = 20) -> List[Dict]:
        """获取对话历史"""
        history = self._histories.get(agent_name, [])
        return history[-limit:] if limit else history
    
    def clear_history(self, agent_name: str = "master_agent"):
        """清空对话历史"""
        if agent_name in self._histories:
            self._histories[agent_name] = []


# 单例模式
_instance: Optional[AskService] = None
_lock = threading.Lock()


def get_ask_service() -> AskService:
    """获取 Ask 服务单例"""
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = AskService()
    return _instance
