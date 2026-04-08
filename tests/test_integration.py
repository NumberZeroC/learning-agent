#!/usr/bin/env python3
"""
Learning Agent 集成测试用例

测试所有用户接口，确保功能正常后再打包镜像
"""

import sys
import json
import unittest
from pathlib import Path
from io import StringIO

# 项目路径
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

# 设置测试环境变量（必须在导入 KeyVault 之前）
import os
os.environ['LEARNING_AGENT_MASTER_KEY'] = '6BV4wL6i1u5NyCiExVH_GljmHbir0rADVUlsjMOsQYQ=='

# 强制清除 KeyVault 缓存
if 'services.key_vault' in sys.modules:
    del sys.modules['services.key_vault']
    from services.key_vault import _vault_instance
    import services.key_vault
    services.key_vault._vault_instance = None


class TestKeyVault(unittest.TestCase):
    """KeyVault 集成测试"""
    
    def test_01_keyvault_init(self):
        """测试 KeyVault 初始化"""
        from services.key_vault import get_key_vault
        vault = get_key_vault()
        self.assertIsNotNone(vault)
        print('✅ KeyVault 初始化成功')
    
    def test_02_keyvault_configured(self):
        """测试 API Key 配置状态"""
        from services.key_vault import get_key_vault
        vault = get_key_vault()
        self.assertTrue(vault.is_key_configured('dashscope'))
        print('✅ dashscope 已配置')
    
    def test_03_keyvault_prefix(self):
        """测试 Key 前缀获取"""
        from services.key_vault import get_key_vault
        vault = get_key_vault()
        prefix = vault.get_key_prefix('dashscope')
        self.assertIsNotNone(prefix)
        self.assertIn('sk-', prefix)
        self.assertIn('***', prefix)
        print(f'✅ Key 前缀：{prefix}')
    
    def test_04_keyvault_get_key(self):
        """测试获取 API Key"""
        from services.key_vault import get_key_vault
        vault = get_key_vault()
        key = vault.get_key('dashscope')
        self.assertIsNotNone(key)
        self.assertTrue(key.startswith('sk-'))
        print(f'✅ API Key 获取成功，长度：{len(key)}')


class TestAskService(unittest.TestCase):
    """Ask Service 集成测试"""
    
    def test_01_ask_service_init(self):
        """测试 Ask Service 初始化"""
        from services.ask_service import AskService
        service = AskService()
        self.assertIsNotNone(service)
        print('✅ Ask Service 初始化成功')
    
    def test_02_ask_service_api_config(self):
        """测试 API 配置获取"""
        from services.ask_service import AskService
        service = AskService()
        config = service._get_api_config()
        self.assertIsNotNone(config)
        self.assertIn('api_key', config)
        self.assertIsNotNone(config['api_key'])
        print(f'✅ API Key 获取成功，前缀：{config["api_key"][:15]}...')


class TestWorkflowAPI(unittest.TestCase):
    """工作流 API 集成测试"""
    
    def test_01_check_api_config(self):
        """测试 API 配置检查"""
        from web.routes.workflow_run_routes import check_api_config
        result = check_api_config()
        self.assertEqual(result['ok'], True, f"API 配置检查失败：{result.get('error', '')}")
        print('✅ API 配置检查通过')
    
    def test_02_check_workflow_script(self):
        """测试工作流脚本检查"""
        from web.routes.workflow_run_routes import check_workflow_script
        result = check_workflow_script()
        self.assertTrue(result['ok'], f"脚本检查失败：{result.get('error', '')}")
        print(f'✅ 工作流脚本存在：{result["path"]}')
    
    def test_03_get_workflow_status(self):
        """测试工作流状态获取"""
        from web.routes.workflow_run_routes import get_workflow_status
        status = get_workflow_status()
        self.assertIn('running', status)
        self.assertIn('status', status)
        print(f'✅ 工作流状态：{status["status"]}')


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
            print('✅ Provider 配置获取成功')
    
    def test_02_test_api_key(self):
        """测试 API Key 连接（可选，需要网络）"""
        from web.routes.config_routes import test_api_key
        from flask import Flask
        
        app = Flask(__name__)
        with app.test_request_context():
            response = test_api_key('dashscope')
            data = json.loads(response.data)
            # 404 或 500 可能是网络问题，不视为失败
            if response.status_code == 200:
                print('✅ API 连接测试成功')
            else:
                print(f'⚠️  API 连接测试返回：{data.get("error", "未知错误")}')


class TestFullWorkflow(unittest.TestCase):
    """完整工作流集成测试"""
    
    def test_01_full_check(self):
        """测试完整启动前检查"""
        from web.routes.workflow_run_routes import check_api_config, check_workflow_script, get_workflow_status
        
        # 1. 检查 API 配置
        api_result = check_api_config()
        self.assertTrue(api_result['ok'], f"API 配置检查失败：{api_result.get('error', '')}")
        
        # 2. 检查工作流脚本
        script_result = check_workflow_script()
        self.assertTrue(script_result['ok'], f"脚本检查失败：{script_result.get('error', '')}")
        
        # 3. 检查工作流状态
        status = get_workflow_status()
        self.assertFalse(status['running'], "工作流已在运行中")
        
        print('✅ 完整启动前检查通过')
        print(f'   - API 配置：{api_result["message"] if "message" in api_result else "OK"}')
        print(f'   - 工作流脚本：{script_result["path"]}')
        print(f'   - 工作流状态：{status["status"]}')


def run_tests():
    """运行所有测试"""
    print('=' * 60)
    print('🧪 Learning Agent 集成测试')
    print('=' * 60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestKeyVault))
    suite.addTests(loader.loadTestsFromTestCase(TestAskService))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigRoutes))
    suite.addTests(loader.loadTestsFromTestCase(TestFullWorkflow))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出总结
    print('\n' + '=' * 60)
    print('📊 测试总结')
    print('=' * 60)
    print(f'✅ 通过：{result.testsRun - len(result.failures) - len(result.errors)}')
    print(f'❌ 失败：{len(result.failures)}')
    print(f'⚠️  错误：{len(result.errors)}')
    print(f'📝 总计：{result.testsRun}')
    
    if result.failures:
        print('\n❌ 失败详情:')
        for test, traceback in result.failures:
            print(f'  - {test}: {traceback.split(chr(10))[-2]}')
    
    if result.errors:
        print('\n⚠️  错误详情:')
        for test, traceback in result.errors:
            print(f'  - {test}: {traceback.split(chr(10))[-2]}')
    
    return len(result.failures) + len(result.errors) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
