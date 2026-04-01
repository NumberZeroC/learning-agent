#!/usr/bin/env python3
"""
公共配置加载器

功能：从公共配置文件加载 Tushare Token 等共享配置
位置：/home/admin/.openclaw/workspace/config/config_loader.py

使用示例：
    from config_loader import get_tushare_token
    token = get_tushare_token()
    
    # 或
    from config_loader import load_config
    config = load_config('tushare')
"""
import os
import yaml
from pathlib import Path
from typing import Optional, Any, Dict


# 公共配置目录
CONFIG_DIR = Path('/home/admin/.openclaw/workspace/config')


def get_tushare_token() -> Optional[str]:
    """
    获取 Tushare Token
    
    优先级：
    1. 环境变量 TUSHARE_TOKEN
    2. 公共配置文件 /home/admin/.openclaw/workspace/config/tushare.yaml
    3. 返回 None
    
    Returns:
        Tushare Token 字符串，如果未找到则返回 None
    """
    # 1. 尝试从环境变量获取
    token = os.getenv('TUSHARE_TOKEN')
    if token:
        return token
    
    # 2. 尝试从公共配置文件获取
    config_file = CONFIG_DIR / 'tushare.yaml'
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            token = config.get('tushare', {}).get('token')
            if token:
                return token
        except Exception as e:
            print(f"[ConfigLoader] ⚠️ 读取 Tushare 配置失败：{e}")
    
    # 3. 尝试从 stock-notification 配置获取（兼容旧配置）
    legacy_config = Path('/home/admin/.openclaw/workspace/stock-notification/config.yaml')
    if legacy_config.exists():
        try:
            with open(legacy_config, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            token = config.get('tushare', {}).get('token')
            if token:
                return token
        except Exception as e:
            pass
    
    # 4. 尝试从 stock-agent 配置获取
    stock_agent_config = Path('/home/admin/.openclaw/workspace/stock-agent/config.yaml')
    if stock_agent_config.exists():
        try:
            with open(stock_agent_config, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            token = config.get('tushare', {}).get('token')
            if token:
                return token
        except Exception as e:
            pass
    
    return None


def load_config(config_name: str) -> Optional[Dict[str, Any]]:
    """
    加载公共配置
    
    Args:
        config_name: 配置文件名（不含扩展名）
        
    Returns:
        配置字典，如果文件不存在则返回 None
        
    示例：
        tushare_config = load_config('tushare')
        token = tushare_config['tushare']['token']
    """
    config_file = CONFIG_DIR / f"{config_name}.yaml"
    
    if not config_file.exists():
        return None
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"[ConfigLoader] ⚠️ 加载配置失败：{config_file} - {e}")
        return None


def save_config(config_name: str, config: Dict[str, Any]) -> bool:
    """
    保存公共配置
    
    Args:
        config_name: 配置文件名（不含扩展名）
        config: 配置字典
        
    Returns:
        是否保存成功
    """
    config_file = CONFIG_DIR / f"{config_name}.yaml"
    
    try:
        # 确保目录存在
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        # 设置文件权限（仅所有者可读写）
        os.chmod(config_file, 0o600)
        
        return True
    except Exception as e:
        print(f"[ConfigLoader] ⚠️ 保存配置失败：{e}")
        return False


def get_env_with_fallback(var_name: str, config_name: str, *keys) -> Optional[str]:
    """
    获取环境变量，如果不存在则从配置文件获取
    
    Args:
        var_name: 环境变量名
        config_name: 配置文件名
        *keys: 配置字典的键路径
        
    Returns:
        配置值
        
    示例：
        token = get_env_with_fallback('TUSHARE_TOKEN', 'tushare', 'tushare', 'token')
    """
    # 尝试环境变量
    value = os.getenv(var_name)
    if value:
        return value
    
    # 尝试配置文件
    config = load_config(config_name)
    if config:
        for key in keys:
            if isinstance(config, dict):
                config = config.get(key)
            else:
                return None
        return config
    
    return None


# 命令行工具
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'get-token':
            # 获取 Tushare Token
            token = get_tushare_token()
            if token:
                print(token)
            else:
                print("Error: Tushare Token not found", file=sys.stderr)
                sys.exit(1)
        
        elif command == 'test':
            # 测试配置加载
            print("=== 配置加载测试 ===\n")
            
            token = get_tushare_token()
            if token:
                print(f"✅ Tushare Token: {token[:20]}...{token[-10:]}")
            else:
                print("❌ Tushare Token: 未找到")
            
            tushare_config = load_config('tushare')
            if tushare_config:
                print(f"✅ 公共配置文件：已加载")
            else:
                print(f"❌ 公共配置文件：未找到")
        
        else:
            print(f"Unknown command: {command}")
            print("Usage: python config_loader.py [get-token|test]")
            sys.exit(1)
    else:
        # 默认运行测试
        token = get_tushare_token()
        if token:
            print(f"Tushare Token: {token[:20]}...{token[-10:]}")
        else:
            print("Tushare Token not found")
