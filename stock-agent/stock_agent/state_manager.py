"""
状态管理模块 - 基于 LangGraph 理念的状态机
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from .account import Account, Position, Order, Trade


@dataclass
class Signal:
    """交易信号"""
    stock_code: str
    stock_name: str
    action: str  # BUY | SELL | HOLD
    strength: float  # 0-1
    reason: str
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


@dataclass
class MarketData:
    """市场数据"""
    date: str
    indices: Dict[str, float] = field(default_factory=dict)  # 指数
    stocks: Dict[str, Dict] = field(default_factory=dict)  # 个股
    sectors: Dict[str, float] = field(default_factory=dict)  # 板块


class StateManager:
    """状态管理器"""
    
    def __init__(self, account: Account):
        self.account = account
        
        # 系统状态
        self.current_step: str = "init"
        self.trading_date: str = ""
        self.is_trading: bool = False
        
        # 数据状态
        self.market_data: Optional[MarketData] = None
        self.signals: List[Signal] = []
        
        # Agent 消息
        self.messages: List[str] = []
        
        # 性能指标
        self.daily_return: float = 0.0
        self.total_return: float = 0.0
        self.max_drawdown: float = 0.0
        self.sharpe_ratio: float = 0.0
        self.win_rate: float = 0.0
        
        # 历史峰值（用于计算回撤）
        self.peak_value: float = account.initial_capital
        
        # 状态历史
        self.history: List[Dict] = []
    
    def add_message(self, agent: str, message: str) -> None:
        """添加 Agent 消息"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.messages.append(f"[{timestamp}] {agent}: {message}")
    
    def add_signal(self, signal: Signal) -> None:
        """添加交易信号"""
        self.signals.append(signal)
        self.add_message("Analyst", f"{signal.action} {signal.stock_name} - {signal.reason}")
    
    def clear_signals(self) -> None:
        """清除信号"""
        self.signals = []
    
    def update_market_data(self, data: MarketData) -> None:
        """更新市场数据"""
        self.market_data = data
        self.trading_date = data.date
        
        # 更新持仓价格
        prices = {code: info.get('close', info.get('price', 0)) 
                  for code, info in data.stocks.items()}
        self.account.update_prices(prices)
    
    def update_performance(self) -> None:
        """更新性能指标"""
        # 总收益
        self.total_return = self.account.return_rate
        
        # 日收益
        if self.history:
            prev_value = self.history[-1].get('total_value', self.account.initial_capital)
            self.daily_return = (self.account.total_value - prev_value) / prev_value
        
        # 最大回撤
        if self.account.total_value > self.peak_value:
            self.peak_value = self.account.total_value
        drawdown = (self.peak_value - self.account.total_value) / self.peak_value
        self.max_drawdown = max(self.max_drawdown, drawdown)
        
        # 胜率
        if self.account.trades:
            profitable = sum(1 for t in self.account.trades if t.side == 'SELL' and t.price > 0)
            # 简化计算
            self.win_rate = profitable / len(self.account.trades) if self.account.trades else 0
    
    def save_state(self) -> Dict:
        """保存当前状态"""
        state = {
            'date': self.trading_date,
            'timestamp': datetime.now().isoformat(),
            'step': self.current_step,
            'account': self.account.get_summary(),
            'positions': [
                {
                    'code': p.stock_code,
                    'name': p.stock_name,
                    'volume': p.volume,
                    'avg_cost': p.avg_cost,
                    'current_price': p.current_price,
                    'profit_rate': p.profit_rate,
                }
                for p in self.account.get_positions()
            ],
            'signals': [
                {
                    'code': s.stock_code,
                    'name': s.stock_name,
                    'action': s.action,
                    'strength': s.strength,
                    'reason': s.reason,
                }
                for s in self.signals
            ],
            'performance': {
                'daily_return': self.daily_return,
                'total_return': self.total_return,
                'max_drawdown': self.max_drawdown,
                'sharpe_ratio': self.sharpe_ratio,
                'win_rate': self.win_rate,
            },
        }
        
        self.history.append(state)
        return state
    
    def get_state(self) -> Dict:
        """获取当前状态"""
        return {
            'step': self.current_step,
            'date': self.trading_date,
            'is_trading': self.is_trading,
            'account_summary': self.account.get_summary(),
            'signal_count': len(self.signals),
            'message_count': len(self.messages),
        }
    
    def get_recent_messages(self, limit: int = 10) -> List[str]:
        """获取最近消息"""
        return self.messages[-limit:]
    
    def __repr__(self) -> str:
        return f"StateManager(step={self.current_step}, date={self.trading_date})"
