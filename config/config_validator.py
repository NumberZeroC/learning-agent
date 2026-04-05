#!/usr/bin/env python3
"""
配置验证器（基于 Pydantic）

提供配置文件的 Schema 验证，确保：
- 配置格式正确
- 参数在有效范围内
- 必填字段存在
- 类型正确

支持：
- 配置验证
- 配置迁移（版本升级）
- 默认值填充
"""

from pydantic import BaseModel, Field, field_validator, ValidationError, ConfigDict
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================
# 配置模型
# ============================================

class ProviderConfig(BaseModel):
    """LLM 提供者配置"""
    enabled: bool = True
    api_key_env: str = ""
    api_key_value: str = ""
    base_url: str = "https://api.dashscope.aliyuncs.com/v1"
    models: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('base_url 必须是有效的 HTTP/HTTPS URL')
        return v


class AgentLLMConfig(BaseModel):
    """Agent LLM 配置"""
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4000, ge=1, le=32000)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    
    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v):
        if not 0 <= v <= 2:
            raise ValueError('temperature 必须在 0 到 2 之间')
        return v


class AgentConfig(BaseModel):
    """Agent 配置"""
    enabled: bool = True
    role: str = "助手"
    description: str = ""
    layer: int = Field(default=0, ge=0)
    model: str = "qwen-plus"
    provider: str = "dashscope"
    system_prompt: str = ""
    tools: List[str] = Field(default_factory=list)
    llm_config: Optional[AgentLLMConfig] = None
    
    @field_validator('layer')
    @classmethod
    def validate_layer(cls, v):
        if not 0 <= v <= 10:
            raise ValueError('layer 必须在 0 到 10 之间')
        return v


class HotReloadConfig(BaseModel):
    """热更新配置"""
    enabled: bool = True
    auto_apply: bool = True
    check_interval: int = Field(default=10, ge=1, le=3600)
    backup_enabled: bool = True
    backup_dir: str = "config/backups"
    log_changes: bool = True
    log_file: str = "logs/config_changes.log"
    config_file: str = "config/agent_config.yaml"


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = Field(default="INFO")
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "logs/app.log"
    max_size: int = Field(default=10485760, ge=1024)  # 10MB
    backup_count: int = Field(default=5, ge=1, le=100)
    console: bool = True
    
    @field_validator('level')
    @classmethod
    def validate_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'日志级别必须是 {valid_levels} 之一')
        return v.upper()


class CacheConfig(BaseModel):
    """缓存配置"""
    enabled: bool = True
    backend: str = "memory"  # memory, redis
    max_size: int = Field(default=1000, ge=1)
    ttl: int = Field(default=14400, ge=0)  # 秒


class PerformanceConfig(BaseModel):
    """性能配置"""
    max_concurrent_agents: int = Field(default=6, ge=1, le=50)
    agent_timeout: int = Field(default=120, ge=10, le=600)
    cache: Optional[CacheConfig] = None


class ToolConfig(BaseModel):
    """工具配置"""
    enabled: bool = True


class ToolsConfig(BaseModel):
    """工具集合配置"""
    web_search: Optional[ToolConfig] = None
    code_execution: Optional[Dict[str, Any]] = None
    file_operations: Optional[Dict[str, Any]] = None
    calculator: Optional[ToolConfig] = None


class GlobalConfig(BaseModel):
    """全局配置"""
    cache_enabled: bool = False
    max_retries: int = Field(default=3, ge=0, le=10)
    timeout: int = Field(default=180, ge=10, le=600)


class AppConfig(BaseModel):
    """应用配置根模型"""
    version: str = Field(default="1.0.0")
    updated_at: Optional[str] = None
    
    providers: Dict[str, ProviderConfig] = Field(default_factory=dict)
    agents: Dict[str, AgentConfig] = Field(default_factory=dict)
    global_: Optional[GlobalConfig] = Field(default=None, alias="global")
    hot_reload: Optional[HotReloadConfig] = None
    logging: Optional[LoggingConfig] = None
    performance: Optional[PerformanceConfig] = None
    tools: Optional[ToolsConfig] = None
    
    model_config = ConfigDict(populate_by_name=True)


# ============================================
# 配置验证器
# ============================================

