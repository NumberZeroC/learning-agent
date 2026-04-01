"""
回测引擎核心模块

负责执行回测流程，模拟交易
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from stock_agent import Account, Config
from .signal import Signal, SignalType
from .market_data import MarketData, DailyQuote
from .result import BacktestResult, PerformanceMetrics, DailySnapshot, TradeRecord
from .analyzer import PerformanceAnalyzer


class Backtester:
    """
    回测引擎
    
    执行完整的回测流程：
    1. 初始化账户和数据
    2. 按交易日推进
    3. 生成和执行信号
    4. 记录结果
    5. 绩效分析
    """
    
    def __init__(
        self,
        strategy,
        start_date: str,
        end_date: str,
        initial_capital: float = 1000000,
        commission_rate: float = 0.0003,
        stamp_duty: float = 0.001,
        data_source=None,
        benchmark_code: str = '000001.SH',  # 上证指数
        verbose: bool = True
    ):
        """
        初始化回测器
        
        Args:
            strategy: 交易策略 (实现 BaseStrategy 接口)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            initial_capital: 初始资金
            commission_rate: 佣金率
            stamp_duty: 印花税
            data_source: 数据源 (TushareSource 或 AKShareSource)
            benchmark_code: 基准指数代码
            verbose: 是否输出详细信息
        """
        self.strategy = strategy
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.stamp_duty = stamp_duty
        self.data_source = data_source
        self.benchmark_code = benchmark_code
        self.verbose = verbose
        
        # 核心组件
        self.account: Optional[Account] = None
        self.market_data: Optional[MarketData] = None
        
        # 结果记录
        self.snapshots: List[DailySnapshot] = []
        self.trades: List[TradeRecord] = []
        self.signals_history: List[List[Signal]] = []
        
        # 配置
        self.config = {
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': initial_capital,
            'commission_rate': commission_rate,
            'stamp_duty': stamp_duty,
            'benchmark_code': benchmark_code,
            'strategy_name': strategy.name() if hasattr(strategy, 'name') else 'Unknown',
        }
    
    def _log(self, message: str):
        """日志输出"""
        if self.verbose:
            print(f"[Backtester] {message}")
    
    def prepare_data(self, stock_pool: List[str] = None) -> bool:
        """
        准备历史数据
        
        Args:
            stock_pool: 股票池 (可选，为空则使用策略提供的股票池)
            
        Returns:
            是否成功
        """
        self._log("准备历史数据...")
        
        if not self.data_source:
            self._log("⚠️ 未配置数据源")
            return False
        
        # 获取股票池
        if stock_pool is None and hasattr(self.strategy, 'get_stock_pool'):
            stock_pool = self.strategy.get_stock_pool()
        
        if not stock_pool:
            self._log("⚠️ 未提供股票池")
            return False
        
        # 添加基准指数
        if self.benchmark_code not in stock_pool:
            stock_pool.append(self.benchmark_code)
        
        # 创建市场数据管理器
        self.market_data = MarketData(data_source=self.data_source)
        
        # 加载数据
        success = self.market_data.load_daily_data(
            ts_codes=stock_pool,
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        if success:
            stats = self.market_data.get_stats()
            self._log(f"✅ 加载 {stats['stocks_loaded']} 只股票，{stats['days_loaded']} 条数据")
        else:
            self._log("❌ 数据加载失败")
        
        return success
    
    def run(self) -> BacktestResult:
        """
        运行回测
        
        Returns:
            回测结果
        """
        self._log("=" * 60)
        self._log(f"开始回测：{self.config['strategy_name']}")
        self._log(f"区间：{self.start_date} ~ {self.end_date}")
        self._log(f"初始资金：¥{self.initial_capital:,.0f}")
        self._log("=" * 60)
        
        # 创建模拟账户
        self.account = Account(
            initial_capital=self.initial_capital,
            commission_rate=self.commission_rate,
            stamp_duty=self.stamp_duty
        )
        
        # 获取交易日期
        trading_dates = self.market_data.get_trading_dates(
            self.start_date,
            self.end_date,
            self.benchmark_code
        )
        
        if not trading_dates:
            self._log("❌ 无法获取交易日期")
            return None
        
        self._log(f"交易天数：{len(trading_dates)}")
        self._log("")
        
        # 主回测循环
        for i, date in enumerate(trading_dates):
            self._run_day(date, i, len(trading_dates))
        
        # 计算最终结果
        final_value = self.account.total_value
        self._log("")
        self._log(f"回测完成！期末总值：¥{final_value:,.0f}")
        
        # 创建回测结果
        result = BacktestResult(
            strategy_name=self.config['strategy_name'],
            start_date=self.start_date,
            end_date=self.end_date,
            initial_capital=self.initial_capital,
            final_value=final_value,
            metrics=PerformanceMetrics(),  # 稍后计算
            snapshots=self.snapshots,
            trades=self.trades,
            holdings=self._get_current_holdings(),
            config=self.config,
        )
        
        # 绩效分析
        self._log("计算绩效指标...")
        analyzer = PerformanceAnalyzer(result)
        benchmark_returns = self._get_benchmark_returns(trading_dates)
        result.metrics = analyzer.calculate_metrics(benchmark_returns)
        
        # 输出结果摘要
        self._log("")
        self._log("=" * 60)
        self._log("回测结果摘要")
        self._log("=" * 60)
        self._log(f"总收益率：  {result.total_return:.2%}")
        self._log(f"年化收益：  {result.metrics.annual_return:.2%}")
        self._log(f"最大回撤：  {result.metrics.max_drawdown:.2%}")
        self._log(f"夏普比率：  {result.metrics.sharpe_ratio:.2f}")
        self._log(f"胜率：      {result.metrics.win_rate:.1%}")
        self._log(f"交易次数：  {result.metrics.total_trades}")
        self._log("=" * 60)
        
        return result
    
    def _run_day(self, date: str, day_index: int, total_days: int):
        """
        运行单个交易日
        
        Args:
            date: 交易日期
            day_index: 第几天
            total_days: 总天数
        """
        # 进度输出
        if self.verbose and (day_index % 20 == 0 or day_index == total_days - 1):
            progress = (day_index + 1) / total_days * 100
            self._log(f"进度：{progress:.1f}% ({day_index + 1}/{total_days})")
        
        # 1. 获取当日数据
        daily_quotes = self.market_data.get_all_quotes(date)
        
        if not daily_quotes:
            return
        
        # 2. 更新持仓价格
        self._update_positions(daily_quotes, date)
        
        # 3. 检查止损止盈
        stop_signals = self._check_stop_loss(date, daily_quotes)
        
        # 4. 生成新信号
        new_signals = self.strategy.generate_signals(
            date=date,
            data=daily_quotes,
            account=self.account,
            market_data=self.market_data
        )
        
        # 5. 合并信号 (止损优先)
        all_signals = stop_signals + new_signals
        
        # 6. 执行信号
        self._execute_signals(all_signals, date, daily_quotes)
        
        # 7. 记录快照
        self._record_snapshot(date)
    
    def _update_positions(self, quotes: Dict[str, DailyQuote], date: str):
        """更新持仓价格"""
        for stock_code, position in self.account.positions.items():
            # 尝试不同格式的代码
            quote = quotes.get(stock_code)
            if not quote:
                # 尝试添加后缀
                if '.' not in stock_code:
                    if stock_code.startswith('6'):
                        quote = quotes.get(f"{stock_code}.SH")
                    else:
                        quote = quotes.get(f"{stock_code}.SZ")
            
            if quote:
                position.current_price = quote.close
    
    def _check_stop_loss(
        self,
        date: str,
        quotes: Dict[str, DailyQuote]
    ) -> List[Signal]:
        """检查止损止盈信号"""
        signals = []
        
        for stock_code, position in self.account.positions.items():
            # 获取股票代码
            ts_code = stock_code
            if '.' not in ts_code:
                ts_code = f"{ts_code}.SH" if ts_code.startswith('6') else f"{ts_code}.SZ"
            
            quote = quotes.get(ts_code)
            if not quote:
                continue
            
            current_price = quote.close
            cost = position.avg_cost
            
            # 检查止损
            if cost > 0:
                loss_pct = (current_price - cost) / cost
                
                # 止损 (亏损超过 8%)
                if loss_pct < -0.08:
                    signals.append(Signal(
                        stock_code=ts_code,
                        stock_name=position.stock_name,
                        action=SignalType.SELL,
                        price=current_price,
                        volume=position.volume,
                        confidence=1.0,
                        reason=f"止损：{loss_pct:.1%}",
                        date=date,
                        priority=10,  # 高优先级
                    ))
                
                # 止盈 (盈利超过 20%)
                elif loss_pct > 0.20:
                    signals.append(Signal(
                        stock_code=ts_code,
                        stock_name=position.stock_name,
                        action=SignalType.SELL,
                        price=current_price,
                        volume=position.volume,
                        confidence=1.0,
                        reason=f"止盈：{loss_pct:.1%}",
                        date=date,
                        priority=10,
                    ))
        
        return signals
    
    def _execute_signals(
        self,
        signals: List[Signal],
        date: str,
        quotes: Dict[str, DailyQuote]
    ):
        """执行交易信号"""
        # 按优先级排序
        signals.sort(key=lambda s: s.priority, reverse=True)
        
        for signal in signals:
            # 获取实际价格
            quote = quotes.get(signal.stock_code)
            if quote:
                exec_price = quote.close
            else:
                exec_price = signal.price
            
            if signal.action == SignalType.BUY:
                # 买入
                success = self._execute_buy(signal, exec_price, date)
            else:
                # 卖出
                success = self._execute_sell(signal, exec_price, date)
            
            if success:
                self._log(f"  {signal.action.value} {signal.stock_name} {signal.volume}股 @¥{exec_price:.2f}")
    
    def _execute_buy(self, signal: Signal, price: float, date: str) -> bool:
        """执行买入"""
        # 检查资金
        required = price * signal.volume
        commission = required * self.commission_rate
        total_cost = required + commission
        
        if total_cost > self.account.cash:
            # 资金不足，调整数量
            available = self.account.cash * 0.95  # 留 5% 余量
            max_volume = int(available / price / 100) * 100
            if max_volume < 100:
                return False
            signal.volume = max_volume
            required = price * signal.volume
            commission = required * self.commission_rate
        
        # 执行买入
        order = self.account.buy(
            stock_code=signal.stock_code.replace('.SH', '').replace('.SZ', ''),
            stock_name=signal.stock_name,
            volume=signal.volume,
            price=price
        )
        
        if order:
            # 记录交易
            self.trades.append(TradeRecord(
                date=date,
                stock_code=signal.stock_code,
                stock_name=signal.stock_name,
                action='BUY',
                volume=signal.volume,
                price=price,
                amount=required,
                commission=commission,
                reason=signal.reason,
            ))
            return True
        
        return False
    
    def _execute_sell(self, signal: Signal, price: float, date: str) -> bool:
        """执行卖出"""
        # 检查持仓
        stock_code = signal.stock_code.replace('.SH', '').replace('.SZ', '')
        if stock_code not in self.account.positions:
            return False
        
        position = self.account.positions[stock_code]
        
        # 执行卖出
        order = self.account.sell(
            stock_code=stock_code,
            volume=signal.volume,
            price=price
        )
        
        if order:
            # 计算盈亏
            cost = position.avg_cost * signal.volume
            revenue = price * signal.volume
            commission = revenue * self.commission_rate
            stamp_duty = revenue * self.stamp_duty
            pnl = revenue - cost - commission - stamp_duty
            
            # 计算持有天数
            hold_period = 1
            if hasattr(position, 'buy_date') and position.buy_date:
                try:
                    buy_date = datetime.strptime(position.buy_date, '%Y-%m-%d')
                    sell_date = datetime.strptime(date, '%Y-%m-%d')
                    hold_period = (sell_date - buy_date).days
                except:
                    pass
            
            # 记录交易
            self.trades.append(TradeRecord(
                date=date,
                stock_code=signal.stock_code,
                stock_name=signal.stock_name,
                action='SELL',
                volume=signal.volume,
                price=price,
                amount=revenue,
                commission=commission + stamp_duty,
                pnl=pnl,
                hold_period=hold_period,
                reason=signal.reason,
            ))
            return True
        
        return False
    
    def _record_snapshot(self, date: str):
        """记录每日快照"""
        prev_value = self.snapshots[-1].total_value if self.snapshots else self.initial_capital
        curr_value = self.account.total_value
        
        daily_return = (curr_value - prev_value) / prev_value if prev_value > 0 else 0
        cumulative_return = (curr_value - self.initial_capital) / self.initial_capital
        
        self.snapshots.append(DailySnapshot(
            date=date,
            total_value=curr_value,
            cash=self.account.cash,
            market_value=self.account.market_value,
            position_count=len(self.account.positions),
            daily_return=daily_return,
            cumulative_return=cumulative_return,
        ))
    
    def _get_current_holdings(self) -> Dict:
        """获取当前持仓"""
        holdings = {}
        for code, pos in self.account.positions.items():
            holdings[code] = {
                'name': pos.stock_name,
                'volume': pos.volume,
                'avg_cost': pos.avg_cost,
                'current_price': pos.current_price,
                'market_value': pos.market_value,
                'profit': pos.profit,
                'profit_rate': pos.profit_rate,
            }
        return holdings
    
    def _get_benchmark_returns(self, trading_dates: List[str]) -> List[float]:
        """获取基准收益率"""
        returns = []
        
        prev_close = None
        for date in trading_dates:
            quote = self.market_data.get_quote(self.benchmark_code, date)
            if quote:
                if prev_close:
                    ret = (quote.close - prev_close) / prev_close
                    returns.append(ret)
                prev_close = quote.close
        
        return returns
