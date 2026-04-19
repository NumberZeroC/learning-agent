#!/usr/bin/env python3
"""
Learning Agent 集成测试用例

测试核心组件的基本功能，不依赖外部 API
"""

import sys
import json
import unittest
from pathlib import Path

project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

import os
os.environ['LEARNING_AGENT_MASTER_KEY'] = '6BV4wL6i1u5NyCiExVH_GljmHbir0rADVUlsjMOsQYQ=='


class TestKeyVault(unittest.TestCase):
    """KeyVault 集成测试"""
    
    def test_01_keyvault_init(self):
        """测试 KeyVault 初始化"""
        from services.key_vault import get_key_vault
        vault = get_key_vault()
        self.assertIsNotNone(vault)
    
    def test_02_keyvault_configured(self):
        """测试 API Key 配置状态"""
        from services.key_vault import get_key_vault
        vault = get_key_vault()
        self.assertTrue(vault.is_key_configured('dashscope'))
    
    def test_03_keyvault_prefix(self):
        """测试 Key 前缀获取"""
        from services.key_vault import get_key_vault
        vault = get_key_vault()
        prefix = vault.get_key_prefix('dashscope')
        self.assertIsNotNone(prefix)
        self.assertIn('sk-', prefix)
        self.assertIn('***', prefix)


class TestAskService(unittest.TestCase):
    """Ask Service 集成测试"""
    
    def test_01_ask_service_init(self):
        """测试 Ask Service 初始化"""
        from services.ask_service import AskService
        service = AskService()
        self.assertIsNotNone(service)
    
    def test_02_ask_service_agents(self):
        """测试 Agent 配置"""
        from services.ask_service import AskService
        service = AskService()
        agents = service.get_available_agents()
        self.assertIsNotNone(agents)
        self.assertIsInstance(agents, list)


class TestWorkflowAPI(unittest.TestCase):
    """工作流 API 集成测试"""
    
    def test_01_check_workflow_script(self):
        """测试工作流脚本检查"""
        from web.routes.workflow_run_routes import check_workflow_script
        result = check_workflow_script()
        self.assertTrue(result['ok'], f"脚本检查失败：{result.get('error', '')}")
    
    def test_02_get_workflow_status(self):
        """测试工作流状态获取"""
        from web.routes.workflow_run_routes import get_workflow_status
        status = get_workflow_status()
        self.assertIn('running', status)
        self.assertIn('status', status)


class TestConfigRoutes(unittest.TestCase):
    """配置路由集成测试"""
    
    def test_01_get_providers_config(self):
        """测试获取 Provider 配置"""
        from web.routes.config_routes import get_providers_config
        from flask import Flask
        
        app = Flask(__name__)
        with app.test_request_context():
            response = get_providers_config()
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertIn('dashscope', data['data'])


def run_tests():
    """运行所有测试"""
    print('=' * 60)
    print('🧪 Learning Agent 集成测试')
    print('=' * 60)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestKeyVault))
    suite.addTests(loader.loadTestsFromTestCase(TestAskService))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigRoutes))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print('\n' + '=' * 60)
    print('📊 测试总结')
    print('=' * 60)
    print(f'✅ 通过：{result.testsRun - len(result.failures) - len(result.errors)}')
    print(f'❌ 失败：{len(result.failures)}')
    print(f'⚠️  错误：{len(result.errors)}')
    
    return len(result.failures) + len(result.errors) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)