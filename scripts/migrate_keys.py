#!/usr/bin/env python3
"""
API Key 迁移脚本

将旧配置中的明文 API Key 迁移到 KeyVault 加密存储
"""

import sys
import yaml
from pathlib import Path

# 项目路径
script_dir = Path(__file__).parent
project_dir = script_dir.parent
sys.path.insert(0, str(project_dir))


def migrate_keys():
    """迁移 API Key 到 KeyVault"""
    print("🔐 API Key 迁移工具")
    print("=" * 60)
    
    config_path = project_dir / "config" / "agent_config.yaml"
    
    if not config_path.exists():
        print(f"❌ 配置文件不存在：{config_path}")
        return False
    
    print(f"📄 配置文件：{config_path}")
    
    # 读取配置
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    providers = config.get('providers', {})
    migrated = []
    
    # 初始化 KeyVault
    print("\n🔑 初始化 KeyVault...")
    try:
        from services.key_vault import get_key_vault
        vault = get_key_vault()
        print("✅ KeyVault 已初始化")
    except Exception as e:
        print(f"❌ KeyVault 初始化失败：{e}")
        print("   请先安装依赖：pip install cryptography")
        return False
    
    # 迁移每个 Provider 的 Key
    print("\n🔄 开始迁移 API Key...")
    for provider_name, provider_config in providers.items():
        api_key = provider_config.get('api_key_value', '')
        
        if api_key:
            print(f"\n  📌 {provider_name}:")
            print(f"     当前 Key 前缀：{api_key[:10]}...")
            
            # 检查是否已存在
            if vault.is_key_configured(provider_name):
                existing_prefix = vault.get_key_prefix(provider_name)
                print(f"     ⚠️  KeyVault 中已存在：{existing_prefix}")
                
                # 询问是否覆盖
                response = input("     是否覆盖？(y/N): ").strip().lower()
                if response != 'y':
                    print(f"     ⏭️  跳过")
                    continue
            
            # 保存到 KeyVault
            try:
                prefix = vault.save_key(provider_name, api_key)
                print(f"     ✅ 已迁移到 KeyVault (前缀：{prefix})")
                migrated.append(provider_name)
            except Exception as e:
                print(f"     ❌ 迁移失败：{e}")
    
    # 从配置文件移除明文 Key
    if migrated:
        print("\n🧹 清理配置文件中的明文 Key...")
        for provider_name in migrated:
            if provider_name in providers:
                if 'api_key_value' in providers[provider_name]:
                    del providers[provider_name]['api_key_value']
                    print(f"     ✅ 已移除 {provider_name} 的明文 Key")
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        
        print(f"\n✅ 配置文件已更新")
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 迁移总结:")
    print(f"   成功迁移：{len(migrated)} 个 Provider")
    if migrated:
        print(f"   Provider 列表：{', '.join(migrated)}")
    
    if migrated:
        print("\n⚠️  重要提示:")
        print("   1. 请重启服务使更改生效：sudo systemctl restart learning-agent")
        print("   2. 请备份主密钥（如果尚未保存）:")
        print("      echo $LEARNING_AGENT_MASTER_KEY")
        print("   3. 建议检查审计日志：tail -f logs/config_audit.log")
    
    print("\n✅ 迁移完成！")
    return True


def generate_master_key():
    """生成主密钥"""
    print("🔑 生成主密钥")
    print("=" * 60)
    
    try:
        from cryptography.fernet import Fernet
        master_key = Fernet.generate_key().decode()
        
        print("\n✅ 主密钥已生成:")
        print(f"\nLEARNING_AGENT_MASTER_KEY={master_key}\n")
        print("⚠️  重要提示:")
        print("   1. 请将此 Key 保存到 .env 文件")
        print("   2. 请妥善保管，不要泄露")
        print("   3. 如果丢失，所有加密的 API Key 将无法解密")
        print("\n保存命令:")
        print(f"   echo 'LEARNING_AGENT_MASTER_KEY={master_key}' >> .env")
        
    except ImportError:
        print("❌ cryptography 未安装")
        print("   安装：pip install cryptography")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--generate-key':
        generate_master_key()
    else:
        migrate_keys()
