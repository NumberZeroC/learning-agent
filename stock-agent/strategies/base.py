"""
策略基类模块

定义策略的标准接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backtest.signal import Signal


class BaseStrategy(ABC):
    """
    策略基类
    
    所有交易策略都应继承此类并实现必要的方法
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        初始化策略
        
        Args:
            params: 策略参数
        """
        self.params = params or {}
        self.name_str = self.__class__.__name__
    
    @abstractmethod
    def generate_signals(
        self,
        date: str,
        data: Dict,
        account: Any,
        market_data: Any = None
    ) -> List[Signal]:
        """
        生成交易信号
        
        Args:
            date: 当前日期 (YYYY-MM-DD)
            data: 当日市场数据 {ts_code: DailyQuote}
            account: 账户对象
            market_data: 市场数据管理器 (可选)
            
        Returns:
            交易信号列表
        """
        pass
    
    def name(self) -> str:
        """策略名称"""
        return self.name_str
    
    def get_param(self, key: str, default: Any = None) -> Any:
        """获取参数"""
        return self.params.get(key, default)
    
    def get_stock_pool(self) -> List[str]:
        """
        获取股票池
        
        Returns:
            股票代码列表
        """
        # 默认返回空列表，子类可重写
        return []
    
    def _calculate_ma(self, prices: List[float], period: int) -> Optional[float]:
        """计算移动平均线"""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period
    
    def _calculate_momentum(
        self,
        prices: List[float],
        period: int
    ) -> Optional[float]:
        """计算动量 (价格变化率)"""
        if len(prices) < period + 1:
            return None
        return (prices[-1] - prices[-period - 1]) / prices[-period - 1]
    
    def _calculate_rsi(
        self,
        prices: List[float],
        period: int = 14
    ) -> Optional[float]:
        """计算 RSI 指标"""
        if len(prices) < period + 1:
            return None
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return None
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _is_price_above_ma(
        self,
        prices: List[float],
        ma_period: int
    ) -> bool:
        """判断价格是否在均线上方"""
        if len(prices) < ma_period + 1:
            return False
        
        ma = self._calculate_ma(prices, ma_period)
        return prices[-1] > ma if ma else False
    
    def _calculate_volatility(
        self,
        prices: List[float],
        period: int = 20
    ) -> Optional[float]:
        """计算波动率 (标准差)"""
        if len(prices) < period:
            return None
        
        import math
        ma = sum(prices[-period:]) / period
        variance = sum((p - ma) ** 2 for p in prices[-period:]) / period
        return math.sqrt(variance)
