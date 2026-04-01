"""
动量策略

基于价格动量和技术指标的选股策略

核心逻辑：
1. 选择近期表现强势的股票
2. 确认趋势向上 (均线多头)
3. 成交量放大
4. RSI 不过热
"""
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backtest.signal import Signal, SignalType
from strategies.base import BaseStrategy


class MomentumStrategy(BaseStrategy):
    """
    动量策略
    
    参数:
        lookback_period: 回看天数 (计算动量)
        holding_period: 预期持有天数
        top_n: 选股数量
        ma_period: 均线周期
        rsi_upper: RSI 上限 (避免过热)
        rsi_lower: RSI 下限 (确保强势)
        min_volume_ratio: 最小量比
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        default_params = {
            'lookback_period': 20,      # 20 日动量
            'holding_period': 5,        # 持有 5 天
            'top_n': 10,                # 选 10 只
            'ma_period': 20,            # 20 日均线
            'rsi_upper': 80,            # RSI 上限
            'rsi_lower': 50,            # RSI 下限
            'min_volume_ratio': 1.2,    # 最小量比
        }
        
        # 合并参数
        if params:
            default_params.update(params)
        
        super().__init__(default_params)
        self.name_str = f"动量策略 (N={self.get_param('lookback_period')})"
        
        # 内部状态
        self._last_buy_date: Dict[str, str] = {}  # 最后买入日期
        self._holding_stocks: set = set()  # 持仓股票
    
    def generate_signals(
        self,
        date: str,
        data: Dict,
        account: Any,
        market_data: Any = None
    ) -> List[Signal]:
        """生成交易信号"""
        signals = []
        
        if not market_data:
            return signals
        
        # 1. 检查持仓，生成卖出信号
        sell_signals = self._check_exit(date, data, account, market_data)
        signals.extend(sell_signals)
        
        # 2. 选股，生成买入信号
        buy_signals = self._select_stocks(date, data, account, market_data)
        signals.extend(buy_signals)
        
        return signals
    
    def _check_exit(
        self,
        date: str,
        data: Dict,
        account: Any,
        market_data: Any
    ) -> List[Signal]:
        """检查卖出条件"""
        signals = []
        
        for stock_code, position in list(account.positions.items()):
            # 获取股票代码格式
            ts_code = stock_code
            if '.' not in ts_code:
                ts_code = f"{ts_code}.SH" if ts_code.startswith('6') else f"{ts_code}.SZ"
            
            if ts_code not in data:
                continue
            
            quote = data[ts_code]
            
            # 检查持有时间
            holding_period = self.get_param('holding_period', 5)
            last_buy = self._last_buy_date.get(ts_code)
            
            if last_buy:
                from datetime import datetime
                try:
                    buy_date = datetime.strptime(last_buy, '%Y-%m-%d')
                    current_date = datetime.strptime(date, '%Y-%m-%d')
                    days_held = (current_date - buy_date).days
                    
                    # 达到持有期，卖出
                    if days_held >= holding_period:
                        signals.append(Signal(
                            stock_code=ts_code,
                            stock_name=position.stock_name,
                            action=SignalType.SELL,
                            price=quote.close,
                            volume=position.volume,
                            confidence=0.8,
                            reason=f"持有{days_held}天，达到目标",
                            date=date,
                            priority=5,
                        ))
                        self._holding_stocks.discard(ts_code)
                except:
                    pass
        
        return signals
    
    def _select_stocks(
        self,
        date: str,
        data: Dict,
        account: Any,
        market_data: Any
    ) -> List[Signal]:
        """选股并生成买入信号"""
        signals = []
        
        # 检查可用资金
        if account.cash < self.initial_capital * 0.1:  # 现金少于 10%
            return signals
        
        # 评分所有股票
        scored_stocks = []
        
        for ts_code, quote in data.items():
            # 跳过指数
            if ts_code.endswith('.SH') or ts_code.endswith('.SZ'):
                if ts_code.startswith('000') or ts_code.startswith('399'):
                    continue
            
            # 获取历史数据
            history = market_data.get_history(ts_code, date, self.get_param('lookback_period') + 10)
            
            if len(history) < self.get_param('lookback_period'):
                continue
            
            # 计算评分
            score = self._score_stock(history, quote)
            
            if score > 0:
                scored_stocks.append((ts_code, quote, score))
        
        # 按评分排序
        scored_stocks.sort(key=lambda x: x[2], reverse=True)
        
        # 选择 TOP N
        top_n = self.get_param('top_n', 10)
        selected = scored_stocks[:top_n]
        
        # 生成买入信号
        for ts_code, quote, score in selected:
            # 检查是否已持仓
            stock_code = ts_code.replace('.SH', '').replace('.SZ', '')
            if stock_code in account.positions:
                continue
            
            # 检查是否已在持仓集合中
            if ts_code in self._holding_stocks:
                continue
            
            # 计算买入数量 (每只股票分配 10% 资金)
            position_size = self.initial_capital * 0.10
            volume = int(position_size / quote.close / 100) * 100
            
            if volume < 100:
                continue
            
            signals.append(Signal(
                stock_code=ts_code,
                stock_name=self._get_stock_name(ts_code),
                action=SignalType.BUY,
                price=quote.close,
                volume=volume,
                confidence=min(score / 100, 1.0),
                reason=f"动量评分：{score:.1f}",
                date=date,
                hold_period=self.get_param('holding_period', 5),
                priority=3,
            ))
            
            self._holding_stocks.add(ts_code)
            self._last_buy_date[ts_code] = date
        
        return signals
    
    def _score_stock(self, history: List, quote: Any) -> float:
        """
        股票评分
        
        评分维度:
        1. 价格动量 (40 分)
        2. 均线趋势 (30 分)
        3. RSI 强度 (20 分)
        4. 成交量 (10 分)
        """
        scores = []
        weights = []
        
        # 1. 价格动量 (40 分)
        lookback = self.get_param('lookback_period', 20)
        momentum = self._calculate_momentum(
            [h.close for h in history],
            lookback
        )
        
        if momentum is not None:
            # 动量越强，分数越高
            momentum_score = min(momentum * 100, 40)  # 最多 40 分
            scores.append(max(0, momentum_score))
            weights.append(40)
        
        # 2. 均线趋势 (30 分)
        ma_period = self.get_param('ma_period', 20)
        prices = [h.close for h in history]
        
        if self._is_price_above_ma(prices, ma_period):
            scores.append(30)
        else:
            scores.append(0)
        weights.append(30)
        
        # 3. RSI 强度 (20 分)
        rsi = self._calculate_rsi(prices, 14)
        
        if rsi is not None:
            rsi_upper = self.get_param('rsi_upper', 80)
            rsi_lower = self.get_param('rsi_lower', 50)
            
            if rsi_lower <= rsi <= rsi_upper:
                # RSI 在合理区间
                rsi_score = 20 - abs(rsi - 65) / 15 * 10  # 65 最佳
                scores.append(max(0, rsi_score))
            else:
                scores.append(0)
            weights.append(20)
        
        # 4. 成交量 (10 分)
        if len(history) >= 5:
            avg_vol = sum(h.vol for h in history[-5:-1]) / 4
            if quote.vol > avg_vol * self.get_param('min_volume_ratio', 1.2):
                scores.append(10)
            else:
                scores.append(5)
            weights.append(10)
        
        # 计算加权总分
        if not scores:
            return 0
        
        total_score = sum(scores)
        return total_score
    
    def _get_stock_name(self, ts_code: str) -> str:
        """获取股票名称 (简化版)"""
        # 实际应用中可以从数据源获取
        return ts_code.split('.')[0]
    
    @property
    def initial_capital(self) -> float:
        """初始资金 (从账户获取)"""
        # 这里返回默认值，实际使用时会被覆盖
        return 1000000
