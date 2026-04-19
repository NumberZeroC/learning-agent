#!/usr/bin/env python3
"""
自定义主题生成器单元测试
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

from custom_topic_generator import CustomTopicGenerator, CustomTopicResult


class TestCustomTopicGenerator:
    """自定义主题生成器测试"""
    
    def test_init(self):
        """测试初始化"""
        generator = CustomTopicGenerator()
        assert generator.config_path.exists()
        assert generator.custom_config_path.exists()
        assert generator.output_dir.name == "custom_topics"
    
    def test_agent_mapping(self):
        """测试 Agent 映射"""
        generator = CustomTopicGenerator()
        
        assert "theory_worker" in generator.AGENT_MAPPING
        assert "tech_stack_worker" in generator.AGENT_MAPPING
        assert "core_skill_worker" in generator.AGENT_MAPPING
        assert "engineering_worker" in generator.AGENT_MAPPING
        assert "interview_worker" in generator.AGENT_MAPPING
        
        assert generator.AGENT_MAPPING["theory_worker"]["layer"] == 1
        assert generator.AGENT_MAPPING["engineering_worker"]["layer"] == 4
    
    def test_classify_by_keywords(self):
        """测试关键词分类"""
        generator = CustomTopicGenerator()
        generator.initialize()
        
        result = generator._classify_by_keywords("算法设计与分析")
        assert result in generator.AGENT_MAPPING
        
        result = generator._classify_by_keywords("Python 编程")
        assert result in generator.AGENT_MAPPING
        
        result = generator._classify_by_keywords("系统架构设计")
        assert result in generator.AGENT_MAPPING
        
        result = generator._classify_by_keywords("项目实战")
        assert result in generator.AGENT_MAPPING
        
        result = generator._classify_by_keywords("面试技巧")
        assert result in generator.AGENT_MAPPING
    
    def test_classify_unknown_topic(self):
        """测试未知主题分类"""
        generator = CustomTopicGenerator()
        generator.initialize()
        
        result = generator._classify_by_keywords("某个随机主题")
        assert result == "core_skill_worker"
    
    def test_build_custom_question(self):
        """测试问题构建"""
        generator = CustomTopicGenerator()
        
        question = generator._build_custom_question("微服务架构", 4, "分布式系统设计")
        assert "微服务架构" in question
        assert "工程实践层" in question
        assert "分布式系统设计" in question
        assert "JSON" in question
    
    def test_build_question_without_description(self):
        """测试无描述的问题构建"""
        generator = CustomTopicGenerator()
        
        question = generator._build_custom_question("机器学习", 1, "")
        assert "机器学习" in question
        assert "基础理论层" in question
    
    def test_parse_knowledge_json(self):
        """测试 JSON 解析"""
        generator = CustomTopicGenerator()
        
        content = '{"topic_name": "测试主题", "description": "测试描述"}'
        result = generator._parse_knowledge(content, "fallback")
        
        assert result["topic_name"] == "测试主题"
        assert result["description"] == "测试描述"
    
    def test_parse_knowledge_with_markdown(self):
        """测试带 Markdown 的 JSON 解析"""
        generator = CustomTopicGenerator()
        
        content = '```json\n{"topic_name": "测试主题"}\n```'
        result = generator._parse_knowledge(content, "fallback")
        
        assert result["topic_name"] == "测试主题"
    
    def test_parse_knowledge_invalid(self):
        """测试无效 JSON 解析"""
        generator = CustomTopicGenerator()
        
        content = "这不是JSON"
        result = generator._parse_knowledge(content, "fallback_name")
        
        assert result["topic_name"] == "fallback_name"
        assert "raw_content" in result
    
    def test_count_keypoints(self):
        """测试知识点计数"""
        generator = CustomTopicGenerator()
        
        knowledge = {
            "subtopics": [
                {"detailed_keypoints": [{"key_point": "kp1"}, {"key_point": "kp2"}]},
                {"detailed_keypoints": [{"key_point": "kp3"}]},
                {"key_points": ["a", "b"]},
            ]
        }
        
        count = generator._count_keypoints(knowledge)
        assert count == 3
    
    def test_count_keypoints_empty(self):
        """测试空知识点计数"""
        generator = CustomTopicGenerator()
        
        knowledge = {"subtopics": []}
        count = generator._count_keypoints(knowledge)
        assert count == 0
    
    def test_save_result(self):
        """测试结果保存"""
        generator = CustomTopicGenerator()
        generator.initialize()
        
        topic_id = "test_001"
        knowledge = {"topic_name": "测试", "data": "value"}
        
        generator._save_result(topic_id, knowledge)
        
        result_file = generator.output_dir / f"{topic_id}.json"
        assert result_file.exists()
        
        with open(result_file, "r", encoding="utf-8") as f:
            saved = json.load(f)
        
        assert saved["topic_name"] == "测试"
        
        result_file.unlink()
    
    def test_update_index(self):
        """测试索引更新"""
        generator = CustomTopicGenerator()
        generator.initialize()
        
        generator._update_index("test_001", "测试主题", "engineering_worker", True)
        
        index_file = generator.output_dir / "custom_topics_index.json"
        assert index_file.exists()
        
        with open(index_file, "r", encoding="utf-8") as f:
            index = json.load(f)
        
        assert "topics" in index
        assert len(index["topics"]) > 0
        
        entry = index["topics"][-1]
        assert entry["topic_id"] == "test_001"
        assert entry["success"] is True
    
    def test_list_custom_topics(self):
        """测试获取主题列表"""
        generator = CustomTopicGenerator()
        generator.initialize()
        
        generator._update_index("list_test_001", "测试1", "theory_worker", True)
        generator._update_index("list_test_002", "测试2", "tech_stack_worker", False, "错误")
        
        topics = generator.list_custom_topics()
        assert len(topics) >= 2
    
    def test_get_custom_topic(self):
        """测试获取主题详情"""
        generator = CustomTopicGenerator()
        generator.initialize()
        
        topic_id = "get_test_001"
        knowledge = {"topic_name": "获取测试", "data": "value"}
        generator._save_result(topic_id, knowledge)
        
        result = generator.get_custom_topic(topic_id)
        assert result is not None
        assert result["topic_name"] == "获取测试"
        
        generator.output_dir.joinpath(f"{topic_id}.json").unlink()
    
    def test_get_custom_topic_not_found(self):
        """测试获取不存在主题"""
        generator = CustomTopicGenerator()
        generator.initialize()
        
        result = generator.get_custom_topic("nonexistent_topic")
        assert result is None


class TestCustomTopicResult:
    """自定义主题结果测试"""
    
    def test_result_dataclass(self):
        """测试结果数据类"""
        result = CustomTopicResult(
            topic_id="test_001",
            topic_name="测试主题",
            agent="engineering_worker",
            success=True,
            knowledge={"topic_name": "测试"},
            created_at="2026-04-19T10:00:00",
            keypoint_count=5,
        )
        
        assert result.topic_id == "test_001"
        assert result.topic_name == "测试主题"
        assert result.agent == "engineering_worker"
        assert result.success is True
        assert result.keypoint_count == 5
    
    def test_failed_result(self):
        """测试失败结果"""
        result = CustomTopicResult(
            topic_id="test_002",
            topic_name="失败测试",
            agent="theory_worker",
            success=False,
            error="API 调用失败",
            created_at="2026-04-19T10:00:00",
        )
        
        assert result.success is False
        assert result.error == "API 调用失败"
        assert result.knowledge is None


@pytest.mark.integration
class TestCustomTopicGeneratorIntegration:
    """集成测试（需要 API Key）"""
    
    @pytest.mark.skipif(
        not os.getenv("DASHSCOPE_API_KEY"),
        reason="需要配置 DASHSCOPE_API_KEY"
    )
    def test_generate_with_api(self):
        """测试真实生成（需要 API Key）"""
        generator = CustomTopicGenerator()
        generator.initialize()
        
        result = generator.generate(
            topic="测试主题",
            agent="theory_worker",
            skip_details=True,
            skip_relation=True,
        )
        
        assert result.topic_id.startswith("custom_")
        assert result.topic_name == "测试主题"
        
        if result.success:
            assert result.knowledge is not None
            assert "topic_name" in result.knowledge


if __name__ == "__main__":
    pytest.main([__file__, "-v"])