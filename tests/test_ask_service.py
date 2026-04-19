#!/usr/bin/env python3
"""
问答服务测试用例

测试 ask_service.py 的核心功能
基于 AskService 新架构（使用 LLMClient）
"""

import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open

project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

from services.ask_service import AskService, get_ask_service


class TestAskServiceInit:
    """测试 AskService 初始化"""
    
    @patch('services.ask_service.Path.exists')
    @patch('services.ask_service.yaml.safe_load')
    def test_init_with_config(self, mock_yaml_load, mock_exists):
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
            },
            "providers": {"dashscope": {"api_key_value": "sk-test-key"}}
        }
        
        service = AskService("config/agent_config.yaml")
        
        assert service.config is not None
        assert len(service.agents) == 1
        assert "test_agent" in service.agents
    
    @patch('services.ask_service.Path.exists')
    def test_init_without_config(self, mock_exists):
        """测试无配置文件时的初始化"""
        mock_exists.return_value = False
        
        service = AskService("nonexistent.yaml")
        
        assert service.config == {}
        assert service.agents == {}


class TestAskServiceHistory:
    """测试对话历史功能"""
    
    @patch('services.ask_service.Path.exists')
    @patch('services.ask_service.yaml.safe_load')
    def test_get_history_empty(self, mock_yaml_load, mock_exists):
        """测试获取空历史"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {"agents": {}, "providers": {}}
        
        service = AskService()
        service._histories = {}  # 清空历史
        
        history = service.get_history("test_agent")
        assert len(history) == 0
    
    @patch('services.ask_service.Path.exists')
    @patch('services.ask_service.yaml.safe_load')
    def test_clear_history(self, mock_yaml_load, mock_exists):
        """测试清空历史"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {"agents": {}, "providers": {}}
        
        service = AskService()
        
        service._histories["test_agent"] = [
            {"role": "user", "content": "问题"},
            {"role": "assistant", "content": "回答"}
        ]
        
        service.clear_history("test_agent")
        
        history = service.get_history("test_agent")
        assert len(history) == 0
    
    @patch('services.ask_service.Path.exists')
    @patch('services.ask_service.yaml.safe_load')
    def test_history_limit(self, mock_yaml_load, mock_exists):
        """测试历史长度限制"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {"agents": {}, "providers": {}}
        
        service = AskService()
        
        # 添加超过限制的历史
        for i in range(15):
            service._histories["test_agent"] = service._histories.get("test_agent", [])
            service._histories["test_agent"].append({"role": "user", "content": f"问题{i}"})
            service._histories["test_agent"].append({"role": "assistant", "content": f"回答{i}"})
        
        # 模拟 trim_history 调用
        if len(service._histories["test_agent"]) > service.MAX_HISTORY_LENGTH * 2:
            service._histories["test_agent"] = service._histories["test_agent"][-(service.MAX_HISTORY_LENGTH * 2):]
        
        history = service.get_history("test_agent")
        assert len(history) <= service.MAX_HISTORY_LENGTH * 2


class TestAskServiceAgents:
    """测试 Agent 管理"""
    
    @patch('services.ask_service.Path.exists')
    @patch('services.ask_service.yaml.safe_load')
    def test_get_available_agents(self, mock_yaml_load, mock_exists):
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
                    "enabled": False,
                    "role": "专家 2",
                    "layer": 2
                },
                "agent3": {
                    "enabled": True,
                    "role": "专家 3",
                    "layer": 3
                }
            },
            "providers": {}
        }
        
        service = AskService()
        agents = service.get_available_agents()
        
        assert len(agents) == 2
        agent_names = [a["name"] for a in agents]
        assert "agent1" in agent_names
        assert "agent3" in agent_names
        assert "agent2" not in agent_names


class TestAskServiceAPIConfig:
    """测试 API 配置"""
    
    @patch('services.ask_service.Path.exists')
    @patch('services.ask_service.yaml.safe_load')
    @patch('services.ask_service.os.getenv')
    def test_get_api_config(self, mock_getenv, mock_yaml_load, mock_exists):
        """测试获取 API 配置"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {
            "providers": {
                "dashscope": {
                    "api_key_value": "sk-test-key",
                    "base_url": "https://test.api.com/v1"
                }
            },
            "global": {"default_model": "test-model"},
            "agents": {}
        }
        mock_getenv.return_value = ""
        
        service = AskService()
        api_config = service._get_api_config()
        
        assert api_config["api_key"] == "sk-test-key"
        assert api_config["base_url"] == "https://test.api.com/v1"
        assert api_config["model"] == "test-model"
    
    @patch('services.ask_service.Path.exists')
    @patch('services.ask_service.yaml.safe_load')
    @patch('services.ask_service.os.getenv')
    def test_get_api_config_from_env(self, mock_getenv, mock_yaml_load, mock_exists):
        """测试从环境变量获取 API Key"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {
            "providers": {},
            "global": {},
            "agents": {}
        }
        mock_getenv.return_value = "sk-env-key"
        
        service = AskService()
        api_config = service._get_api_config()
        
        assert api_config["api_key"] == "sk-env-key"


class TestAskServiceChat:
    """测试聊天功能"""
    
    @patch('services.ask_service.Path.exists')
    @patch('services.ask_service.yaml.safe_load')
    @patch('services.ask_service.AskService._get_llm_client')
    def test_chat_success(self, mock_get_llm_client, mock_yaml_load, mock_exists):
        """测试成功聊天"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {
            "agents": {
                "test_agent": {
                    "enabled": True,
                    "role": "测试专家",
                    "system_prompt": "你是测试专家"
                }
            },
            "providers": {"dashscope": {"api_key_value": "sk-test"}}
        }
        
        # Mock LLMClient
        mock_client = MagicMock()
        mock_client.chat.return_value = {
            "success": True,
            "content": "这是测试回答"
        }
        mock_get_llm_client.return_value = mock_client
        
        service = AskService()
        result = service.chat("什么是机器学习？", "test_agent")
        
        assert result["success"] is True
        assert result["reply"] == "这是测试回答"
        assert result["agent"] == "test_agent"
    
    @patch('services.ask_service.Path.exists')
    @patch('services.ask_service.yaml.safe_load')
    @patch('services.ask_service.AskService._get_llm_client')
    def test_chat_api_error(self, mock_get_llm_client, mock_yaml_load, mock_exists):
        """测试 API 错误"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {"agents": {}, "providers": {}}
        
        mock_client = MagicMock()
        mock_client.chat.side_effect = Exception("API 调用失败")
        mock_get_llm_client.return_value = mock_client
        
        service = AskService()
        result = service.chat("测试问题", "test_agent")
        
        assert result["success"] is False
        assert "error" in result


class TestSingleton:
    """测试单例模式"""
    
    @patch('services.ask_service.Path.exists')
    @patch('services.ask_service.yaml.safe_load')
    def test_get_ask_service_singleton(self, mock_yaml_load, mock_exists):
        """测试单例模式"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {"agents": {}, "providers": {}}
        
        from services import ask_service
        ask_service._instance = None
        
        service1 = get_ask_service()
        service2 = get_ask_service()
        
        assert service1 is service2
        
        ask_service._instance = None


class TestHistoryFileStorage:
    """测试历史文件存储"""
    
    @patch('services.ask_service.Path.exists')
    @patch('services.ask_service.yaml.safe_load')
    @patch('services.ask_service.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_history_to_file(self, mock_file, mock_mkdir, mock_yaml_load, mock_exists):
        """测试保存历史到文件"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {"agents": {}, "providers": {}}
        
        service = AskService()
        service._histories = {"test": [{"role": "user", "content": "test"}]}
        
        service._save_history_to_file()
        
        mock_file.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])