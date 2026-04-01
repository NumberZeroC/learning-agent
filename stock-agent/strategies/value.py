"""
价值策略

基于基本面因子的选股策略

核心逻辑:
1. 低估值 (低 PE、低 PB)
2. 高盈利 (高 ROE)
3. 稳定增长 (营收增长)
4. 财务健康
"""
from typing import List, Dict, Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backtest.signal import Signal, SignalType
from strategies.base import BaseStrategy


class ValueStrategy(BaseStrategy):
    """
    价值策略
    
    参数:
        pe_max: 最大 PE
        pb_max: 最大 PB
        roe_min: 最小 ROE
        growth_min: 最小营收增长率
        top_n: 选股数量
        holding_period: 持有天数
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        default_params = {
            'pe_max': 30,             # PE 上限
            'pb_max': 5,              # PB 上限
            'roe_min': 10,            # ROE 下限 (%)
            'growth_min': 10,         # 营收增长下限 (%)
            'top_n': 10,              # 选 10 只
            'holding_period': 20,     # 持有 20 天
        }
        
        if params:
            default_params.update(params)
        
        super().__init__(default_params)
        self.name_str = f"价值策略 (PE<{self.get_param('pe_max')}, ROE>{self.get_param('roe_min')}%)"
    
    def generate_signals(
        self,
        date: str,
        data: Dict,
        account: Any,
        market_data: Any = None
    ) -> List[Signal]:
        """生成交易信号"""
        signals = []
        
        # 简化实现：基于技术面的价值选股
        # 实际应用中应结合基本面数据
        
        if not market_data:
            return signals
        
        # 选股
        buy_signals = self._select_value_stocks(date, data, account, market_data)
        signals.extend(buy_signals)
        
        return signals
    
    def _select_value_stocks(
        self,
        date: str,
        data: Dict,
        account: Any,
        market_data: Any
    ) -> List[Signal]:
        """选择价值股"""
        signals = []
        
        # 简化版：使用技术指标模拟价值因子
        scored_stocks = []
        
        for ts_code, quote in data.items():
            # 跳过指数
            if ts_code.startswith('000') or ts_code.startswith('399'):
                continue
            
            # 获取历史数据
            history = market_data.get_history(ts_code, date, 60)
            
            if len(history) < 20:
                continue
            
            # 评分
            score = self._score_value_stock(history, quote)
            
            if score > 50:  # 及格线
                scored_stocks.append((ts_code, quote, score))
        
        # 排序
        scored_stocks.sort(key=lambda x: x[2], reverse=True)
        
        # 选择 TOP N
        top_n = self.get_param('top_n', 10)
        
        for ts_code, quote, score in scored_stocks[:top_n]:
            stock_code = ts_code.replace('.SH', '').replace('.SZ', '')
            
            if stock_code in account.positions:
                continue
            
            # 计算买入数量
            position_size = 1000000 * 0.10
            volume = int(position_size / quote.close / 100) * 100
            
            if volume < 100:
                continue
            
            signals.append(Signal(
                stock_code=ts_code,
                stock_name=ts_code.split('.')[0],
                action=SignalType.BUY,
                price=quote.close,
                volume=volume,
                confidence=min(score / 100, 1.0),
                reason=f"价值评分：{score:.1f}",
                date=date,
                hold_period=self.get_param('holding_period', 20),
            ))
        
        return signals
    
    def _score_value_stock(self, history: List, quote: Any) -> float:
        """价值股评分"""
        score = 50  # 基础分
        
        prices = [h.close for h in history]
        
        # 1. 估值 (模拟：价格相对 60 日的位置)
        if len(prices) >= 60:
            high_60 = max(prices[-60:])
            low_60 = min(prices[-60:])
            if high_60 > low_60:
                position = (quote.close - low_60) / (high_60 - low_60)
                # 低位加分
                score += (1 - position) * 20
        
        # 2. 稳定性 (波动率低加分)
        volatility = self._calculate_volatility(prices, 20)
        if volatility and quote.close > 0:
            vol_ratio = volatility / quote.close
            if vol_ratio < 0.03:  # 低波动
                score += 15
            elif vol_ratio < 0.05:
                score += 8
        
        # 3. 趋势 (均线上方加分)
        if self._is_price_above_ma(prices, 20):
            score += 10
        
        if self._is_price_above_ma(prices, 60):
            score += 10
        
        return min(score, 100)