class ConfigValidator:
    """
    配置验证器
    
    功能：
    - 验证配置文件
    - 加载配置
    - 保存配置
    - 配置迁移
    """
    
    def __init__(self, config_path: str = "config/agent_config.yaml"):
        self.config_path = Path(config_path)
        self.config: Optional[AppConfig] = None
        self.validation_errors: List[str] = []
    
    def validate(self, raise_on_error: bool = False) -> bool:
        """
        验证配置文件
        
        Args:
            raise_on_error: 验证失败时是否抛出异常
            
        Returns:
            bool: 验证是否通过
        """
        self.validation_errors = []
        
        try:
            if not self.config_path.exists():
                error = f"配置文件不存在：{self.config_path}"
                self.validation_errors.append(error)
                if raise_on_error:
                    raise FileNotFoundError(error)
                return False
            
            # 加载 YAML
            with open(self.config_path, 'r', encoding='utf-8') as f:
                raw_config = yaml.safe_load(f)
            
            # 验证并解析
            self.config = AppConfig(**raw_config)
            
            # 额外业务验证
            self._business_validation()
            
            logger.info(f"✅ 配置验证通过：{self.config_path}")
            return True
            
        except ValidationError as e:
            error_msg = f"配置验证失败：{e.error_count()} 个错误"
            self.validation_errors.append(error_msg)
            
            for error in e.errors():
                field = ".".join(str(x) for x in error['loc'])
                msg = error['msg']
                self.validation_errors.append(f"  - {field}: {msg}")
                logger.error(f"  ❌ {field}: {msg}")
            
            if raise_on_error:
                raise ValueError(error_msg)
            
            return False
        
        except Exception as e:
            error_msg = f"配置加载失败：{e}"
            self.validation_errors.append(error_msg)
            logger.error(f"❌ {error_msg}")
            
            if raise_on_error:
                raise
            
            return False
    
    def _business_validation(self):
        """业务规则验证"""
        if not self.config:
            return
        
        # 验证至少有一个启用的 Agent
        enabled_agents = [
            name for name, agent in self.config.agents.items()
            if agent.enabled
        ]
        
        if not enabled_agents:
            self.validation_errors.append("⚠️  警告：没有启用的 Agent")
            logger.warning("⚠️  没有启用的 Agent")
        
        # 验证至少有一个启用的 Provider
        enabled_providers = [
            name for name, provider in self.config.providers.items()
            if provider.enabled
        ]
        
        if not enabled_providers:
            self.validation_errors.append("⚠️  警告：没有启用的 LLM 提供者")
            logger.warning("⚠️  没有启用的 LLM 提供者")
        
        # 验证 Agent 使用的模型是否在 Provider 中定义
        for agent_name, agent in self.config.agents.items():
            if agent.enabled:
                provider = self.config.providers.get(agent.provider)
                if provider and provider.models:
                    if agent.model not in provider.models:
                        self.validation_errors.append(
                            f"⚠️  警告：Agent '{agent_name}' 使用未定义的模型 '{agent.model}'"
                        )
    
    def load(self) -> Optional[AppConfig]:
        """加载配置"""
        if self.validate():
            return self.config
        return None
    
    def save(self, config: Optional[AppConfig] = None, 
             backup: bool = True) -> bool:
        """
        保存配置
        
        Args:
            config: 配置对象（不传则使用当前配置）
            backup: 是否备份旧配置
            
        Returns:
            bool: 保存是否成功
        """
        try:
            config_to_save = config or self.config
            
            if not config_to_save:
                logger.error("❌ 没有可保存的配置")
                return False
            
            # 备份旧配置
            if backup and self.config_path.exists():
                self._backup_config()
            
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存 YAML
            config_dict = config_to_save.dict(by_alias=True, exclude_none=True)
            config_dict['updated_at'] = datetime.now().isoformat()
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, allow_unicode=True, 
                         default_flow_style=False, sort_keys=False)
            
            logger.info(f"✅ 配置已保存：{self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 配置保存失败：{e}")
            return False
    
    def _backup_config(self):
        """备份当前配置"""
        if not self.config_path.exists():
            return
        
        backup_dir = Path("config/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"agent_config_{timestamp}.yaml"
        
        import shutil
        shutil.copy2(self.config_path, backup_path)
        logger.debug(f"💾 配置已备份：{backup_path}")
    
    def get_validation_report(self) -> str:
        """获取验证报告"""
        if not self.validation_errors:
            return "✅ 配置验证通过"
        
        report = ["配置验证报告", "=" * 40]
        for error in self.validation_errors:
            report.append(error)
        return "\n".join(report)


# ============================================
# 便捷函数
# ============================================

def validate_config(config_path: str = "config/agent_config.yaml",
                   raise_on_error: bool = False) -> bool:
    """便捷函数：验证配置"""
    validator = ConfigValidator(config_path)
    return validator.validate(raise_on_error)


def load_config(config_path: str = "config/agent_config.yaml") -> Optional[AppConfig]:
    """便捷函数：加载配置"""
    validator = ConfigValidator(config_path)
    return validator.load()


# ============================================
# CLI 工具
# ============================================

if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config/agent_config.yaml"
    
    print(f"\n🔍 验证配置文件：{config_path}\n")
    
    validator = ConfigValidator(config_path)
    success = validator.validate(raise_on_error=False)
    
    print("\n" + "=" * 40)
    print(validator.get_validation_report())
    
    if success and validator.config:
        print("\n📊 配置摘要:")
        print(f"   Agents: {len(validator.config.agents)} 个")
        print(f"   Providers: {len(validator.config.providers)} 个")
        
        enabled_agents = sum(1 for a in validator.config.agents.values() if a.enabled)
        print(f"   启用的 Agents: {enabled_agents} 个")
    
    sys.exit(0 if success else 1)
