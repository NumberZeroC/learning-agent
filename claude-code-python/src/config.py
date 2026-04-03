"""Configuration loading for CCP"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


def find_env_file(start_path: Path | None = None) -> Path | None:
    """Find .env file in current or parent directories"""
    
    if start_path is None:
        start_path = Path.cwd()
    
    # Check current directory
    env_file = start_path / ".env"
    if env_file.exists():
        return env_file
    
    # Check parent directories (up to root)
    for parent in start_path.parents:
        env_file = parent / ".env"
        if env_file.exists():
            return env_file
    
    # Check home directory
    home_env = Path.home() / ".ccp" / ".env"
    if home_env.exists():
        return home_env
    
    return None


def load_env_file(env_file: Path) -> dict[str, str]:
    """Load environment variables from .env file"""
    
    env_vars = {}
    
    try:
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                
                # Parse KEY=VALUE
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    
                    env_vars[key] = value
        
        logger.info("Loaded environment from file", path=env_file, count=len(env_vars))
        
    except Exception as e:
        logger.warning("Failed to load .env file", path=env_file, error=str(e))
    
    return env_vars


def load_config() -> dict[str, Any]:
    """
    Load configuration from multiple sources.
    
    Priority (highest to lowest):
    1. Current environment variables
    2. .env file in current directory
    3. .env file in home directory (~/.ccp/.env)
    """
    
    config = {}
    
    # Find and load .env file
    env_file = find_env_file()
    if env_file:
        file_vars = load_env_file(env_file)
        config.update(file_vars)
        logger.debug("Loaded from .env file", path=env_file)
    
    # Override with current environment
    for key in ["USE_ALIYUN", "DASHSCOPE_API_KEY", "ALIYUN_API_KEY", "ANTHROPIC_API_KEY"]:
        env_value = os.environ.get(key)
        if env_value:
            config[key] = env_value
    
    return config


def get_api_config() -> dict[str, str | bool]:
    """
    Get API configuration with provider detection.
    
    Returns:
        Dictionary with provider info and API key
    """
    
    config = load_config()
    
    # Determine provider
    use_aliyun = config.get("USE_ALIYUN", "").lower() in ("1", "true", "yes")
    aliyun_key = config.get("DASHSCOPE_API_KEY") or config.get("ALIYUN_API_KEY")
    anthropic_key = config.get("ANTHROPIC_API_KEY")
    
    # Auto-detect if no preference
    if not use_aliyun and not anthropic_key and aliyun_key:
        use_aliyun = True
    
    result = {
        "use_aliyun": use_aliyun,
        "provider": "aliyun" if use_aliyun else "anthropic",
        "api_key": aliyun_key if use_aliyun else anthropic_key,
        "configured": bool(aliyun_key if use_aliyun else anthropic_key),
    }
    
    return result


def print_config_summary() -> None:
    """Print configuration summary"""
    
    config = get_api_config()
    
    print("📋 Configuration Summary")
    print("=" * 40)
    print(f"Provider: {'Aliyun (通义千问)' if config['use_aliyun'] else 'Anthropic'}")
    print(f"API Key: {'✅ Set' if config['api_key'] else '❌ Not set'}")
    print(f"Configured: {'✅ Yes' if config['configured'] else '❌ No'}")
    print("=" * 40)
    
    if not config["configured"]:
        print()
        if config["use_aliyun"]:
            print("To configure Aliyun:")
            print("  export DASHSCOPE_API_KEY=sk-xxx")
            print("  # Or add to ~/.bashrc or .env file")
        else:
            print("To configure Anthropic:")
            print("  export ANTHROPIC_API_KEY=sk-ant-xxx")
            print("  # Or use Aliyun:")
            print("  export USE_ALIYUN=1")
            print("  export DASHSCOPE_API_KEY=sk-xxx")


if __name__ == "__main__":
    print_config_summary()
