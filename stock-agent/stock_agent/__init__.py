"""
Stock-Agent - 智能量化模拟交易系统

核心模块初始化
数据源：Tushare Pro (主) + AKShare (备用)
"""

__version__ = '1.0.0'
__author__ = 'Stock-Agent Team'

from .account import Account
from .state_manager import StateManager
from .config import Config
from .tushare_source import TushareSource
from .akshare_source import AKShareSource
from .realtime_monitor import RealTimeMonitor, TradingLogger

__all__ = [
    'Account', 
    'StateManager', 
    'Config', 
    'TushareSource',
    'AKShareSource',
    'RealTimeMonitor',
    'TradingLogger'
]
