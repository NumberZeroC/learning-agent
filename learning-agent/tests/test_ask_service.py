#!/usr/bin/env python3
"""
问答服务测试用例

测试 ask_service.py 的核心功能
使用 Mock 替代真实的大模型 API 调用
"""

import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# 添加项目路径
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

from services.ask_service import AskService, get_ask_service


class TestAskServiceInit:
    """测试 AskService 初始化"""
    
    @patch('services.ask_service.os.getenv')
    @patch('services.ask_service.Path.exists')
    @patch('services.ask_service.yaml.safe_load')
    def test_init_with_config(self, mock_yaml_load, mock_exists, mock_getenv):
        """测试有配置文件时的初始化"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {
            "agents": {
                "test_agent": {
                    "enabled": True,
                    "role": "测试专家",
                    "system_prompt": "你是测试专家",
                    "layer": 1
                }
            }
        }
        mock_getenv.return_value = "sk-test-key"
        
        service = AskService("config/agent_config.yaml")
        
        assert service.api_key == "sk-test-key"
        assert len(service.agents) == 1
        assert "test_agent" in service.agents
    
    @patch('services.ask_service.os.getenv')
    @patch('services.ask_service.Path.exists')
    def test_init_without_config(self, mock_exists, mock_getenv):
        """测试无配置文件时的初始化"""
        mock_exists.return_value = False
        mock_getenv.return_value = "sk-test-key"
        
        service = AskService("nonexistent.yaml")
        
        assert service.api_key == "sk-test-key"
        assert service.agents == {}


class TestAskServiceChat:
    """测试聊天功能"""
    
    @patch('services.ask_service.urllib.request.urlopen')
    @patch('services.ask_service.os.getenv')
    @patch('services.ask_service.Path.exists')
    @patch('services.ask_service.yaml.safe_load')
    def test_chat_success(self, mock_yaml_load, mock_exists, mock_getenv, mock_urlopen):
        """测试成功聊天"""
        # 设置 Mock
        mock_exists.return_value = True
        mock_yaml_load.return_value = {
            "agents": {
                "test_agent": {
                    "enabled": True,
                    "role": "测试专家",
                    "system_prompt": "你是测试专家"
                }
            }
        }
        mock_getenv.return_value = "sk-test-key"
        
        # Mock API 响应
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [
                {
                    "message": {
                        "content": "这是测试回答"
                    }
                }
            ]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        service = AskService()
        result = service.chat("什么是机器学习？", "test_agent")
        
        assert result["success"] is True
        assert result["reply"] == "这是测试回答"
        assert result["agent"] == "test_agent"
        assert "timestamp" in result
        mock_urlopen.assert_called_once()
    
    @patch('services.ask_service.urllib.request.urlopen')
    @patch('services.ask_service.os.getenv')
    @patch('services.ask_service.Path.exists')
    @patch('services.ask_service.yaml.safe_load')
    def test_chat_api_error(self, mock_yaml_load, mock_exists, mock_getenv, mock_urlopen):
        """测试 API 错误"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {"agents": {}}
        mock_getenv.return_value = "sk-test-key"
        
        # Mock API 错误
        mock_urlopen.side_effect = Exception("API 调用失败")
        
        service = AskService()
        result = service.chat("测试问题", "test_agent")
        
        assert result["success"] is False
        assert "error" in result
        assert "API 调用失败" in result["error"]
    
    @patch('services.ask_service.urllib.request.urlopen')
    @patch('services.ask_service.os.getenv')
    @patch('services.ask_service.Path.exists')
    @patch('services.ask_service.yaml.safe_load')
    def test_chat_empty_message(self, mock_yaml_load, mock_exists, mock_getenv, mock_urlopen):
        """测试空消息"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {"agents": {}}
        mock_getenv.return_value = "sk-test-key"
        
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "回答"}}]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        service = AskService()
        result = service.chat("", "test_agent")
        
        # 即使消息为空，也应该调用 API
        assert result["success"] is True


class TestAskServiceHistory:
    """测试对话历史功能"""
    
    @patch('services.ask_service.os.getenv')
    @patch('services.ask_service.Path.exists')
    @patch('services.ask_service.yaml.safe_load')
    def test_get_history(self, mock_yaml_load, mock_exists, mock_getenv):
        """测试获取对话历史"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {"agents": {}}
        mock_getenv.return_value = "sk-test-key"
        
        service = AskService()
        
        # 初始应该为空
        history = service.get_history("test_agent")
        assert len(history) == 0
    
    @patch('services.ask_service.urllib.request.urlopen')
    @patch('services.ask_service.os.getenv')
    @patch('services.ask_service.Path.exists')
    @patch('services.ask_service.yaml.safe_load')
    def test_chat_saves_history(self, mock_yaml_load, mock_exists, mock_getenv, mock_urlopen):
        """测试聊天保存历史"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {"agents": {}}
        mock_getenv.return_value = "sk-test-key"
        
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "回答"}}]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        service = AskService()
        service.chat("问题 1", "test_agent")
        service.chat("问题 2", "test_agent")
        
        history = service.get_history("test_agent")
        
        # 应该有 4 条消息（2 个用户问题 + 2 个助手回答）
        assert len(history) == 4
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "问题 1"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "回答"
    
    @patch('services.ask_service.os.getenv')
    @patch('services.ask_service.Path.exists')
    @patch('services.ask_service.yaml.safe_load')
    def test_clear_history(self, mock_yaml_load, mock_exists, mock_getenv):
        """测试清空历史"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {"agents": {}}
        mock_getenv.return_value = "sk-test-key"
        
        service = AskService()
        
        # 手动添加一些历史
        service._histories["test_agent"] = [
            {"role": "user", "content": "问题"},
            {"role": "assistant", "content": "回答"}
        ]
        
        service.clear_history("test_agent")
        
        history = service.get_history("test_agent")
        assert len(history) == 0
    
    @patch('services.ask_service.urllib.request.urlopen')
    @patch('services.ask_service.os.getenv')
    @patch('services.ask_service.Path.exists')
    @patch('services.ask_service.yaml.safe_load')
    def test_history_limit(self, mock_yaml_load, mock_exists, mock_getenv, mock_urlopen):
        """测试历史长度限制"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {"agents": {}}
        mock_getenv.return_value = "sk-test-key"
        
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "回答"}}]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        service = AskService()
        
        # 发送 15 条消息（会超过 20 条限制）
        for i in range(15):
            service.chat(f"问题{i}", "test_agent")
        
        history = service.get_history("test_agent")
        
        # 最多 20 条
        assert len(history) <= 20


class TestAskServiceLLMCall:
    """测试 LLM 调用"""
    
    @patch('services.ask_service.urllib.request.urlopen')
    @patch('services.ask_service.os.getenv')
    @patch('services.ask_service.Path.exists')
    @patch('services.ask_service.yaml.safe_load')
    def test_call_llm_request_format(self, mock_yaml_load, mock_exists, mock_getenv, mock_urlopen):
        """测试 LLM 请求格式"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {"agents": {}}
        mock_getenv.return_value = "sk-test-key"
        
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "回答"}}]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        service = AskService()
        service._call_llm("用户问题", "系统提示词")
        
        # 验证请求被调用
        assert mock_urlopen.called
        
        # 验证请求参数
        call_args = mock_urlopen.call_args
        request_obj = call_args[0][0]
        
        assert request_obj.get_full_url() == "https://coding.dashscope.aliyuncs.com/v1/chat/completions"
        assert "Authorization" in request_obj.headers
        assert "Bearer sk-test-key" in request_obj.headers["Authorization"]
    
    @patch('services.ask_service.urllib.request.urlopen')
    @patch('services.ask_service.os.getenv')
    @patch('services.ask_service.Path.exists')
    @patch('services.ask_service.yaml.safe_load')
    def test_call_llm_timeout(self, mock_yaml_load, mock_exists, mock_getenv, mock_urlopen):
        """测试超时设置"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {"agents": {}}
        mock_getenv.return_value = "sk-test-key"
        
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "回答"}}]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        service = AskService()
        service._call_llm("问题", "提示词", timeout=60)
        
        # 验证 timeout 参数
        call_args = mock_urlopen.call_args
        assert call_args[1]["timeout"] == 60
    
    @patch('services.ask_service.urllib.request.urlopen')
    @patch('services.ask_service.os.getenv')
    @patch('services.ask_service.Path.exists')
    @patch('services.ask_service.yaml.safe_load')
    def test_call_llm_empty_response(self, mock_yaml_load, mock_exists, mock_getenv, mock_urlopen):
        """测试空响应处理"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {"agents": {}}
        mock_getenv.return_value = "sk-test-key"
        
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": []  # 空 choices
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        service = AskService()
        result = service._call_llm("问题", "提示词")
        
        assert result == "抱歉，我无法回答这个问题。"


