"""
绩效分析器模块

计算回测绩效指标，生成分析报告
"""
import math
from typing import List, Dict, Optional
from datetime import datetime
import numpy as np

from .result import BacktestResult, PerformanceMetrics, DailySnapshot, TradeRecord


class PerformanceAnalyzer:
    """
    绩效分析器
    
    计算各种绩效指标并生成报告
    """
    
    RISK_FREE_RATE = 0.03  # 无风险利率 (年化 3%)
    TRADING_DAYS_PER_YEAR = 252
    
    def __init__(self, result: BacktestResult):
        """
        初始化分析器
        
        Args:
            result: 回测结果
        """
        self.result = result
        self.metrics: Optional[PerformanceMetrics] = None
    
    def calculate_metrics(
        self,
        benchmark_returns: List[float] = None
    ) -> PerformanceMetrics:
        """
        计算绩效指标
        
        Args:
            benchmark_returns: 基准收益率列表 (可选)
            
        Returns:
            绩效指标
        """
        snapshots = self.result.snapshots
        
        if len(snapshots) < 2:
            self.metrics = PerformanceMetrics()
            return self.metrics
        
        # 计算日收益率
        values = [s.total_value for s in snapshots]
        daily_returns = self._calculate_returns(values)
        
        # 收益指标
        total_return = (values[-1] - values[0]) / values[0]
        trading_days = len(snapshots)
        annual_return = (1 + total_return) ** (self.TRADING_DAYS_PER_YEAR / trading_days) - 1
        
        # 风险指标
        max_drawdown = self._calculate_max_drawdown(values)
        volatility = self._calculate_volatility(daily_returns)
        var_95 = self._calculate_var(daily_returns, 0.95)
        
        # 风险调整收益
        sharpe_ratio = self._calculate_sharpe(daily_returns, annual_return)
        sortino_ratio = self._calculate_sortino(daily_returns, annual_return)
        calmar_ratio = self._calculate_calmar(annual_return, max_drawdown)
        
        # 交易统计
        trades = self.result.trades
        total_trades = len([t for t in trades if t.action == 'SELL'])
        
        win_trades = [t for t in trades if t.action == 'SELL' and t.pnl > 0]
        loss_trades = [t for t in trades if t.action == 'SELL' and t.pnl <= 0]
        
        win_rate = len(win_trades) / total_trades if total_trades > 0 else 0
        
        avg_win = np.mean([t.pnl for t in win_trades]) if win_trades else 0
        avg_loss = np.mean([t.pnl for t in loss_trades]) if loss_trades else 0
        profit_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        hold_periods = [t.hold_period for t in trades if t.action == 'SELL']
        avg_hold_period = np.mean(hold_periods) if hold_periods else 0
        
        # 基准对比
        benchmark_return = 0.0
        alpha = 0.0
        beta = 0.0
        
        if benchmark_returns and len(benchmark_returns) == len(daily_returns):
            benchmark_return = sum(benchmark_returns)
            alpha, beta = self._calculate_alpha_beta(daily_returns, benchmark_returns)
        
        excess_return = total_return - benchmark_return
        
        self.metrics = PerformanceMetrics(
            total_return=total_return,
            annual_return=annual_return,
            excess_return=excess_return,
            max_drawdown=max_drawdown,
            volatility=volatility,
            var_95=var_95,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            total_trades=total_trades,
            win_rate=win_rate,
            profit_loss_ratio=profit_loss_ratio,
            avg_win=avg_win,
            avg_loss=avg_loss,
            avg_hold_period=avg_hold_period,
            benchmark_return=benchmark_return,
            alpha=alpha,
            beta=beta,
        )
        
        return self.metrics
    
    def _calculate_returns(self, values: List[float]) -> List[float]:
        """计算日收益率"""
        returns = []
        for i in range(1, len(values)):
            ret = (values[i] - values[i-1]) / values[i-1]
            returns.append(ret)
        return returns
    
    def _calculate_max_drawdown(self, values: List[float]) -> float:
        """计算最大回撤"""
        peak = values[0]
        max_dd = 0
        
        for value in values:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def _calculate_volatility(self, returns: List[float]) -> float:
        """计算年化波动率"""
        if len(returns) < 2:
            return 0
        
        std = np.std(returns, ddof=1)
        return std * math.sqrt(self.TRADING_DAYS_PER_YEAR)
    
    def _calculate_var(self, returns: List[float], confidence: float = 0.95) -> float:
        """计算 VaR"""
        if len(returns) < 10:
            return 0
        
        percentile = (1 - confidence) * 100
        return abs(np.percentile(returns, percentile))
    
    def _calculate_sharpe(
        self,
        returns: List[float],
        annual_return: float
    ) -> float:
        """计算夏普比率"""
        if len(returns) < 2:
            return 0
        
        volatility = self._calculate_volatility(returns)
        if volatility == 0:
            return 0
        
        return (annual_return - self.RISK_FREE_RATE) / volatility
    
    def _calculate_sortino(
        self,
        returns: List[float],
        annual_return: float
    ) -> float:
        """计算索提诺比率 (只考虑下行波动)"""
        if len(returns) < 2:
            return 0
        
        negative_returns = [r for r in returns if r < 0]
        if not negative_returns:
            return float('inf')
        
        downside_std = np.std(negative_returns, ddof=1)
        downside_annual = downside_std * math.sqrt(self.TRADING_DAYS_PER_YEAR)
        
        if downside_annual == 0:
            return 0
        
        return (annual_return - self.RISK_FREE_RATE) / downside_annual
    
    def _calculate_calmar(
        self,
        annual_return: float,
        max_drawdown: float
    ) -> float:
        """计算卡玛比率"""
        if max_drawdown == 0:
            return 0
        
        return annual_return / abs(max_drawdown)
    
    def _calculate_alpha_beta(
        self,
        strategy_returns: List[float],
        benchmark_returns: List[float]
    ) -> tuple:
        """计算 Alpha 和 Beta"""
        if len(strategy_returns) < 10:
            return 0, 0
        
        # 简化计算
        strategy_mean = np.mean(strategy_returns)
        benchmark_mean = np.mean(benchmark_returns)
        
        # Beta = Cov(Rs, Rm) / Var(Rm)
        covariance = np.cov(strategy_returns, benchmark_returns)[0, 1]
        variance = np.var(benchmark_returns)
        
        beta = covariance / variance if variance > 0 else 0
        
        # Alpha = Rs - Beta * Rm (年化)
        alpha = (strategy_mean - beta * benchmark_mean) * self.TRADING_DAYS_PER_YEAR
        
        return alpha, beta
    
    def generate_report(self, format: str = 'markdown') -> str:
        """
        生成回测报告
        
        Args:
            format: 报告格式 (markdown | json | text)
            
        Returns:
            报告内容
        """
        if format == 'markdown':
            return self._generate_markdown_report()
        elif format == 'json':
            import json
            return json.dumps(self.result.to_dict(), indent=2, ensure_ascii=False)
        else:
            return self._generate_text_report()
    
    def _generate_markdown_report(self) -> str:
        """生成 Markdown 格式报告"""
        m = self.metrics
        
        report = f"""# 📈 回测报告 - {self.result.strategy_name}

**回测区间：** {self.result.start_date} ~ {self.result.end_date}  
**交易天数：** {self.result.trading_days} 天  
**初始资金：** ¥{self.result.initial_capital:,.0f}  
**期末总值：** ¥{self.result.final_value:,.0f}

---

## 📊 绩效概览

| 指标 | 数值 | 说明 |
|------|------|------|
| **总收益率** | {m.total_return:.2%} | |
| **年化收益率** | {m.annual_return:.2%} | |
| **超额收益** | {m.excess_return:.2%} | 相对基准 |
| **最大回撤** | {m.max_drawdown:.2%} | |
| **年化波动率** | {m.volatility:.2%} | |
| **95% VaR** | {m.var_95:.2%} | 日度 |

---

## 🎯 风险调整收益

| 指标 | 数值 | 说明 |
|------|------|------|
| **夏普比率** | {m.sharpe_ratio:.2f} | >1 优秀 |
| **索提诺比率** | {m.sortino_ratio:.2f} | 下行风险调整 |
| **卡玛比率** | {m.calmar_ratio:.2f} | 收益回撤比 |

---

## 📋 交易统计

| 指标 | 数值 |
|------|------|
| **总交易次数** | {m.total_trades} |
| **胜率** | {m.win_rate:.1%} |
| **盈亏比** | {m.profit_loss_ratio:.2f} |
| **平均盈利** | ¥{m.avg_win:,.0f} |
| **平均亏损** | ¥{abs(m.avg_loss):,.0f} |
| **平均持有天数** | {m.avg_hold_period:.1f} 天 |

---

## 📈 基准对比

| 指标 | 策略 | 基准 | 超额 |
|------|------|------|------|
| **收益率** | {m.total_return:.2%} | {m.benchmark_return:.2%} | {m.excess_return:.2%} |
| **Alpha** | {m.alpha:.4f} | - | - |
| **Beta** | {m.beta:.2f} | 1.0 | - |

---

## 🏆 交易明细

### 买入交易

| 日期 | 股票 | 数量 | 价格 | 金额 |
|------|------|------|------|------|
"""
        
        # 添加买入交易
        buy_trades = [t for t in self.result.trades if t.action == 'BUY'][:20]
        for t in buy_trades:
            report += f"| {t.date} | {t.stock_name} | {t.volume} | ¥{t.price:.2f} | ¥{t.amount:,.0f} |\n"
        
        report += """
### 卖出交易

| 日期 | 股票 | 盈亏 | 持有天数 | 收益率 |
|------|------|------|---------|--------|
"""
        
        # 添加卖出交易
        sell_trades = [t for t in self.result.trades if t.action == 'SELL'][:20]
        for t in sell_trades:
            pnl_pct = t.pnl / t.amount if t.amount > 0 else 0
            report += f"| {t.date} | {t.stock_name} | ¥{t.pnl:,.0f} | {t.hold_period}天 | {pnl_pct:.1%} |\n"
        
        report += f"""
---

## ⚠️ 风险提示

- 历史业绩不代表未来表现
- 回测未考虑滑点和市场冲击成本
- 策略可能存在过拟合风险
- 实际交易可能受涨跌停限制

---

*报告生成时间：{self.result.created_at}*
"""
        
        return report
    
    def _generate_text_report(self) -> str:
        """生成纯文本报告"""
        m = self.metrics
        
        report = f"""
========================================
  回测报告 - {self.result.strategy_name}
========================================

回测区间：{self.result.start_date} ~ {self.result.end_date}
交易天数：{self.result.trading_days} 天
初始资金：¥{self.result.initial_capital:,.0f}
期末总值：¥{self.result.final_value:,.0f}

【绩效指标】
总收益率：    {m.total_return:>10.2%}
年化收益率：  {m.annual_return:>10.2%}
最大回撤：    {m.max_drawdown:>10.2%}
夏普比率：    {m.sharpe_ratio:>10.2f}
胜率：        {m.win_rate:>10.1%}

【交易统计】
总交易次数：  {m.total_trades:>10}
盈亏比：      {m.profit_loss_ratio:>10.2f}
平均持有：    {m.avg_hold_period:>10.1f} 天

========================================
"""
        
        return report
