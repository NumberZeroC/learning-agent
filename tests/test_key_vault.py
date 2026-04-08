#!/usr/bin/env python3
"""
KeyVault 测试用例

测试 API Key 加密存储功能
"""

import os
import sys
import pytest
from pathlib import Path

# 项目路径
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

from services.key_vault import KeyVault, KeyVaultError


class TestKeyVault:
    """KeyVault 测试类"""
    
    @pytest.fixture
    def vault(self, tmp_path):
        """创建测试用的 KeyVault 实例"""
        from cryptography.fernet import Fernet
        
        # 生成有效的测试主密钥
        test_master_key = Fernet.generate_key().decode()
        os.environ['LEARNING_AGENT_MASTER_KEY'] = test_master_key
        
        db_path = tmp_path / "test_secrets.db"
        vault = KeyVault(db_path=str(db_path))
        
        yield vault
        
        # 清理
        if db_path.exists():
            db_path.unlink()
    
    def test_init(self, vault):
        """测试初始化"""
        assert vault is not None
        assert vault.db_path.exists()
    
    def test_save_key(self, vault):
        """测试保存 API Key"""
        prefix = vault.save_key('test_provider', 'sk-test-123456789')
        
        assert prefix is not None
        assert 'sk-test' in prefix
        assert '***' in prefix
    
    def test_get_key(self, vault):
        """测试获取 API Key"""
        original_key = 'sk-test-123456789'
        vault.save_key('test_provider', original_key)
        
        retrieved_key = vault.get_key('test_provider')
        
        assert retrieved_key == original_key
    
    def test_get_key_prefix(self, vault):
        """测试获取 Key 前缀"""
        vault.save_key('test_provider', 'sk-test-123456789')
        
        prefix = vault.get_key_prefix('test_provider')
        
        assert prefix is not None
        assert 'sk-test' in prefix
        assert '***' in prefix
    
    def test_is_key_configured(self, vault):
        """测试检查是否已配置"""
        assert vault.is_key_configured('test_provider') == False
        
        vault.save_key('test_provider', 'sk-test-123456789')
        
        assert vault.is_key_configured('test_provider') == True
    
    def test_delete_key(self, vault):
        """测试删除 API Key"""
        vault.save_key('test_provider', 'sk-test-123456789')
        
        deleted = vault.delete_key('test_provider')
        
        assert deleted == True
        assert vault.is_key_configured('test_provider') == False
    
    def test_delete_nonexistent_key(self, vault):
        """测试删除不存在的 Key"""
        deleted = vault.delete_key('nonexistent_provider')
        
        assert deleted == False
    
    def test_list_providers(self, vault):
        """测试列出所有 Provider"""
        vault.save_key('provider1', 'sk-test-1')
        vault.save_key('provider2', 'sk-test-2')
        
        providers = vault.list_providers()
        
        assert len(providers) == 2
        provider_names = [p['provider'] for p in providers]
        assert 'provider1' in provider_names
        assert 'provider2' in provider_names
    
    def test_audit_log(self, vault):
        """测试审计日志"""
        vault.save_key('test_provider', 'sk-test-123456789', 
                      user_ip='127.0.0.1', user_agent='TestAgent')
        
        logs = vault.get_audit_logs(provider='test_provider')
        
        assert len(logs) > 0
        assert logs[0]['action'] == 'key_update'
        assert logs[0]['result'] == 'success'
    
    def test_key_format_validation(self, vault):
        """测试 Key 格式验证（前缀生成）"""
        # 短 Key
        prefix = vault._generate_prefix('sk-short')
        assert '***' in prefix
        
        # 标准 Key
        prefix = vault._generate_prefix('sk-test-123456789')
        assert 'sk-test' in prefix
        assert '***' in prefix
        
        # 空 Key
        prefix = vault._generate_prefix('')
        assert prefix == '***'
    
    def test_multiple_providers(self, vault):
        """测试多 Provider 管理"""
        providers = ['dashscope', 'openai', 'deepseek']
        keys = ['sk-ds-123', 'sk-oi-456', 'sk-ds-789']
        
        for provider, key in zip(providers, keys):
            vault.save_key(provider, key)
        
        for provider, key in zip(providers, keys):
            assert vault.is_key_configured(provider) == True
            assert vault.get_key(provider) == key
    
    def test_key_update(self, vault):
        """测试 Key 更新"""
        vault.save_key('test_provider', 'sk-test-old-key')
        old_prefix = vault.get_key_prefix('test_provider')
        
        vault.save_key('test_provider', 'sk-test-new-key-different')
        new_prefix = vault.get_key_prefix('test_provider')
        
        assert vault.get_key('test_provider') == 'sk-test-new-key-different'
        # 前缀可能相同（如果长度和结尾相同），但 Key 应该已更新
        assert vault.get_key('test_provider').endswith('different')
    
    def test_concurrent_access(self, vault):
        """测试并发访问"""
        import threading
        
        results = []
        
        def save_key(provider, key):
            try:
                vault.save_key(provider, key)
                results.append(True)
            except:
                results.append(False)
        
        threads = []
        for i in range(5):
            t = threading.Thread(target=save_key, args=(f'provider_{i}', f'sk-test-{i}'))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert all(results)
        assert vault.list_providers() is not None


class TestKeyVaultEncryption:
    """KeyVault 加密测试"""
    
    def test_encryption_decryption(self):
        """测试加密解密"""
        from cryptography.fernet import Fernet
        
        master_key = Fernet.generate_key()
        fernet = Fernet(master_key)
        
        original = 'sk-test-secret-key'
        encrypted = fernet.encrypt(original.encode())
        decrypted = fernet.decrypt(encrypted).decode()
        
        assert original == decrypted
        assert encrypted != original.encode()
    
    def test_different_keys_produce_different_encryption(self):
        """测试不同密钥产生不同加密结果"""
        from cryptography.fernet import Fernet
        
        key1 = Fernet.generate_key()
        key2 = Fernet.generate_key()
        
        fernet1 = Fernet(key1)
        fernet2 = Fernet(key2)
        
        original = 'sk-test-secret'
        
        encrypted1 = fernet1.encrypt(original.encode())
        encrypted2 = fernet2.encrypt(original.encode())
        
        assert encrypted1 != encrypted2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
