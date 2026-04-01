"""
市场数据模块

负责加载和管理历史市场数据
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd


@dataclass
class DailyQuote:
    """
    日线行情数据
    
    Attributes:
        ts_code: 股票代码 (TS 格式：600519.SH)
        trade_date: 交易日期 (YYYYMMDD)
        open: 开盘价
        high: 最高价
        low: 最低价
        close: 收盘价
        pre_close: 昨收价
        change: 涨跌额
        pct_chg: 涨跌幅 (%)
        vol: 成交量 (手)
        amount: 成交额 (千元)
    """
    
    ts_code: str
    trade_date: str
    open: float
    high: float
    low: float
    close: float
    pre_close: float
    change: float
    pct_chg: float
    vol: float
    amount: float
    
    @property
    def date_str(self) -> str:
        """格式化的日期字符串 (YYYY-MM-DD)"""
        if len(self.trade_date) == 8:
            return f"{self.trade_date[:4]}-{self.trade_date[4:6]}-{self.trade_date[6:8]}"
        return self.trade_date
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'ts_code': self.ts_code,
            'trade_date': self.trade_date,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'pre_close': self.pre_close,
            'change': self.change,
            'pct_chg': self.pct_chg,
            'vol': self.vol,
            'amount': self.amount,
        }


@dataclass
class IndexQuote:
    """指数行情"""
    
    ts_code: str
    trade_date: str
    close: float
    pct_chg: float
    
    @property
    def date_str(self) -> str:
        if len(self.trade_date) == 8:
            return f"{self.trade_date[:4]}-{self.trade_date[4:6]}-{self.trade_date[6:8]}"
        return self.trade_date


class MarketData:
    """
    市场数据管理器
    
    负责加载、缓存和提供历史市场数据
    """
    
    def __init__(self, data_source=None, cache_dir: str = None):
        """
        初始化市场数据
        
        Args:
            data_source: 数据源 (TushareSource 或 AKShareSource)
            cache_dir: 缓存目录
        """
        self.data_source = data_source
        self.cache_dir = Path(cache_dir) if cache_dir else None
        
        # 数据缓存
        self._daily_quotes: Dict[str, pd.DataFrame] = {}  # ts_code -> DataFrame
        self._index_quotes: Dict[str, pd.DataFrame] = {}
        self._trading_dates: List[str] = []
        
        # 统计
        self.stats = {
            'stocks_loaded': 0,
            'days_loaded': 0,
            'cache_hits': 0,
            'cache_misses': 0,
        }
    
    def load_daily_data(
        self,
        ts_codes: List[str],
        start_date: str,
        end_date: str,
        force_reload: bool = False
    ) -> bool:
        """
        加载股票日线数据
        
        Args:
            ts_codes: 股票代码列表
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            force_reload: 强制重新加载
            
        Returns:
            是否成功
        """
        if not self.data_source:
            print("[MarketData] ⚠️ 未配置数据源")
            return False
        
        # 转换日期格式
        start = start_date.replace('-', '')
        end = end_date.replace('-', '')
        
        for ts_code in ts_codes:
            try:
                # 尝试从数据源获取
                df = self.data_source.get_daily_history(
                    ts_code=ts_code,
                    start_date=start,
                    end_date=end
                )
                
                if df is not None and len(df) > 0:
                    self._daily_quotes[ts_code] = df
                    self.stats['stocks_loaded'] += 1
                    self.stats['days_loaded'] += len(df)
                    
            except Exception as e:
                print(f"[MarketData] ⚠️ 加载 {ts_code} 失败：{e}")
                continue
        
        return self.stats['stocks_loaded'] > 0
    
    def get_quote(self, ts_code: str, date: str) -> Optional[DailyQuote]:
        """
        获取指定日期的行情
        
        Args:
            ts_code: 股票代码
            date: 日期 (YYYY-MM-DD)
            
        Returns:
            日线行情数据
        """
        if ts_code not in self._daily_quotes:
            return None
        
        df = self._daily_quotes[ts_code]
        date_fmt = date.replace('-', '')
        
        # 查找匹配的日期
        mask = df['trade_date'].astype(str) == date_fmt
        row = df[mask]
        
        if len(row) == 0:
            return None
        
        row = row.iloc[0]
        return DailyQuote(
            ts_code=ts_code,
            trade_date=str(row['trade_date']),
            open=float(row.get('open', 0)),
            high=float(row.get('high', 0)),
            low=float(row.get('low', 0)),
            close=float(row.get('close', 0)),
            pre_close=float(row.get('pre_close', 0)),
            change=float(row.get('change', 0)),
            pct_chg=float(row.get('pct_chg', 0)),
            vol=float(row.get('vol', 0)),
            amount=float(row.get('amount', 0)),
        )
    
    def get_history(
        self,
        ts_code: str,
        end_date: str,
        days: int
    ) -> List[DailyQuote]:
        """
        获取历史行情 (用于计算技术指标)
        
        Args:
            ts_code: 股票代码
            end_date: 结束日期
            days: 获取天数
            
        Returns:
            历史行情列表 (按时间正序)
        """
        if ts_code not in self._daily_quotes:
            return []
        
        df = self._daily_quotes[ts_code]
        end_fmt = end_date.replace('-', '')
        
        # 筛选日期
        mask = df['trade_date'].astype(str) <= end_fmt
        filtered = df[mask].tail(days)
        
        quotes = []
        for _, row in filtered.iterrows():
            quotes.append(DailyQuote(
                ts_code=ts_code,
                trade_date=str(row['trade_date']),
                open=float(row.get('open', 0)),
                high=float(row.get('high', 0)),
                low=float(row.get('low', 0)),
                close=float(row.get('close', 0)),
                pre_close=float(row.get('pre_close', 0)),
                change=float(row.get('change', 0)),
                pct_chg=float(row.get('pct_chg', 0)),
                vol=float(row.get('vol', 0)),
                amount=float(row.get('amount', 0)),
            ))
        
        return quotes
    
    def get_all_quotes(self, date: str) -> Dict[str, DailyQuote]:
        """
        获取所有股票在指定日期的行情
        
        Args:
            date: 日期 (YYYY-MM-DD)
            
        Returns:
            股票代码 -> 行情的字典
        """
        result = {}
        date_fmt = date.replace('-', '')
        
        for ts_code, df in self._daily_quotes.items():
            mask = df['trade_date'].astype(str) == date_fmt
            row = df[mask]
            
            if len(row) > 0:
                row = row.iloc[0]
                result[ts_code] = DailyQuote(
                    ts_code=ts_code,
                    trade_date=str(row['trade_date']),
                    open=float(row.get('open', 0)),
                    high=float(row.get('high', 0)),
                    low=float(row.get('low', 0)),
                    close=float(row.get('close', 0)),
                    pre_close=float(row.get('pre_close', 0)),
                    change=float(row.get('change', 0)),
                    pct_chg=float(row.get('pct_chg', 0)),
                    vol=float(row.get('vol', 0)),
                    amount=float(row.get('amount', 0)),
                )
        
        return result
    
    def get_trading_dates(
        self,
        start_date: str,
        end_date: str,
        index_code: str = '000001.SH'
    ) -> List[str]:
        """
        获取交易日期列表
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            index_code: 用于判断交易日的指数代码
            
        Returns:
            交易日期列表 (YYYY-MM-DD 格式)
        """
        if self._trading_dates:
            return self._trading_dates
        
        # 从指数数据中提取交易日
        if index_code in self._daily_quotes:
            df = self._daily_quotes[index_code]
            start = start_date.replace('-', '')
            end = end_date.replace('-', '')
            
            mask = (df['trade_date'].astype(str) >= start) & \
                   (df['trade_date'].astype(str) <= end)
            dates = df[mask]['trade_date'].astype(str).tolist()
            
            # 转换为 YYYY-MM-DD 格式
            self._trading_dates = [
                f"{d[:4]}-{d[4:6]}-{d[6:8]}" for d in sorted(dates)
            ]
        
        return self._trading_dates
    
    def get_stats(self) -> dict:
        """获取加载统计"""
        return self.stats.copy()
