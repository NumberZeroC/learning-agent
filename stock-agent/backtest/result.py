"""
回测结果模块
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class PerformanceMetrics:
    """
    绩效指标
    
    Attributes:
        # 收益指标
        total_return: 总收益率
        annual_return: 年化收益率
        excess_return: 超额收益 (相对基准)
        
        # 风险指标
        max_drawdown: 最大回撤
        volatility: 年化波动率
        var_95: 95% VaR
        
        # 风险调整收益
        sharpe_ratio: 夏普比率
        sortino_ratio: 索提诺比率
        calmar_ratio: 卡玛比率
        
        # 交易统计
        total_trades: 总交易次数
        win_rate: 胜率
        profit_loss_ratio: 盈亏比
        avg_win: 平均盈利
        avg_loss: 平均亏损
        avg_hold_period: 平均持有天数
        
        # 基准对比
        benchmark_return: 基准收益
        alpha: Alpha
        beta: Beta
    """
    
    # 收益指标
    total_return: float = 0.0
    annual_return: float = 0.0
    excess_return: float = 0.0
    
    # 风险指标
    max_drawdown: float = 0.0
    volatility: float = 0.0
    var_95: float = 0.0
    
    # 风险调整收益
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    
    # 交易统计
    total_trades: int = 0
    win_rate: float = 0.0
    profit_loss_ratio: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    avg_hold_period: float = 0.0
    
    # 基准对比
    benchmark_return: float = 0.0
    alpha: float = 0.0
    beta: float = 0.0
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'total_return': self.total_return,
            'annual_return': self.annual_return,
            'excess_return': self.excess_return,
            'max_drawdown': self.max_drawdown,
            'volatility': self.volatility,
            'var_95': self.var_95,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'calmar_ratio': self.calmar_ratio,
            'total_trades': self.total_trades,
            'win_rate': self.win_rate,
            'profit_loss_ratio': self.profit_loss_ratio,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'avg_hold_period': self.avg_hold_period,
            'benchmark_return': self.benchmark_return,
            'alpha': self.alpha,
            'beta': self.beta,
        }
    
    def summary(self) -> str:
        """绩效摘要"""
        return (
            f"总收益率：{self.total_return:.2%} | "
            f"年化收益：{self.annual_return:.2%} | "
            f"最大回撤：{self.max_drawdown:.2%} | "
            f"夏普比率：{self.sharpe_ratio:.2f} | "
            f"胜率：{self.win_rate:.1%}"
        )


@dataclass
class TradeRecord:
    """交易记录"""
    
    date: str
    stock_code: str
    stock_name: str
    action: str  # BUY | SELL
    volume: int
    price: float
    amount: float
    commission: float
    pnl: float = 0.0  # 盈亏 (仅卖出时有值)
    hold_period: int = 0  # 持有天数
    reason: str = ""


@dataclass
class DailySnapshot:
    """每日账户快照"""
    
    date: str
    total_value: float
    cash: float
    market_value: float
    position_count: int
    daily_return: float = 0.0
    cumulative_return: float = 0.0


@dataclass
class BacktestResult:
    """
    回测结果
    
    Attributes:
        strategy_name: 策略名称
        start_date: 开始日期
        end_date: 结束日期
        initial_capital: 初始资金
        final_value: 期末总值
        metrics: 绩效指标
        snapshots: 每日快照
        trades: 交易记录
        holdings: 最终持仓
        config: 回测配置
    """
    
    strategy_name: str
    start_date: str
    end_date: str
    initial_capital: float
    final_value: float
    
    metrics: PerformanceMetrics
    snapshots: List[DailySnapshot] = field(default_factory=list)
    trades: List[TradeRecord] = field(default_factory=list)
    holdings: Dict[str, Any] = field(default_factory=dict)
    
    config: Dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    @property
    def total_return(self) -> float:
        """总收益率"""
        return (self.final_value - self.initial_capital) / self.initial_capital
    
    @property
    def trading_days(self) -> int:
        """交易天数"""
        return len(self.snapshots)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'strategy_name': self.strategy_name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'initial_capital': self.initial_capital,
            'final_value': self.final_value,
            'total_return': self.total_return,
            'trading_days': self.trading_days,
            'metrics': self.metrics.to_dict(),
            'snapshots': [
                {
                    'date': s.date,
                    'total_value': s.total_value,
                    'cash': s.cash,
                    'market_value': s.market_value,
                    'position_count': s.position_count,
                    'daily_return': s.daily_return,
                    'cumulative_return': s.cumulative_return,
                }
                for s in self.snapshots
            ],
            'trades': [
                {
                    'date': t.date,
                    'stock_code': t.stock_code,
                    'stock_name': t.stock_name,
                    'action': t.action,
                    'volume': t.volume,
                    'price': t.price,
                    'amount': t.amount,
                    'commission': t.commission,
                    'pnl': t.pnl,
                    'hold_period': t.hold_period,
                    'reason': t.reason,
                }
                for t in self.trades
            ],
            'holdings': self.holdings,
            'config': self.config,
            'created_at': self.created_at,
        }
    
    def summary(self) -> str:
        """结果摘要"""
        return (
            f"【{self.strategy_name}】回测结果\n"
            f"区间：{self.start_date} ~ {self.end_date} ({self.trading_days}天)\n"
            f"初始资金：¥{self.initial_capital:,.0f} → 期末总值：¥{self.final_value:,.0f}\n"
            f"总收益率：{self.total_return:.2%}\n"
            f"{self.metrics.summary()}"
        )
