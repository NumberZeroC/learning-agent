"""
Stock-Agent 回测模块

提供完整的回测功能：
- 回测引擎
- 绩效分析
- 策略框架
"""

from .signal import Signal, SignalType
from .market_data import MarketData, DailyQuote
from .result import BacktestResult, PerformanceMetrics
from .backtester import Backtester
from .analyzer import PerformanceAnalyzer

__all__ = [
    'Signal',
    'SignalType',
    'MarketData',
    'DailyQuote',
    'BacktestResult',
    'PerformanceMetrics',
    'Backtester',
    'PerformanceAnalyzer',
]
