"""
配置管理模块
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """配置管理器"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> None:
        """加载配置文件"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = self._default_config()
            self.save()
    
    def save(self) -> None:
        """保存配置文件"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            'account': {
                'initial_capital': 1000000,  # 初始资金 100 万
                'currency': 'CNY',
                'commission_rate': 0.0003,  # 佣金万三
                'stamp_duty': 0.001,  # 印花税千一
            },
            'data': {
                'primary': 'tushare',  # 默认使用 Tushare
                'cache_enabled': True,
                'cache_ttl': 600,
            },
            'tushare': {
                'enabled': True,
                'token': '',  # 从环境变量或配置文件读取
                'priority': 1,
                'cache_ttl': 600,
            },
            'akshare': {
                'enabled': True,
                'priority': 2,
                'cache_ttl': 300,
            },
            'risk_limits': {
                'max_single_position': 0.30,  # 单只股票最大 30%
                'max_sector_exposure': 0.50,  # 单板块最大 50%
                'min_cash_ratio': 0.10,  # 最低现金 10%
                'stop_loss_pct': 0.08,  # 8% 止损
                'take_profit_pct': 0.20,  # 20% 止盈
            },
            'trading': {
                'max_daily_trades': 10,
                'max_positions': 10,
                'min_holding_period': 1,
            },
            'agents': {
                'analyst': {'enabled': True},
                'trader': {'enabled': True},
                'risk_manager': {'enabled': True},
            },
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置配置项"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
    
    @property
    def initial_capital(self) -> float:
        """初始资金"""
        return self.get('account.initial_capital', 1000000)
    
    @property
    def commission_rate(self) -> float:
        """佣金率"""
        return self.get('account.commission_rate', 0.0003)
    
    @property
    def stamp_duty(self) -> float:
        """印花税"""
        return self.get('account.stamp_duty', 0.001)
