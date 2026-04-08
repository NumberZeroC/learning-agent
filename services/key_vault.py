#!/usr/bin/env python3
"""
Key Vault - API Key 加密存储（密钥保险箱）

核心功能：
- 使用 Fernet 对称加密存储 API Key
- 主密钥从环境变量读取（不落地）
- 支持多 Provider Key 管理
- Key 前缀用于前端显示

使用示例：
    vault = KeyVault()
    vault.save_key('dashscope', 'sk-sp-xxx')
    key = vault.get_key('dashscope')
"""

import os
import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from contextlib import contextmanager

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠️  cryptography 未安装，Key Vault 将使用明文存储（不安全！）")
    print("   安装：pip install cryptography")


logger = logging.getLogger('key_vault')


class KeyVaultError(Exception):
    """Key Vault 异常"""
    pass


class KeyVault:
    """
    API Key 保险箱
    
    安全特性：
    - Fernet 加密存储
    - 主密钥从环境变量读取
    - 支持 Key 轮换
    - 完整的审计日志
    """
    
    def __init__(self, db_path: str = None):
        """
        初始化 Key Vault
        
        Args:
            db_path: SQLite 数据库路径，默认 data/secrets.db
        """
        if not CRYPTO_AVAILABLE:
            logger.warning("⚠️  cryptography 不可用，将使用明文存储（不安全！）")
            self.fernet = None
        else:
            # 初始化 Fernet 加密
            self._init_master_key()
        
        # 数据库路径
        if db_path is None:
            project_dir = Path(__file__).parent.parent
            db_path = project_dir / "data" / "secrets.db"
        self.db_path = Path(db_path)
        
        # 初始化数据库
        self._init_database()
        
        logger.info(f"✅ Key Vault 初始化完成 (数据库：{self.db_path})")
    
    def _init_master_key(self):
        """初始化主密钥"""
        master_key = os.getenv('LEARNING_AGENT_MASTER_KEY')
        
        if not master_key:
            # 首次运行：生成并提示
            if CRYPTO_AVAILABLE:
                master_key = Fernet.generate_key().decode()
                logger.warning("⚠️  首次运行，已生成主密钥，请保存到环境变量：")
                logger.warning(f"   LEARNING_AGENT_MASTER_KEY={master_key}")
                logger.warning("   然后重启服务")
                # 临时使用（仅首次）
                self.fernet = Fernet(master_key.encode())
                self._temp_master_key = master_key
            else:
                self.fernet = None
        else:
            try:
                self.fernet = Fernet(master_key.encode())
                logger.info("✅ 主密钥已加载")
            except Exception as e:
                raise KeyVaultError(f"主密钥无效：{e}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    @contextmanager
    def _get_db(self):
        """数据库上下文管理器"""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        """初始化数据库表"""
        with self._get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_secrets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider VARCHAR(50) NOT NULL UNIQUE,
                    encrypted_key BLOB NOT NULL,
                    key_prefix VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS key_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action VARCHAR(50) NOT NULL,
                    provider VARCHAR(50),
                    user_ip VARCHAR(50),
                    user_agent TEXT,
                    result VARCHAR(20),
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_provider ON api_secrets(provider)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_action ON key_audit_log(action)')
            
            logger.info("✅ 数据库表初始化完成")
    
    def _encrypt(self, api_key: str) -> bytes:
        """加密 API Key"""
        if self.fernet is None:
            # 降级：返回明文（不安全！）
            logger.warning("⚠️  使用明文存储（不安全！）")
            return api_key.encode()
        return self.fernet.encrypt(api_key.encode())
    
    def _decrypt(self, encrypted_key: bytes) -> str:
        """解密 API Key"""
        if self.fernet is None:
            # 降级：返回明文（不安全！）
            return encrypted_key.decode()
        return self.fernet.decrypt(encrypted_key).decode()
    
    def _generate_prefix(self, api_key: str) -> str:
        """生成 Key 前缀用于显示（如 sk-sp11***3434）"""
        if not api_key or len(api_key) < 16:
            return "***"
        # 显示前 8 位和后 4 位
        return f"{api_key[:8]}***{api_key[-4:]}"
    
    def _log_audit(self, action: str, provider: str, result: str, 
                   details: Dict = None, user_ip: str = None, user_agent: str = None):
        """记录审计日志"""
        try:
            with self._get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO key_audit_log 
                    (action, provider, user_ip, user_agent, result, details)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    action, provider, user_ip, user_agent, result,
                    json.dumps(details) if details else None
                ))
        except Exception as e:
            logger.error(f"审计日志记录失败：{e}")
    
    def save_key(self, provider: str, api_key: str, 
                 user_ip: str = None, user_agent: str = None) -> str:
        """
        保存 API Key（加密存储）
        
        Args:
            provider: Provider 名称（如 'dashscope', 'openai'）
            api_key: API Key 明文
            user_ip: 用户 IP（用于审计）
            user_agent: User-Agent（用于审计）
        
        Returns:
            str: Key 前缀（用于前端显示）
        """
        try:
            encrypted_key = self._encrypt(api_key)
            key_prefix = self._generate_prefix(api_key)
            
            with self._get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO api_secrets 
                    (provider, encrypted_key, key_prefix, updated_at, is_active)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, 1)
                ''', (provider, encrypted_key, key_prefix))
            
            # 审计日志
            self._log_audit(
                action='key_update',
                provider=provider,
                result='success',
                details={'key_prefix': key_prefix},
                user_ip=user_ip,
                user_agent=user_agent
            )
            
            logger.info(f"✅ 已保存 {provider} 的 API Key (前缀：{key_prefix})")
            return key_prefix
            
        except Exception as e:
            # 审计日志
            self._log_audit(
                action='key_update',
                provider=provider,
                result='failed',
                details={'error': str(e)},
                user_ip=user_ip,
                user_agent=user_agent
            )
            
            logger.error(f"❌ 保存 {provider} API Key 失败：{e}")
            raise KeyVaultError(f"保存 API Key 失败：{e}")
    
    def get_key(self, provider: str) -> Optional[str]:
        """
        获取 API Key（解密后返回）
        
        Args:
            provider: Provider 名称
        
        Returns:
            str: API Key 明文，如果不存在则返回 None
        """
        try:
            with self._get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT encrypted_key, is_active FROM api_secrets
                    WHERE provider = ?
                ''', (provider,))
                
                row = cursor.fetchone()
                if row and row['is_active']:
                    api_key = self._decrypt(row['encrypted_key'])
                    
                    # 更新最后使用时间
                    cursor.execute('''
                        UPDATE api_secrets SET last_used_at = CURRENT_TIMESTAMP
                        WHERE provider = ?
                    ''', (provider,))
                    
                    return api_key
                return None
                
        except Exception as e:
            logger.error(f"获取 {provider} API Key 失败：{e}")
            return None
    
    def get_key_prefix(self, provider: str) -> Optional[str]:
        """
        获取 Key 前缀（用于前端显示）
        
        Args:
            provider: Provider 名称
        
        Returns:
            str: Key 前缀，如果不存在则返回 None
        """
        try:
            with self._get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT key_prefix, is_active FROM api_secrets
                    WHERE provider = ?
                ''', (provider,))
                
                row = cursor.fetchone()
                if row and row['is_active']:
                    return row['key_prefix']
                return None
                
        except Exception as e:
            logger.error(f"获取 {provider} Key 前缀失败：{e}")
            return None
    
    def delete_key(self, provider: str, 
                   user_ip: str = None, user_agent: str = None) -> bool:
        """
        删除 API Key
        
        Args:
            provider: Provider 名称
            user_ip: 用户 IP
            user_agent: User-Agent
        
        Returns:
            bool: 是否成功删除
        """
        try:
            with self._get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE api_secrets SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE provider = ?
                ''', (provider,))
                
                deleted = cursor.rowcount > 0
            
            # 审计日志
            self._log_audit(
                action='key_delete',
                provider=provider,
                result='success' if deleted else 'not_found',
                user_ip=user_ip,
                user_agent=user_agent
            )
            
            if deleted:
                logger.info(f"✅ 已删除 {provider} 的 API Key")
            else:
                logger.warning(f"⚠️  {provider} 的 API Key 不存在")
            
            return deleted
            
        except Exception as e:
            # 审计日志
            self._log_audit(
                action='key_delete',
                provider=provider,
                result='failed',
                details={'error': str(e)},
                user_ip=user_ip,
                user_agent=user_agent
            )
            
            logger.error(f"❌ 删除 {provider} API Key 失败：{e}")
            raise KeyVaultError(f"删除 API Key 失败：{e}")
    
    def is_key_configured(self, provider: str) -> bool:
        """
        检查是否已配置 API Key
        
        Args:
            provider: Provider 名称
        
        Returns:
            bool: 是否已配置
        """
        prefix = self.get_key_prefix(provider)
        return prefix is not None
    
    def list_providers(self) -> List[Dict]:
        """
        列出所有已配置的 Provider
        
        Returns:
            List[Dict]: Provider 列表
        """
        try:
            with self._get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT provider, key_prefix, created_at, updated_at, last_used_at
                    FROM api_secrets WHERE is_active = 1
                ''')
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"列出 Provider 失败：{e}")
            return []
    
    def get_audit_logs(self, limit: int = 100, 
                       provider: str = None) -> List[Dict]:
        """
        获取审计日志
        
        Args:
            limit: 限制数量
            provider: 过滤 Provider
        
        Returns:
            List[Dict]: 审计日志列表
        """
        try:
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                if provider:
                    cursor.execute('''
                        SELECT * FROM key_audit_log
                        WHERE provider = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    ''', (provider, limit))
                else:
                    cursor.execute('''
                        SELECT * FROM key_audit_log
                        ORDER BY created_at DESC
                        LIMIT ?
                    ''', (limit,))
                
                logs = []
                for row in cursor.fetchall():
                    log = dict(row)
                    # 解析 details JSON
                    if log.get('details'):
                        try:
                            log['details'] = json.loads(log['details'])
                        except:
                            pass
                    logs.append(log)
                
                return logs
                
        except Exception as e:
            logger.error(f"获取审计日志失败：{e}")
            return []


# 全局单例
_vault_instance: Optional[KeyVault] = None


def get_key_vault() -> KeyVault:
    """获取 Key Vault 单例"""
    global _vault_instance
    if _vault_instance is None:
        _vault_instance = KeyVault()
    return _vault_instance


def init_secrets_db():
    """初始化 secrets 数据库（部署脚本使用）"""
    vault = KeyVault()
    logger.info("✅ Secrets 数据库初始化完成")


if __name__ == '__main__':
    # 测试
    logging.basicConfig(level=logging.INFO)
    
    print("🔐 Key Vault 测试")
    print("=" * 50)
    
    vault = KeyVault()
    
    # 测试保存
    prefix = vault.save_key('test_provider', 'sk-test-123456789')
    print(f"✅ 保存 Key: {prefix}")
    
    # 测试获取
    key = vault.get_key('test_provider')
    print(f"✅ 获取 Key: {key}")
    
    # 测试前缀
    prefix = vault.get_key_prefix('test_provider')
    print(f"✅ Key 前缀：{prefix}")
    
    # 测试检查
    configured = vault.is_key_configured('test_provider')
    print(f"✅ 已配置：{configured}")
    
    # 测试删除
    vault.delete_key('test_provider')
    print(f"✅ 删除 Key")
    
    configured = vault.is_key_configured('test_provider')
    print(f"✅ 已配置：{configured}")
