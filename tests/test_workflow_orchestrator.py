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

from workflow_orchestrator import SubAgent, WorkflowOrchestrator, Task, WorkflowResult
from services.llm_client import LLMClient


class TestSubAgent:
    """测试 SubAgent 类"""
    
    def test_sub_agent_init(self):
        """测试 SubAgent 初始化"""
        agent = SubAgent(
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
    
    @patch.object(LLMClient, 'chat')
    def test_ask_success(self, mock_chat):
        """测试成功调用 LLM"""
        # Mock LLMClient 响应
        mock_chat.return_value = {
            "success": True,
            "content": "这是测试回答",
            "usage": {"total_tokens": 100}
        }
        
        agent = SubAgent(
            name="test_agent",
            role="测试专家",
            layer=1,
            system_prompt="你是测试专家",
            api_key="sk-test-key",
            base_url="https://test.api.com/v1"
        )
        
        result = agent.ask("测试问题", timeout=30)
        
        assert result["success"] is True
        assert result["content"] == "这是测试回答"
        assert result["agent"] == "test_agent"
        mock_chat.assert_called_once()
    
    @patch.object(LLMClient, 'chat')
    def test_ask_api_error(self, mock_chat):
        """测试 LLM 错误处理"""
        # Mock LLMClient 错误
        mock_chat.return_value = {
            "success": False,
            "error": "API 调用失败"
        }
        
        agent = SubAgent(
            name="test_agent",
            role="测试专家",
            layer=1,
            system_prompt="你是测试专家",
            api_key="sk-test-key",
            base_url="https://test.api.com/v1"
        )
        
        result = agent.ask("测试问题", max_retries=1, timeout=30)
        
        assert result["success"] is False
        assert "error" in result
    
    @patch.object(LLMClient, 'chat')
    def test_ask_retry_mechanism(self, mock_chat):
        """测试重试机制（LLMClient 内部处理）"""
        # Mock LLMClient 响应（重试由 LLMClient 内部处理）
        mock_chat.return_value = {
            "success": True,
            "content": "重试后成功",
            "usage": {"total_tokens": 100}
        }
        
        agent = SubAgent(
            name="test_agent",
            role="测试专家",
            layer=1,
            system_prompt="你是测试专家",
            api_key="sk-test-key",
            base_url="https://test.api.com/v1"
        )
        
        result = agent.ask("测试问题", max_retries=3)
        
        # 验证调用了 LLMClient
        assert mock_chat.called
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
        
        # 应该有 17 个任务（5 层架构）
        assert len(orchestrator.tasks) == 17
        
        # 检查任务分布
        layer_counts = {}
        for task in orchestrator.tasks:
            layer_counts[task.layer_num] = layer_counts.get(task.layer_num, 0) + 1
        
        assert layer_counts[1] == 4  # 第 1 层 4 个主题
        assert layer_counts[2] == 3  # 第 2 层 3 个主题
        assert layer_counts[3] == 4  # 第 3 层 4 个主题
        assert layer_counts[4] == 3  # 第 4 层 3 个主题
        assert layer_counts[5] == 3  # 第 5 层 3 个主题
    
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
    
    @patch('workflow_orchestrator.SubAgent')
    @patch('workflow_orchestrator.WorkflowOrchestrator._load_config')
    def test_execute_task_success(self, mock_load_config, mock_sub_agent):
        """测试任务执行成功"""
        mock_load_config.return_value = {
            "providers": {"dashscope": {"api_key_value": "sk-test-key"}},
            "agents": {}
        }
        
        # Mock Agent 返回成功
        mock_agent = Mock()
        mock_agent.ask.return_value = {
            "success": True,
            "content": '{"topic_name": "测试", "subtopics": []}'
        }
        
        orchestrator = WorkflowOrchestrator()
        task = Task(
            task_id="test_task",
            layer_num=1,
            topic_name="测试主题",
            status="pending"
        )
        
        layer_result = {"topics": []}
        
        orchestrator._execute_task(task, mock_agent, layer_result, 1, 4)
        
        assert task.status == "completed"
        assert task.result is not None
        assert len(layer_result["topics"]) == 1
    
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
    
    @patch('workflow_orchestrator.SubAgent')
    @patch('workflow_orchestrator.WorkflowOrchestrator._load_config')
    def test_full_workflow_mock(self, mock_load_config, mock_sub_agent, tmp_path):
        """测试完整工作流（全 Mock）"""
        mock_load_config.return_value = {
            "providers": {"dashscope": {"api_key_value": "sk-test-key"}},
            "agents": {
                "theory_worker": {
                    "enabled": True,
                    "layer": 1,
                    "role": "理论专家",
                    "system_prompt": "测试",
                    "model": "qwen3.5-plus"
                }
            }
        }
        
        # Mock Agent 返回
        mock_agent = Mock()
        mock_agent.ask.return_value = {
            "success": True,
            "content": '{"topic_name": "测试", "subtopics": [], "description": "测试"}'
        }
        mock_agent.name = "theory_worker"
        mock_agent.layer = 1
        mock_agent.role = "理论专家"
        mock_sub_agent.return_value = mock_agent
        
        orchestrator = WorkflowOrchestrator()
        orchestrator.output_dir = tmp_path
        orchestrator.initialize()
        
        # 只测试第 1 层
        layer_tasks = [t for t in orchestrator.tasks if t.layer_num == 1]
        layer_results = {}
        
        orchestrator._execute_layer(1, layer_tasks, mock_agent, layer_results)
        
        # 验证结果
        assert "1" in layer_results
        assert len(layer_results["1"]["topics"]) > 0
        
        # 验证文件已保存
        merged_file = tmp_path / "layer_1_workflow.json"
        assert merged_file.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
