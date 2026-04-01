#!/usr/bin/env python3
"""
Pytest 配置文件

提供全局的 fixture 和配置
"""

import os
import sys
from pathlib import Path
import pytest

# 添加项目路径
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))


@pytest.fixture
def project_dir_path():
    """项目根目录路径"""
    return project_dir


@pytest.fixture
def config_path(project_dir_path):
    """配置文件路径"""
    return project_dir_path / "config" / "agent_config.yaml"


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock 环境变量"""
    monkeypatch.setenv('DASHSCOPE_API_KEY', 'sk-test-mock-key')
    monkeypatch.setenv('LEARNING_AGENT_TOKEN', 'test-token')


@pytest.fixture
def mock_api_key():
    """Mock API Key"""
    return 'sk-test-mock-key'


@pytest.fixture
def data_dir(project_dir_path):
    """数据目录"""
    return project_dir_path / "data" / "workflow_results"


@pytest.fixture
def sample_workflow_result():
    """示例工作流结果"""
    return {
        "workflow_id": "test_20260331_120000",
        "started_at": "2026-03-31T12:00:00",
        "completed_at": "2026-03-31T12:30:00",
        "total_tasks": 17,
        "success_count": 17,
        "failed_count": 0,
        "layer_results": {
            "1": {
                "layer": 1,
                "layer_name": "基础理论层",
                "agent": "theory_worker",
                "topics": [
                    {
                        "topic_name": "AI 基础",
                        "description": "机器学习和深度学习基础",
                        "subtopics": [
                            {
                                "name": "机器学习概述",
                                "key_points": ["监督学习", "无监督学习", "强化学习"],
                                "difficulty": "beginner"
                            }
                        ]
                    }
                ],
                "task_count": 4
            }
        },
        "duration_seconds": 1800
    }


@pytest.fixture
def sample_chat_message():
    """示例聊天消息"""
    return {
        "message": "什么是机器学习？",
        "agent": "theory_worker"
    }


@pytest.fixture
def sample_llm_response():
    """示例 LLM 响应"""
    return {
        "choices": [
            {
                "message": {
                    "content": "机器学习是人工智能的一个分支，它使计算机能够从数据中学习..."
                }
            }
        ]
    }
