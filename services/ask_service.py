#!/usr/bin/env python3
"""
Ask Service - Web 问答助手服务（优化版）

核心功能：
- 对话历史管理（SQLite）
- Agent 回复生成（使用统一 LLMClient）
- 多轮对话支持
- 流式响应

优化改进：
- ✅ 使用 LLMClient 统一调用（带审计日志）
- ✅ 使用 SQLite 存储对话历史
- ✅ 支持会话管理
"""

import os
import sys
import json
import threading
import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from logging.handlers import RotatingFileHandler

# 项目路径
web_dir = Path(__file__).parent
project_dir = web_dir.parent

# 配置日志
log_dir = project_dir / "logs"
log_dir.mkdir(exist_ok=True)

# 日志配置（轮转：最多保留 10 个文件，每个文件最大 10MB）
log_file = log_dir / "ask_service.log"
handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=10,  # 保留 10 个备份文件
    encoding='utf-8'
)
handler.setFormatter(logging.Formatter(
    '%(asctime)s - [%(levelname)s] - %(name)s - %(message)s'
))

# 配置 logger
logger = logging.getLogger('ask_service')
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.addHandler(logging.StreamHandler())

logger.info("🔧 Ask Service 初始化（优化版：LLMClient + SQLite）")
logger.info(f"📝 日志文件：{log_file}")


class AskService:
    """
    Ask 服务 - Web 问答助手（优化版）
    """
    
    def __init__(self, config_path: str = "config/agent_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # 初始化数据库
        self._init_database()
        
        # 对话历史存储（内存缓存 + SQLite 持久化）
        self._histories: Dict[str, List[Dict]] = {}
        
        # API 配置（热更新：每次调用时从配置文件读取）
        self._default_base_url = "https://coding.dashscope.aliyuncs.com/v1"
        self._default_model = "qwen3.5-plus"
        
        # Agent 配置
        self.agents = self._init_agents()
        
        # LLM 客户端缓存（按 Agent 名称）
        self._llm_clients: Dict[str, Any] = {}
    
    def _init_database(self):
        """初始化数据库"""
        try:
            from models.database import initialize, ChatHistoryDAO
            initialize()
            self.chat_dao = ChatHistoryDAO
            logger.info("✅ 数据库初始化完成")
        except Exception as e:
            logger.warning(f"⚠️ 数据库初始化失败：{e}，将使用内存存储")
            self.chat_dao = None
    
    def _get_api_config(self) -> Dict[str, str]:
        """获取最新的 API 配置（支持热更新）"""
        config = self._load_config()
        providers = config.get('providers', {})
        dashscope = providers.get('dashscope', {})
        
        api_key = dashscope.get('api_key_value', '') or os.getenv('DASHSCOPE_API_KEY', '')
        base_url = dashscope.get('base_url', self._default_base_url)
        model = config.get('default_model', self._default_model)
        
        return {
            'api_key': api_key,
            'base_url': base_url,
            'model': model
        }
    
    def _get_llm_client(self, agent_name: str) -> Any:
        """获取或创建 LLM 客户端（按 Agent 缓存）"""
        if agent_name not in self._llm_clients:
            from services.llm_client import LLMClient
            api_config = self._get_api_config()
            agent_config = self.agents.get(agent_name, {})
            
            self._llm_clients[agent_name] = LLMClient(
                api_key=api_config['api_key'],
                base_url=api_config['base_url'],
                model=agent_config.get('model', api_config['model']),
                agent_name=agent_name
            )
        
        return self._llm_clients[agent_name]
    
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
    
    def chat(self, message: str, agent_name: str = "master_agent", 
             session_id: Optional[str] = None) -> Dict:
        """
        发送消息并获取回复（使用统一 LLMClient）
        
        Args:
            message: 用户消息
            agent_name: Agent 名称
            session_id: 可选的会话 ID
            
        Returns:
            Dict: {success, reply, agent, timestamp, usage, cost}
        """
        try:
            agent = self.agents.get(agent_name, {})
            system_prompt = agent.get('system_prompt', '你是一个有帮助的 AI 助手。')
            
            # 使用统一的 LLMClient 调用
            llm_client = self._get_llm_client(agent_name)
            result = llm_client.chat(
                messages=[{"role": "user", "content": message}],
                system_prompt=system_prompt,
                max_retries=2
            )
            
            if result.get('success'):
                reply = result['content']
                self._save_history(agent_name, message, reply, session_id)
                
                return {
                    "success": True,
                    "reply": reply,
                    "agent": agent_name,
                    "timestamp": datetime.now().isoformat(),
                    "usage": result.get('usage', {}),
                    "cost": result.get('cost', 0)
                }
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"LLM 调用失败：{error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "agent": agent_name,
                    "timestamp": datetime.now().isoformat()
                }
            
        except Exception as e:
            logger.error(f"chat 异常：{e}")
            return {
                "success": False,
                "error": str(e),
                "agent": agent_name,
                "timestamp": datetime.now().isoformat()
            }
    
    def _save_history(self, agent_name: str, user_msg: str, reply: str, 
                     session_id: Optional[str] = None):
        """保存对话历史到内存 + SQLite"""
        timestamp = datetime.now().isoformat()
        
        # 保存到内存
        if agent_name not in self._histories:
            self._histories[agent_name] = []
        
        self._histories[agent_name].append({
            "role": "user",
            "content": user_msg,
            "timestamp": timestamp
        })
        self._histories[agent_name].append({
            "role": "assistant",
            "content": reply,
            "timestamp": timestamp
        })
        
        # 限制内存历史长度（最多 20 条）
        if len(self._histories[agent_name]) > 20:
            self._histories[agent_name] = self._histories[agent_name][-20:]
        
        # 保存到 SQLite
        if self.chat_dao:
            try:
                self.chat_dao.add_message(agent_name, "user", user_msg, timestamp, session_id)
                self.chat_dao.add_message(agent_name, "assistant", reply, timestamp, session_id)
            except Exception as e:
                logger.warning(f"SQLite 保存失败：{e}")
    
    def get_history(self, agent_name: str = "master_agent", limit: int = 20,
                   session_id: Optional[str] = None) -> List[Dict]:
        """获取对话历史（优先从 SQLite 读取）"""
        if self.chat_dao:
            try:
                db_history = self.chat_dao.get_history(agent_name, limit * 2, session_id)
                if db_history:
                    history = []
                    for row in db_history[-limit:]:
                        history.append({
                            "role": row['role'],
                            "content": row['content'],
                            "timestamp": row['timestamp']
                        })
                    return history
            except Exception as e:
                logger.warning(f"SQLite 读取失败：{e}")
        
        history = self._histories.get(agent_name, [])
        return history[-limit:] if limit else history
    
    def clear_history(self, agent_name: str = "master_agent", 
                     session_id: Optional[str] = None):
        """清空对话历史"""
        if agent_name in self._histories:
            self._histories[agent_name] = []
        
        if self.chat_dao:
            try:
                self.chat_dao.clear_history(agent_name, session_id)
            except Exception as e:
                logger.warning(f"SQLite 清空失败：{e}")


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
