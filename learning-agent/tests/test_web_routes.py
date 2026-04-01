#!/usr/bin/env python3
"""
Web API 路由测试用例

测试 chat_routes.py 和 workflow_routes.py
使用 Mock 替代真实的服务调用
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


class TestChatRoutes:
    """测试聊天路由"""
    
    @patch('web.routes.chat_routes.get_ask_service')
    def test_send_message_success(self, mock_get_service):
        """测试发送消息成功"""
        # Mock AskService
        mock_service = Mock()
        mock_service.chat.return_value = {
            "success": True,
            "reply": "这是测试回答",
            "agent": "test_agent",
            "timestamp": "2026-03-31T12:00:00"
        }
        mock_get_service.return_value = mock_service
        
        # 导入并创建测试客户端
        from web.app import app
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            response = client.post(
                '/api/chat/send',
                json={
                    "message": "什么是机器学习？",
                    "agent": "test_agent"
                },
                content_type='application/json'
            )
            
            data = json.loads(response.data)
            
            assert response.status_code == 200
            assert data["success"] is True
            assert data["reply"] == "这是测试回答"
            mock_service.chat.assert_called_once()
    
    @patch('web.routes.chat_routes.get_ask_service')
    def test_send_message_empty_message(self, mock_get_service):
        """测试空消息"""
        from web.app import app
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            response = client.post(
                '/api/chat/send',
                json={"message": ""},
                content_type='application/json'
            )
            
            data = json.loads(response.data)
            
            assert response.status_code == 400
            assert data["success"] is False
            assert "为空" in data["error"]
    
    @patch('web.routes.chat_routes.get_ask_service')
    def test_send_message_missing_message(self, mock_get_service):
        """测试缺少消息字段"""
        from web.app import app
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            response = client.post(
                '/api/chat/send',
                json={"agent": "test_agent"},
                content_type='application/json'
            )
            
            data = json.loads(response.data)
            
            assert response.status_code == 400
            assert data["success"] is False
    
    @patch('web.routes.chat_routes.get_ask_service')
    def test_send_message_empty_json(self, mock_get_service):
        """测试空 JSON"""
        from web.app import app
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            response = client.post(
                '/api/chat/send',
                json={},
                content_type='application/json'
            )
            
            data = json.loads(response.data)
            
            assert response.status_code == 400
            assert data["success"] is False
    
    @patch('web.routes.chat_routes.get_ask_service')
    def test_get_history(self, mock_get_service):
        """测试获取对话历史"""
        mock_service = Mock()
        mock_service.get_history.return_value = [
            {"role": "user", "content": "问题 1", "timestamp": "2026-03-31T12:00:00"},
            {"role": "assistant", "content": "回答 1", "timestamp": "2026-03-31T12:00:01"}
        ]
        mock_get_service.return_value = mock_service
        
        from web.app import app
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            response = client.get('/api/chat/history?agent=test_agent&limit=10')
            
            data = json.loads(response.data)
            
            assert response.status_code == 200
            assert data["success"] is True
            assert len(data["data"]["history"]) == 2
            assert data["data"]["agent"] == "test_agent"


class TestWorkflowRoutes:
    """测试工作流路由"""
    
    @patch('web.routes.workflow_routes.WORKFLOW_RESULTS_DIR')
    def test_get_all_layers(self, mock_results_dir, tmp_path):
        """测试获取所有层"""
        # 创建测试数据
        mock_results_dir.exists.return_value = True
        mock_results_dir.glob.return_value = []
        
        from web.app import app
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            response = client.get('/api/workflow/layers')
            
            data = json.loads(response.data)
            
            assert response.status_code == 200
            assert data["success"] is True
            assert "layers" in data["data"]
    
    @patch('web.routes.workflow_routes.WORKFLOW_RESULTS_DIR')
    def test_get_layer_success(self, mock_results_dir, tmp_path):
        """测试获取单层成功"""
        # 创建测试文件
        test_file = tmp_path / "layer_1_workflow.json"
        test_data = {
            "layer": 1,
            "layer_name": "测试层",
            "topics": [{"topic_name": "主题 1"}]
        }
        test_file.write_text(json.dumps(test_data, ensure_ascii=False))
        
        mock_results_dir.exists.return_value = True
        mock_results_dir.__truediv__.return_value = test_file
        mock_results_dir.glob.return_value = [test_file]
        
        from web.app import app
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            response = client.get('/api/workflow/layer/1')
            
            data = json.loads(response.data)
            
            assert response.status_code == 200
            assert data["success"] is True
            assert data["data"]["layer"] == 1
    
    @patch('web.routes.workflow_routes.WORKFLOW_RESULTS_DIR')
    def test_get_layer_not_found(self, mock_results_dir):
        """测试获取不存在的层"""
        mock_results_dir.exists.return_value = True
        mock_results_dir.__truediv__.return_value.exists.return_value = False
        
        from web.app import app
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            response = client.get('/api/workflow/layer/99')
            
            data = json.loads(response.data)
            
            assert response.status_code == 404
            assert data["success"] is False
    
    @patch('web.routes.workflow_routes.WORKFLOW_RESULTS_DIR')
    def test_get_topic_success(self, mock_results_dir, tmp_path):
        """测试获取主题成功"""
        # 创建测试文件
        test_file = tmp_path / "layer_1_workflow.json"
        test_data = {
            "layer": 1,
            "topics": [
                {"topic_name": "主题 1"},
                {"topic_name": "主题 2"}
            ]
        }
        test_file.write_text(json.dumps(test_data, ensure_ascii=False))
        
        mock_results_dir.exists.return_value = True
        mock_results_dir.__truediv__.return_value = test_file
        
        from web.app import app
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            response = client.get('/api/workflow/topic/1/0')
            
            data = json.loads(response.data)
            
            assert response.status_code == 200
            assert data["success"] is True
            assert data["data"]["topic_name"] == "主题 1"
    
    @patch('web.routes.workflow_routes.WORKFLOW_RESULTS_DIR')
    def test_get_topic_index_out_of_range(self, mock_results_dir, tmp_path):
        """测试主题索引超出范围"""
        test_file = tmp_path / "layer_1_workflow.json"
        test_data = {
            "layer": 1,
            "topics": [{"topic_name": "主题 1"}]
        }
        test_file.write_text(json.dumps(test_data, ensure_ascii=False))
        
        mock_results_dir.exists.return_value = True
        mock_results_dir.__truediv__.return_value = test_file
        
        from web.app import app
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            response = client.get('/api/workflow/topic/1/99')
            
            data = json.loads(response.data)
            
            assert response.status_code == 404
            assert data["success"] is False
    
    @patch('web.routes.workflow_routes.WORKFLOW_RESULTS_DIR')
    def test_get_workflow_status(self, mock_results_dir):
        """测试获取工作流状态"""
        mock_results_dir.exists.return_value = True
        mock_results_dir.glob.return_value = []
        
        from web.app import app
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            response = client.get('/api/workflow/status')
            
            data = json.loads(response.data)
            
            assert response.status_code == 200
            assert data["success"] is True
            assert "running" in data["data"]
            assert "completed_tasks" in data["data"]
    
    @patch('web.routes.workflow_routes.WORKFLOW_RESULTS_DIR')
    def test_get_workflow_summary(self, mock_results_dir, tmp_path):
        """测试获取工作流汇总"""
        # 创建测试文件
        test_file = tmp_path / "workflow_summary.json"
        test_data = {
            "total_workflows": 5,
            "total_tasks": 85,
            "total_success": 80,
            "total_failed": 5
        }
        test_file.write_text(json.dumps(test_data, ensure_ascii=False))
        
        mock_results_dir.exists.return_value = True
        mock_results_dir.__truediv__.return_value = test_file
        mock_results_dir.glob.return_value = []
        
        from web.app import app
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            response = client.get('/api/workflow/summary')
            
            data = json.loads(response.data)
            
            assert response.status_code == 200
            assert data["success"] is True
            assert "total_layers" in data["data"]


class TestAppRoutes:
    """测试主应用路由"""
    
    def test_health_check(self):
        """测试健康检查接口"""
        from web.app import app
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            response = client.get('/health')
            
            data = json.loads(response.data)
            
            assert response.status_code == 200
            assert data["status"] == "healthy"
            assert "timestamp" in data
            assert data["version"] == "1.0.0"
    
    @patch('web.app.DATA_DIR')
    def test_api_summary_success(self, mock_data_dir, tmp_path):
        """测试获取汇总成功"""
        test_file = tmp_path / "workflow_summary.json"
        test_data = {"total_workflows": 5}
        test_file.write_text(json.dumps(test_data, ensure_ascii=False))
        
        mock_data_dir.__truediv__.return_value = test_file
        mock_data_dir.exists.return_value = True
        
        from web.app import app
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            response = client.get('/api/summary')
            
            data = json.loads(response.data)
            
            assert response.status_code == 200
            assert data["total_workflows"] == 5
    
    @patch('web.app.DATA_DIR')
    def test_api_summary_not_found(self, mock_data_dir):
        """测试汇总文件不存在"""
        mock_data_dir.__truediv__.return_value.exists.return_value = False
        
        from web.app import app
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            response = client.get('/api/summary')
            
            data = json.loads(response.data)
            
            assert response.status_code == 404
            assert "error" in data


class TestPageRoutes:
    """测试页面路由"""
    
    def test_index_page(self):
        """测试首页"""
        from web.app import app
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
    
    def test_chat_page(self):
        """测试聊天页面"""
        from web.app import app
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            response = client.get('/chat')
            assert response.status_code == 200
    
    def test_layer_page(self):
        """测试层级页面"""
        from web.app import app
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            response = client.get('/layer/1')
            assert response.status_code == 200
    
    def test_topic_page(self):
        """测试主题页面"""
        from web.app import app
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            response = client.get('/topic/1/0')
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
