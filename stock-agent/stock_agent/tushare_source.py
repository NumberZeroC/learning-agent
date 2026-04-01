"""
Tushare Pro 数据源模块

参考 stock-notification 项目的 tushare_pro_source.py 实现
支持：日线行情、资金流、龙虎榜、指数行情等
"""
import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any


class TushareSource:
    """Tushare Pro 数据源"""
    
    def __init__(self, token: str = None, cache_dir: str = None, cache_ttl: int = 600):
        """
        初始化 Tushare 数据源
        
        Args:
            token: Tushare Token
            cache_dir: 缓存目录
            cache_ttl: 缓存有效期（秒）
        """
        self.token = token or os.getenv('TUSHARE_TOKEN')
        
        if not self.token:
            raise ValueError("Tushare Token 未配置，请设置 token 参数或 TUSHARE_TOKEN 环境变量")
        
        # 初始化 Tushare Pro
        try:
            import tushare as ts
            ts.set_token(self.token)
            self.pro = ts.pro_api()
            print(f"[Tushare] ✅ 已连接")
        except ImportError:
            raise ImportError("请安装 tushare: pip install tushare")
        
        # 缓存配置
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(__file__).parent.parent / 'data' / 'cache' / 'tushare'
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = cache_ttl
        
        # 缓存统计
        self.cache_stats = {'hits': 0, 'misses': 0}
    
    def _get_cache_key(self, func_name: str, **kwargs) -> str:
        """生成缓存键"""
        params = json.dumps(kwargs, sort_keys=True, default=str)
        return f"{func_name}:{params}"
    
    def _get_cache_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        import hashlib
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{hash_key}.json"
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """从缓存获取数据"""
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            self.cache_stats['misses'] += 1
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查是否过期
            if time.time() - data.get('_cached_at', 0) > self.cache_ttl:
                cache_path.unlink()
                self.cache_stats['misses'] += 1
                return None
            
            self.cache_stats['hits'] += 1
            return data.get('value')
            
        except Exception:
            return None
    
    def _set_cache(self, key: str, value: Any) -> None:
        """保存数据到缓存"""
        cache_path = self._get_cache_path(key)
        
        try:
            data = {
                'value': value,
                '_cached_at': time.time(),
                '_key': key
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, default=str)
                
        except Exception as e:
            print(f"[Tushare] 缓存写入失败：{e}")
    
    # ==================== 基础数据 ====================
    
    def get_stock_basic(self) -> List[Dict]:
        """
        获取股票列表
        
        Returns:
            股票列表
        """
        cache_key = self._get_cache_key('stock_basic')
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            df = self.pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,market,list_date')
            
            if df.empty:
                return []
            
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'ts_code': row.get('ts_code', ''),
                    'symbol': row.get('symbol', ''),
                    'name': row.get('name', ''),
                    'area': row.get('area', ''),
                    'industry': row.get('industry', ''),
                    'market': row.get('market', ''),
                    'list_date': row.get('list_date', '')
                })
            
            self._set_cache(cache_key, stocks)
            print(f"[Tushare] 获取股票列表 {len(stocks)} 只")
            return stocks
            
        except Exception as e:
            print(f"[Tushare] 股票列表获取失败：{e}")
            return []
    
    # ==================== 日线行情 ====================
    
    def get_daily(self, ts_code: str, trade_date: str = None) -> Optional[Dict]:
        """
        获取日线行情
        
        Args:
            ts_code: 股票代码（如 600519.SH）
            trade_date: 交易日期（YYYYMMDD）
        
        Returns:
            日线数据
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        cache_key = self._get_cache_key('daily', ts_code=ts_code, trade_date=trade_date)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            df = self.pro.daily(ts_code=ts_code, trade_date=trade_date)
            
            if df.empty:
                return None
            
            row = df.iloc[0]
            data = {
                'ts_code': ts_code,
                'trade_date': trade_date,
                'open': float(row.get('open', 0)),
                'high': float(row.get('high', 0)),
                'low': float(row.get('low', 0)),
                'close': float(row.get('close', 0)),
                'pre_close': float(row.get('pre_close', 0)),
                'change': float(row.get('change', 0)),
                'pct_chg': float(row.get('pct_chg', 0)),  # 涨跌幅%
                'vol': float(row.get('vol', 0)),  # 成交量（手）
                'amount': float(row.get('amount', 0))  # 成交额（千元）
            }
            
            self._set_cache(cache_key, data)
            return data
            
        except Exception as e:
            print(f"[Tushare] 日线获取失败 {ts_code}: {e}")
            return None
    
    def get_daily_batch(self, ts_codes: List[str], trade_date: str = None) -> Dict[str, Dict]:
        """
        批量获取日线数据
        
        Args:
            ts_codes: 股票代码列表
            trade_date: 交易日期
        
        Returns:
            日线数据字典
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        results = {}
        for i, ts_code in enumerate(ts_codes):
            if i % 10 == 0:
                print(f"[Tushare] 获取日线 {i+1}/{len(ts_codes)}")
            
            data = self.get_daily(ts_code, trade_date)
            if data:
                results[ts_code] = data
        
        return results
    
    # ==================== 资金流 ====================
    
    def get_moneyflow(self, ts_code: str, trade_date: str = None) -> Optional[Dict]:
        """
        获取资金流数据（300 积分）
        
        Args:
            ts_code: 股票代码
            trade_date: 交易日期
        
        Returns:
            资金流数据
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        cache_key = self._get_cache_key('moneyflow', ts_code=ts_code, trade_date=trade_date)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            df = self.pro.moneyflow(ts_code=ts_code, trade_date=trade_date)
            
            if df.empty:
                return None
            
            row = df.iloc[0]
            data = {
                'ts_code': ts_code,
                'trade_date': trade_date,
                'buy_sm_amount': float(row.get('buy_sm_amount', 0)),  # 小单买入
                'sell_sm_amount': float(row.get('sell_sm_amount', 0)),  # 小单卖出
                'buy_md_amount': float(row.get('buy_md_amount', 0)),  # 中单买入
                'sell_md_amount': float(row.get('sell_md_amount', 0)),  # 中单卖出
                'buy_lg_amount': float(row.get('buy_lg_amount', 0)),  # 大单买入
                'sell_lg_amount': float(row.get('sell_lg_amount', 0)),  # 大单卖出
                'buy_elg_amount': float(row.get('buy_elg_amount', 0)),  # 特大单买入
                'sell_elg_amount': float(row.get('sell_elg_amount', 0)),  # 特大单卖出
                'net_mf_amount': float(row.get('net_mf_amount', 0)),  # 主力净流入
            }
            
            self._set_cache(cache_key, data)
            return data
            
        except Exception as e:
            print(f"[Tushare] 资金流获取失败 {ts_code}: {e}")
            return None
    
    # ==================== 指数行情 ====================
    
    def get_index_daily(self, ts_code: str, trade_date: str = None) -> Optional[Dict]:
        """
        获取指数行情
        
        Args:
            ts_code: 指数代码（如 000001.SH）
            trade_date: 交易日期
        
        Returns:
            指数行情数据
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        cache_key = self._get_cache_key('index_daily', ts_code=ts_code, trade_date=trade_date)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            df = self.pro.index_daily(ts_code=ts_code, trade_date=trade_date)
            
            if df.empty:
                return None
            
            row = df.iloc[0]
            data = {
                'ts_code': ts_code,
                'trade_date': trade_date,
                'open': float(row.get('open', 0)),
                'high': float(row.get('high', 0)),
                'low': float(row.get('low', 0)),
                'close': float(row.get('close', 0)),
                'pre_close': float(row.get('pre_close', 0)),
                'change': float(row.get('change', 0)),
                'pct_chg': float(row.get('pct_chg', 0)),
                'vol': float(row.get('vol', 0)),
                'amount': float(row.get('amount', 0))
            }
            
            self._set_cache(cache_key, data)
            return data
            
        except Exception as e:
            print(f"[Tushare] 指数行情获取失败 {ts_code}: {e}")
            return None
    
    def get_major_indices(self, trade_date: str = None) -> Dict[str, Dict]:
        """
        获取主要指数行情
        
        Returns:
            指数行情字典
        """
        indices = {
            'shanghai': '000001.SH',  # 上证指数
            'shenzhen': '399001.SZ',  # 深证成指
            'chinext': '399006.SZ',   # 创业板指
            'hs300': '000300.SH',     # 沪深 300
            'zheng50': '000016.SH',   # 上证 50
        }
        
        results = {}
        for name, code in indices.items():
            data = self.get_index_daily(code, trade_date)
            if data:
                results[name] = data
        
        return results
    
    # ==================== 龙虎榜 ====================
    
    def get_top_list(self, trade_date: str = None) -> List[Dict]:
        """
        获取龙虎榜每日数据
        
        Args:
            trade_date: 交易日期
        
        Returns:
            龙虎榜数据列表
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        cache_key = self._get_cache_key('top_list', trade_date=trade_date)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            df = self.pro.top_list(trade_date=trade_date)
            
            if df.empty:
                return []
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'ts_code': row.get('ts_code', ''),
                    'name': row.get('name', ''),
                    'trade_date': trade_date,
                    'close': float(row.get('close', 0)),
                    'pct_change': float(row.get('pct_change', 0)),
                    'turnover_rate': float(row.get('turnover_rate', 0)),
                    'amount': float(row.get('amount', 0)),
                    'l_buy': float(row.get('l_buy', 0)),
                    'l_sell': float(row.get('l_sell', 0)),
                    'net_amount': float(row.get('net_amount', 0)),
                    'reason': row.get('reason', '')
                })
            
            self._set_cache(cache_key, data)
            print(f"[Tushare] 获取龙虎榜 {len(data)} 只")
            return data
            
        except Exception as e:
            print(f"[Tushare] 龙虎榜获取失败：{e}")
            return []
    
    # ==================== 融资融券 ====================
    
    def get_margin(self, ts_code: str = None, trade_date: str = None) -> List[Dict]:
        """
        获取融资融券数据
        
        Args:
            ts_code: 股票代码（空表示全市场）
            trade_date: 交易日期
        
        Returns:
            融资融券数据列表
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        try:
            if ts_code:
                df = self.pro.margin(ts_code=ts_code, trade_date=trade_date)
            else:
                df = self.pro.margin(trade_date=trade_date)
            
            if df.empty:
                return []
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'ts_code': row.get('ts_code', ''),
                    'trade_date': trade_date,
                    'buy_amount': float(row.get('buy_amount', 0)),  # 融资买入额
                    'sell_amount': float(row.get('sell_amount', 0)),  # 融券卖出量
                    'buy_repay_amount': float(row.get('buy_repay_amount', 0)),  # 融资偿还额
                    'sell_repay_amount': float(row.get('sell_repay_amount', 0)),  # 融券偿还量
                    'fin_balance': float(row.get('fin_balance', 0)),  # 融资余额
                    'sec_balance': float(row.get('sec_balance', 0)),  # 融券余额
                })
            
            return data
            
        except Exception as e:
            print(f"[Tushare] 融资融券获取失败：{e}")
            return []
    
    # ==================== 板块数据 ====================
    
    def get_concept_list(self) -> List[Dict]:
        """
        获取概念板块列表
        
        Returns:
            概念板块列表
        """
        try:
            df = self.pro.concept_src()
            
            if df.empty:
                return []
            
            concepts = []
            for _, row in df.iterrows():
                concepts.append({
                    'code': row.get('code', ''),
                    'name': row.get('name', ''),
                    'src': row.get('src', '')
                })
            
            print(f"[Tushare] 获取概念板块 {len(concepts)} 个")
            return concepts
            
        except Exception as e:
            print(f"[Tushare] 概念板块获取失败：{e}")
            return []
    
    def get_concept_detail(self, code: str) -> List[Dict]:
        """
        获取概念板块成分股
        
        Args:
            code: 板块代码
        
        Returns:
            成分股列表
        """
        try:
            df = self.pro.concept_detail(code=code)
            
            if df.empty:
                return []
            
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'ts_code': row.get('ts_code', ''),
                    'name': row.get('name', ''),
                    'weight': float(row.get('weight', 0)) if 'weight' in row else 0
                })
            
            print(f"[Tushare] 获取 {code} 成分股 {len(stocks)} 只")
            return stocks
            
        except Exception as e:
            print(f"[Tushare] 成分股获取失败：{e}")
            return []
    
    # ==================== 缓存统计 ====================
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计"""
        total = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total * 100) if total > 0 else 0
        
        return {
            **self.cache_stats,
            'hit_rate': f"{hit_rate:.1f}%",
            'cache_dir': str(self.cache_dir),
            'cache_files': len(list(self.cache_dir.glob('*.json')))
        }
    
    def clear_cache(self) -> None:
        """清理缓存"""
        for cache_file in self.cache_dir.glob('*.json'):
            try:
                cache_file.unlink()
            except Exception as e:
                print(f"[Tushare] 清理缓存失败：{e}")
        
        print("[Tushare] 缓存已清理")
    
    # ==================== 财务数据 (2000 积分可用) ====================
    
    def get_fina_indicator(self, ts_code: str, ann_date: str = None) -> List[Dict]:
        """
        获取财务指标数据
        
        Args:
            ts_code: 股票代码
            ann_date: 公告日期（YYYYMMDD）
        
        Returns:
            财务指标列表
        """
        try:
            if ann_date:
                df = self.pro.fina_indicator(ts_code=ts_code, ann_date=ann_date)
            else:
                # 获取最新 4 期财报
                df = self.pro.fina_indicator(ts_code=ts_code)
            
            if df.empty:
                return []
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'ts_code': row.get('ts_code', ''),
                    'ann_date': row.get('ann_date', ''),
                    'end_date': row.get('end_date', ''),
                    'eps': float(row.get('eps', 0)),  # 每股收益
                    'dt_eps': float(row.get('dt_eps', 0)),  # 扣非每股收益
                    'revenue': float(row.get('revenue', 0)),  # 营业收入
                    'operate_profit': float(row.get('operate_profit', 0)),  # 营业利润
                    'net_profit': float(row.get('net_profit', 0)),  # 净利润
                    'roe': float(row.get('roe', 0)),  # 净资产收益率
                    'roe_wa': float(row.get('roe_wa', 0)),  # 加权 ROE
                    'gross_margin': float(row.get('gross_margin', 0)),  # 毛利率
                    'operating_margin': float(row.get('operating_margin', 0)),  # 营业利润率
                    'net_margin': float(row.get('net_margin', 0)),  # 净利率
                    'current_ratio': float(row.get('current_ratio', 0)),  # 流动比率
                    'quick_ratio': float(row.get('quick_ratio', 0)),  # 速动比率
                    'debt_to_assets': float(row.get('debt_to_assets', 0)),  # 资产负债率
                    'revenue_yoy': float(row.get('revenue_yoy', 0)),  # 营收增长率
                    'net_profit_yoy': float(row.get('net_profit_yoy', 0)),  # 净利润增长率
                })
            
            print(f"[Tushare] 获取 {ts_code} 财务指标 {len(data)} 期")
            return data
            
        except Exception as e:
            print(f"[Tushare] 财务指标获取失败 {ts_code}: {e}")
            return []
    
    def get_daily_basic(self, ts_code: str = None, trade_date: str = None) -> List[Dict]:
        """
        获取每日基本面指标
        
        Args:
            ts_code: 股票代码（空表示全市场）
            trade_date: 交易日期
        
        Returns:
            基本面指标列表
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        try:
            if ts_code:
                df = self.pro.daily_basic(ts_code=ts_code, trade_date=trade_date)
            else:
                df = self.pro.daily_basic(trade_date=trade_date)
            
            if df.empty:
                return []
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'ts_code': row.get('ts_code', ''),
                    'trade_date': trade_date,
                    'close': float(row.get('close', 0)),
                    'pe': float(row.get('pe', 0)),  # 市盈率
                    'pe_ttm': float(row.get('pe_ttm', 0)),  # 市盈率 TTM
                    'pb': float(row.get('pb', 0)),  # 市净率
                    'ps': float(row.get('ps', 0)),  # 市销率
                    'dv_ratio': float(row.get('dv_ratio', 0)),  # 股息率
                    'total_mv': float(row.get('total_mv', 0)),  # 总市值
                    'circ_mv': float(row.get('circ_mv', 0)),  # 流通市值
                    'turnover_rate': float(row.get('turnover_rate', 0)),  # 换手率
                    'volume_ratio': float(row.get('volume_ratio', 0)),  # 量比
                    'pe_forecast': float(row.get('pe_forecast', 0)) if 'pe_forecast' in row else 0,  # 预测 PE
                })
            
            return data
            
        except Exception as e:
            print(f"[Tushare] 每日基本面获取失败：{e}")
            return []
    
    # ==================== 复权因子 ====================
    
    def get_adj_factor(self, ts_code: str, trade_date: str = None) -> Optional[Dict]:
        """
        获取复权因子
        
        Args:
            ts_code: 股票代码
            trade_date: 交易日期
        
        Returns:
            复权因子数据
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        cache_key = self._get_cache_key('adj_factor', ts_code=ts_code, trade_date=trade_date)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            df = self.pro.adj_factor(ts_code=ts_code, trade_date=trade_date)
            
            if df.empty:
                return None
            
            row = df.iloc[0]
            data = {
                'ts_code': ts_code,
                'trade_date': trade_date,
                'adj_factor': float(row.get('adj_factor', 1)),
                'close': float(row.get('close', 0)),
                'adj_close': float(row.get('close', 0)) * float(row.get('adj_factor', 1)) / 100  # 复权价
            }
            
            self._set_cache(cache_key, data)
            return data
            
        except Exception as e:
            print(f"[Tushare] 复权因子获取失败 {ts_code}: {e}")
            return None
    
    # ==================== 分钟线数据 ====================
    
    def get_min(self, ts_code: str, trade_date: str = None, min_type: str = '5') -> List[Dict]:
        """
        获取分钟线数据
        
        Args:
            ts_code: 股票代码
            trade_date: 交易日期
            min_type: 分钟类型 (1/5/15/30/60)
        
        Returns:
            分钟线数据列表
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        cache_key = self._get_cache_key('min', ts_code=ts_code, trade_date=trade_date, min_type=min_type)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            df = self.pro.min(ts_code=ts_code, trade_date=trade_date, min_type=min_type)
            
            if df.empty:
                return []
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'ts_code': ts_code,
                    'trade_time': row.get('trade_time', ''),
                    'open': float(row.get('open', 0)),
                    'high': float(row.get('high', 0)),
                    'low': float(row.get('low', 0)),
                    'close': float(row.get('close', 0)),
                    'vol': float(row.get('vol', 0)),
                    'amount': float(row.get('amount', 0)),
                })
            
            self._set_cache(cache_key, data)
            print(f"[Tushare] 获取 {ts_code} {min_type}分钟线 {len(data)} 条")
            return data
            
        except Exception as e:
            print(f"[Tushare] 分钟线获取失败 {ts_code}: {e}")
            return []
    
    # ==================== 北向资金 ====================
    
    def get_north_flow(self, trade_date: str = None) -> Optional[Dict]:
        """
        获取北向资金汇总数据
        
        Args:
            trade_date: 交易日期
        
        Returns:
            北向资金数据
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        cache_key = self._get_cache_key('north_flow', trade_date=trade_date)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            df = self.pro.moneyflow_hsgt(trade_date=trade_date)
            
            if df.empty:
                return None
            
            row = df.iloc[0]
            data = {
                'trade_date': trade_date,
                'ggt_ss': float(row.get('ggt_ss', 0)),  # 沪股通净流入
                'ggt_sz': float(row.get('ggt_sz', 0)),  # 深股通净流入
                'hgt': float(row.get('hgt', 0)),  # 沪股通成交
                'sgt': float(row.get('sgt', 0)),  # 深股通成交
                'north_net_in': float(row.get('ggt_ss', 0)) + float(row.get('ggt_sz', 0)),  # 总净流入
            }
            
            self._set_cache(cache_key, data)
            return data
            
        except Exception as e:
            print(f"[Tushare] 北向资金获取失败：{e}")
            return None
    
    def get_north_hold(self, ts_code: str = None, trade_date: str = None) -> List[Dict]:
        """
        获取北向资金持仓持股
        
        Args:
            ts_code: 股票代码
            trade_date: 交易日期
        
        Returns:
            持仓数据列表
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        try:
            if ts_code:
                df = self.pro.hk_hold(ts_code=ts_code, trade_date=trade_date)
            else:
                df = self.pro.hk_hold(trade_date=trade_date)
            
            if df.empty:
                return []
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'ts_code': row.get('ts_code', ''),
                    'trade_date': trade_date,
                    'hold_vol': float(row.get('hold_vol', 0)),  # 持股数量
                    'hold_ratio': float(row.get('hold_ratio', 0)),  # 持股比例
                    'close': float(row.get('close', 0)),
                })
            
            return data
            
        except Exception as e:
            print(f"[Tushare] 北向持仓获取失败：{e}")
            return []
    
    # ==================== 停复牌数据 ====================
    
    def get_suspend_d(self, ts_code: str = None, trade_date: str = None) -> List[Dict]:
        """
        获取停复牌数据
        
        Args:
            ts_code: 股票代码
            trade_date: 交易日期
        
        Returns:
            停复牌数据列表
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        try:
            if ts_code:
                df = self.pro.suspend_d(ts_code=ts_code, trade_date=trade_date)
            else:
                df = self.pro.suspend_d(trade_date=trade_date)
            
            if df.empty:
                return []
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'ts_code': row.get('ts_code', ''),
                    'trade_date': trade_date,
                    'suspend_type': row.get('suspend_type', ''),
                    'reason': row.get('reason', ''),
                })
            
            return data
            
        except Exception as e:
            print(f"[Tushare] 停复牌获取失败：{e}")
            return []
    
    # ==================== 股东数据 ====================
    
    def get_top10_holders(self, ts_code: str, ann_date: str = None) -> List[Dict]:
        """
        获取前十大股东
        
        Args:
            ts_code: 股票代码
            ann_date: 公告日期
        
        Returns:
            股东列表
        """
        try:
            if ann_date:
                df = self.pro.top10_holders(ts_code=ts_code, ann_date=ann_date)
            else:
                df = self.pro.top10_holders(ts_code=ts_code)
            
            if df.empty:
                return []
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'ts_code': row.get('ts_code', ''),
                    'ann_date': row.get('ann_date', ''),
                    'holder_name': row.get('holder_name', ''),
                    'holder_type': row.get('holder_type', ''),  # 股东类型
                    'hold_vol': float(row.get('hold_vol', 0)),  # 持股数量
                    'hold_ratio': float(row.get('hold_ratio', 0)),  # 持股比例
                })
            
            print(f"[Tushare] 获取 {ts_code} 前十大股东 {len(data)} 个")
            return data
            
        except Exception as e:
            print(f"[Tushare] 股东数据获取失败 {ts_code}: {e}")
            return []
    
    # ==================== 业绩快报 ====================
    
    def get_forecast(self, ts_code: str = None, ann_date: str = None) -> List[Dict]:
        """
        获取业绩预告
        
        Args:
            ts_code: 股票代码
            ann_date: 公告日期
        
        Returns:
            业绩预告列表
        """
        try:
            if ts_code:
                df = self.pro.forecast(ts_code=ts_code, ann_date=ann_date)
            else:
                df = self.pro.forecast(ann_date=ann_date)
            
            if df.empty:
                return []
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'ts_code': row.get('ts_code', ''),
                    'ann_date': row.get('ann_date', ''),
                    'end_date': row.get('end_date', ''),
                    'type': row.get('type', ''),  # 预告类型
                    'net_profit_min': float(row.get('net_profit_min', 0)),  # 净利润下限
                    'net_profit_max': float(row.get('net_profit_max', 0)),  # 净利润上限
                    'net_profit_yoy_min': float(row.get('net_profit_yoy_min', 0)),  # 净利润增速下限
                    'net_profit_yoy_max': float(row.get('net_profit_yoy_max', 0)),  # 净利润增速上限
                })
            
            return data
            
        except Exception as e:
            print(f"[Tushare] 业绩预告获取失败：{e}")
            return []
    
    # ==================== 行业板块 ====================
    
    def get_industry_list(self) -> List[Dict]:
        """
        获取行业板块列表
        
        Returns:
            行业板块列表
        """
        try:
            df = self.pro.index_classify(level='L1')
            
            if df.empty:
                return []
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'index_code': row.get('index_code', ''),
                    'industry_name': row.get('industry_name', ''),
                    'level': row.get('level', ''),
                })
            
            print(f"[Tushare] 获取行业板块 {len(data)} 个")
            return data
            
        except Exception as e:
            print(f"[Tushare] 行业板块获取失败：{e}")
            return []
    
    def get_industry_members(self, index_code: str) -> List[Dict]:
        """
        获取行业成分股
        
        Args:
            index_code: 行业指数代码
        
        Returns:
            成分股列表
        """
        try:
            df = self.pro.index_member(index_code=index_code)
            
            if df.empty:
                return []
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'ts_code': row.get('ts_code', ''),
                    'name': row.get('name', ''),
                    'weight': float(row.get('weight', 0)) if 'weight' in row else 0,
                })
            
            print(f"[Tushare] 获取 {index_code} 成分股 {len(data)} 只")
            return data
            
        except Exception as e:
            print(f"[Tushare] 行业成分股获取失败：{e}")
            return []
    
    # ==================== 数据大全 ====================
    
    def get_all_available_data(self) -> Dict:
        """
        获取所有可用数据接口列表
        
        Returns:
            数据接口字典
        """
        return {
            '基础行情': [
                'get_stock_basic', 'get_daily', 'get_daily_batch',
                'get_min', 'get_adj_factor'
            ],
            '指数数据': [
                'get_index_daily', 'get_major_indices'
            ],
            '资金流': [
                'get_moneyflow', 'get_north_flow', 'get_north_hold',
                'get_margin', 'get_top_list'
            ],
            '财务数据': [
                'get_fina_indicator', 'get_daily_basic', 'get_forecast'
            ],
            '板块数据': [
                'get_concept_list', 'get_concept_detail',
                'get_industry_list', 'get_industry_members'
            ],
            '股东数据': [
                'get_top10_holders', 'get_suspend_d'
            ]
        }
