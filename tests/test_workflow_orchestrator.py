#!/usr/bin/env python3
"""
工作流编排器测试用例

测试 workflow_orchestrator.py 的核心功能
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

from workflow_orchestrator import AsyncSubAgent, WorkflowOrchestrator, Task, WorkflowResult
from services.llm_client import LLMClient


class TestAsyncSubAgent:
    """测试 AsyncSubAgent 类"""
    
    def test_async_sub_agent_init(self):
        """测试 AsyncSubAgent 初始化"""
        agent = AsyncSubAgent(
            name="test_agent",
            role="测试专家",
            layer=1,
            system_prompt="你是测试专家",
            model="qwen3.5-plus",
            api_key="sk-test-key",
            base_url="https://test.api.com/v1"
        )
        
        assert agent.name == "test_agent"
        assert agent.role == "测试专家"
        assert agent.layer == 1
        # 验证使用了 LLMClient
        assert hasattr(agent, 'llm_client')
        assert agent.llm_client is not None
    
    @patch.object(LLMClient, 'async_chat')
    def test_ask_success(self, mock_async_chat):
        """测试成功调用 LLM"""
        pytest.skip("异步测试需要AsyncMock，Python 3.6不完全支持")
    
    @patch.object(LLMClient, 'async_chat')
    def test_ask_api_error(self, mock_async_chat):
        """测试 LLM 错误处理"""
        pytest.skip("异步测试需要AsyncMock，Python 3.6不完全支持")
    
    @patch.object(LLMClient, 'async_chat')
    def test_ask_retry_mechanism(self, mock_async_chat):
        """测试重试机制（LLMClient 内部处理）"""
        pytest.skip("异步测试需要AsyncMock，Python 3.6不完全支持")


class TestWorkflowOrchestrator:
    """测试 WorkflowOrchestrator 类"""
    
    @patch('workflow_orchestrator.WorkflowOrchestrator._load_config')
    def test_orchestrator_init(self, mock_load_config):
        """测试编排器初始化"""
        mock_load_config.return_value = {
            "providers": {
                "dashscope": {
                    "api_key_value": "sk-test-key"
                }
            },
            "agents": {}
        }
        
        orchestrator = WorkflowOrchestrator("config/agent_config.yaml")
        
        assert orchestrator.config_path.name == "agent_config.yaml"
        assert orchestrator.tasks == []
        assert orchestrator.results == {}
    
    @patch('workflow_orchestrator.WorkflowOrchestrator._load_config')
    def test_create_tasks(self, mock_load_config):
        """测试任务创建"""
        mock_load_config.return_value = {
            "providers": {"dashscope": {"api_key_value": "sk-test-key"}},
            "agents": {}
        }
        
        orchestrator = WorkflowOrchestrator()
        orchestrator._create_tasks()
        
        # 应该有 20 个任务（5 层架构，每层 4 个主题）
        assert len(orchestrator.tasks) == 20
        
        # 检查任务分布
        layer_counts = {}
        for task in orchestrator.tasks:
            layer_counts[task.layer_num] = layer_counts.get(task.layer_num, 0) + 1
        
        assert layer_counts[1] == 4  # 第 1 层 4 个主题
        assert layer_counts[2] == 4  # 第 2 层 4 个主题
        assert layer_counts[3] == 4  # 第 3 层 4 个主题
        assert layer_counts[4] == 4  # 第 4 层 4 个主题
        assert layer_counts[5] == 4  # 第 5 层 4 个主题
    
    def test_build_question_format(self):
        """测试问题构建格式"""
        orchestrator = WorkflowOrchestrator.__new__(WorkflowOrchestrator)
        orchestrator.architecture = {"layers": []}
        
        question = orchestrator._build_question("AI 基础", 1)
        
        # 验证基本要素
        assert "AI 基础" in question  # 主题名称
        assert "JSON" in question  # 输出格式要求
        assert "subtopics" in question  # 包含子主题
        assert "key_points" in question  # 包含知识点
    
    def test_parse_knowledge_valid_json(self):
        """测试解析有效的 JSON"""
        orchestrator = WorkflowOrchestrator.__new__(WorkflowOrchestrator)
        orchestrator.architecture = {"layers": []}
        
        content = '''
        {
            "topic_name": "AI 基础",
            "description": "测试描述",
            "subtopics": []
        }
        '''
        
        result = orchestrator._parse_knowledge(content, "AI 基础")
        
        assert result["topic_name"] == "AI 基础"
        assert result["description"] == "测试描述"
    
    def test_parse_knowledge_invalid_json(self):
        """测试解析无效的 JSON（容错）"""
        orchestrator = WorkflowOrchestrator.__new__(WorkflowOrchestrator)
        orchestrator.architecture = {"layers": []}
        
        content = "这不是有效的 JSON"
        
        result = orchestrator._parse_knowledge(content, "AI 基础")
        
        # 应该返回 fallback 结构
        assert result["topic_name"] == "AI 基础"
        assert "raw_content" in result or "description" in result
    
    @patch('workflow_orchestrator.AsyncSubAgent')
    @patch('workflow_orchestrator.WorkflowOrchestrator._load_config')
    def test_execute_task_success(self, mock_load_config, mock_async_sub_agent):
        """测试任务执行成功（异步版本需要跳过）"""
        pytest.skip("异步任务执行测试需要更复杂的mock设置，暂跳过")
    
    @patch('workflow_orchestrator.WorkflowOrchestrator._load_config')
    def test_save_task_result(self, mock_load_config, tmp_path):
        """测试保存任务结果"""
        mock_load_config.return_value = {
            "providers": {"dashscope": {"api_key_value": "sk-test-key"}},
            "agents": {}
        }
        
        orchestrator = WorkflowOrchestrator()
        orchestrator.output_dir = tmp_path
        
        task_data = {
            "topic_name": "测试主题",
            "description": "测试描述"
        }
        
        orchestrator._save_task_result(1, 1, task_data)
        
        # 检查文件是否创建
        task_file = tmp_path / "layer_1_task_1.json"
        assert task_file.exists()
        
        # 验证内容
        with open(task_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert saved_data["layer"] == 1
        assert saved_data["task_index"] == 1
        assert saved_data["data"]["topic_name"] == "测试主题"
    
    @patch('workflow_orchestrator.WorkflowOrchestrator._load_config')
    def test_merge_layer_results(self, mock_load_config, tmp_path):
        """测试层结果合并"""
        mock_load_config.return_value = {
            "providers": {"dashscope": {"api_key_value": "sk-test-key"}},
            "agents": {}
        }
        
        orchestrator = WorkflowOrchestrator()
        orchestrator.output_dir = tmp_path
        
        layer_result = {
            "layer_name": "测试层",
            "agent": "test_agent",
            "topics": [
                {"topic_name": "主题 1"},
                {"topic_name": "主题 2"}
            ]
        }
        
        orchestrator._merge_layer_results(1, layer_result)
        
        # 检查合并文件
        merged_file = tmp_path / "layer_1_workflow.json"
        assert merged_file.exists()
        
        with open(merged_file, 'r', encoding='utf-8') as f:
            merged_data = json.load(f)
        
        assert merged_data["layer"] == 1
        assert merged_data["task_count"] == 2


class TestWorkflowResult:
    """测试 WorkflowResult 数据类"""
    
    def test_workflow_result_creation(self):
        """测试工作流结果创建"""
        result = WorkflowResult(
            workflow_id="test_workflow",
            started_at="2026-03-31T12:00:00",
            completed_at="2026-03-31T12:30:00",
            total_tasks=17,
            success_count=17,
            failed_count=0,
            layer_results={"1": {"layer": 1}},
            duration_seconds=1800
        )
        
        assert result.workflow_id == "test_workflow"
        assert result.total_tasks == 17
        assert result.success_count == 17
        assert result.failed_count == 0


class TestIntegration:
    """集成测试"""
    
    @patch('workflow_orchestrator.AsyncSubAgent')
    @patch('workflow_orchestrator.WorkflowOrchestrator._load_config')
    def test_full_workflow_mock(self, mock_load_config, mock_async_sub_agent, tmp_path):
        """测试完整工作流（全 Mock，异步版本需要跳过）"""
        pytest.skip("异步完整工作流测试需要更复杂的mock设置，暂跳过")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
