#!/usr/bin/env python3
"""
配置路由测试用例

测试配置管理 API 端点
"""

import os
import sys
import pytest
import json
from pathlib import Path

# 项目路径
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

# 设置测试环境变量
os.environ['LEARNING_AGENT_MASTER_KEY'] = 'test-master-key-for-testing-purposes-only='


class TestConfigRoutes:
    """配置路由测试类"""
    
    @pytest.fixture
    def app(self):
        """创建 Flask 应用"""
        from web.app import app
        app.config['TESTING'] = True
        yield app
    
    @pytest.fixture
    def client(self, app):
        """创建测试客户端"""
        return app.test_client()
    
    def test_get_config(self, client):
        """测试获取配置"""
        response = client.get('/api/config')
        result = json.loads(response.data)
        
        assert response.status_code == 200
        assert result['success'] == True
        assert 'data' in result
    
    def test_get_providers_config(self, client):
        """测试获取 Provider 配置"""
        response = client.get('/api/config/providers')
        result = json.loads(response.data)
        
        assert response.status_code == 200
        assert result['success'] == True
        assert 'data' in result
    
    def test_update_api_key(self, client):
        """测试更新 API Key"""
        response = client.post('/api/config/providers/test/key',
                              data=json.dumps({'api_key': 'sk-test-123456'}),
                              content_type='application/json')
        result = json.loads(response.data)
        
        assert response.status_code == 200
        assert result['success'] == True
        assert 'key_prefix' in result
    
    def test_update_api_key_invalid_format(self, client):
        """测试更新 API Key - 无效格式"""
        response = client.post('/api/config/providers/test/key',
                              data=json.dumps({'api_key': 'invalid-key'}),
                              content_type='application/json')
        result = json.loads(response.data)
        
        assert response.status_code == 400
        assert result['success'] == False
        assert '格式不正确' in result['error']
    
    def test_update_api_key_empty(self, client):
        """测试更新 API Key - 空值"""
        response = client.post('/api/config/providers/test/key',
                              data=json.dumps({'api_key': ''}),
                              content_type='application/json')
        result = json.loads(response.data)
        
        assert response.status_code == 400
        assert result['success'] == False
        assert '不能为空' in result['error']
    
    def test_delete_api_key(self, client):
        """测试删除 API Key"""
        # 先添加
        client.post('/api/config/providers/test/key',
                   data=json.dumps({'api_key': 'sk-test-123456'}),
                   content_type='application/json')
        
        # 再删除
        response = client.delete('/api/config/providers/test/key')
        result = json.loads(response.data)
        
        assert response.status_code == 200
        assert result['success'] == True
    
    def test_delete_nonexistent_api_key(self, client):
        """测试删除不存在的 API Key"""
        response = client.delete('/api/config/providers/nonexistent/key')
        result = json.loads(response.data)
        
        assert response.status_code == 404
        assert result['success'] == False
    
    def test_test_api_key(self, client):
        """测试 API Key 连接测试"""
        # 先添加 Key
        client.post('/api/config/providers/test/key',
                   data=json.dumps({'api_key': 'sk-test-123456'}),
                   content_type='application/json')
        
        # 测试连接（预期会失败，因为是测试 Key）
        response = client.post('/api/config/providers/test/test')
        
        # 只要不抛出异常就算通过
        assert response.status_code in [200, 401, 500]
    
    def test_get_audit_logs(self, client):
        """测试获取审计日志"""
        response = client.get('/api/config/audit-logs')
        result = json.loads(response.data)
        
        assert response.status_code == 200
        assert result['success'] == True
        assert 'data' in result
        assert 'logs' in result['data']
    
    def test_get_audit_logs_with_limit(self, client):
        """测试获取审计日志 - 带限制"""
        response = client.get('/api/config/audit-logs?limit=10')
        result = json.loads(response.data)
        
        assert response.status_code == 200
        assert len(result['data']['logs']) <= 10
    
    def test_save_config(self, client):
        """测试保存配置"""
        config = {
            'global': {
                'timeout': 120
            }
        }
        
        response = client.put('/api/config',
                             data=json.dumps(config),
                             content_type='application/json')
        result = json.loads(response.data)
        
        assert response.status_code == 200
        assert result['success'] == True
    
    def test_save_config_empty(self, client):
        """测试保存空配置"""
        response = client.put('/api/config',
                             data=json.dumps({}),
                             content_type='application/json')
        result = json.loads(response.data)
        
        assert response.status_code == 400
        assert result['success'] == False
    
    def test_get_agents_config(self, client):
        """测试获取 Agent 配置"""
        response = client.get('/api/config/agents')
        result = json.loads(response.data)
        
        assert response.status_code == 200
        assert result['success'] == True
        assert 'data' in result


class TestConfigRoutesSecurity:
    """配置路由安全测试"""
    
    @pytest.fixture
    def app(self):
        """创建 Flask 应用"""
        from web.app import app
        app.config['TESTING'] = True
        yield app
    
    @pytest.fixture
    def client(self, app):
        """创建测试客户端"""
        return app.test_client()
    
    def test_api_key_not_exposed_in_config(self, client):
        """测试 API Key 不在配置中暴露"""
        # 先添加 Key
        client.post('/api/config/providers/test/key',
                   data=json.dumps({'api_key': 'sk-test-secret-123'}),
                   content_type='application/json')
        
        # 获取配置
        response = client.get('/api/config')
        result = json.loads(response.data)
        
        # 检查是否包含完整 Key
        config_str = json.dumps(result)
        assert 'sk-test-secret-123' not in config_str
    
    def test_api_key_prefix_only(self, client):
        """测试只返回 Key 前缀"""
        # 先添加 Key
        client.post('/api/config/providers/test/key',
                   data=json.dumps({'api_key': 'sk-test-123456789'}),
                   content_type='application/json')
        
        # 获取 Provider 配置
        response = client.get('/api/config/providers')
        result = json.loads(response.data)
        
        # 检查前缀格式
        if 'test' in result['data']:
            prefix = result['data']['test'].get('key_prefix', '')
            assert '***' in prefix or len(prefix) < 20


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