class TestAskServiceAgents:
    """测试 Agent 管理"""
    
    @patch('services.ask_service.os.getenv')
    @patch('services.ask_service.Path.exists')
    @patch('services.ask_service.yaml.safe_load')
    def test_get_available_agents(self, mock_yaml_load, mock_exists, mock_getenv):
        """测试获取可用 Agent"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {
            "agents": {
                "agent1": {
                    "enabled": True,
                    "role": "专家 1",
                    "layer": 1
                },
                "agent2": {
                    "enabled": False,  # 禁用
                    "role": "专家 2",
                    "layer": 2
                },
                "agent3": {
                    "enabled": True,
                    "role": "专家 3",
                    "layer": 3
                }
            }
        }
        mock_getenv.return_value = "sk-test-key"
        
        service = AskService()
        agents = service.get_available_agents()
        
        # 只返回启用的 Agent
        assert len(agents) == 2
        assert agents[0]["name"] == "agent1"
        assert agents[1]["name"] == "agent3"


class TestSingleton:
    """测试单例模式"""
    
    @patch('services.ask_service.os.getenv')
    @patch('services.ask_service.Path.exists')
    @patch('services.ask_service.yaml.safe_load')
    def test_get_ask_service_singleton(self, mock_yaml_load, mock_exists, mock_getenv):
        """测试单例模式"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {"agents": {}}
        mock_getenv.return_value = "sk-test-key"
        
        # 重置单例
        from services import ask_service
        ask_service._instance = None
        
        service1 = get_ask_service()
        service2 = get_ask_service()
        
        assert service1 is service2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
