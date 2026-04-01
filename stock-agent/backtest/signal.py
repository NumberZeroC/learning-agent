"""
交易信号模块
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime


class SignalType(Enum):
    """信号类型"""
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Signal:
    """
    交易信号
    
    Attributes:
        stock_code: 股票代码 (如：600519.SH)
        stock_name: 股票名称
        action: 买卖方向 (BUY/SELL)
        price: 预期价格
        volume: 交易数量 (股)
        confidence: 置信度 (0-1)
        reason: 信号原因
        date: 信号日期
        stop_loss: 止损价 (可选)
        take_profit: 止盈价 (可选)
        hold_period: 预期持有天数
        priority: 优先级 (数字越大优先级越高)
    """
    
    stock_code: str
    stock_name: str
    action: SignalType
    price: float
    volume: int
    confidence: float
    reason: str
    date: str
    
    # 可选参数
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    hold_period: int = 5
    priority: int = 0
    
    def __post_init__(self):
        """验证和标准化"""
        if not isinstance(self.action, SignalType):
            self.action = SignalType(self.action)
        
        # 确保 volume 是 100 的整数倍 (A 股 1 手=100 股)
        if self.volume > 0:
            self.volume = (self.volume // 100) * 100
        
        # 置信度限制在 0-1
        self.confidence = max(0.0, min(1.0, self.confidence))
    
    @property
    def amount(self) -> float:
        """交易金额"""
        return self.price * self.volume
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'action': self.action.value,
            'price': self.price,
            'volume': self.volume,
            'amount': self.amount,
            'confidence': self.confidence,
            'reason': self.reason,
            'date': self.date,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'hold_period': self.hold_period,
            'priority': self.priority,
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        action_str = "买入" if self.action == SignalType.BUY else "卖出"
        return f"{action_str} {self.stock_name}({self.stock_code}) {self.volume}股 @¥{self.price:.2f}"
