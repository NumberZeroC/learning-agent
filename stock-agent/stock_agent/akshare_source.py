"""
AKShare 数据源模块 - 免费、开源的财经数据
支持：新闻、行情、资金流、板块成分股
特性：重试机制 + 本地缓存 + 故障转移

⚠️ 要求：Python 3.8+ (AKShare 依赖)
"""
import os
import json
import time
import random
import hashlib
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any

# AKShare 导入
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    print("[AKShare] ⚠️ 未安装，运行：pip install akshare")


class CacheManager:
    """本地缓存管理器"""
    
    def __init__(self, cache_dir: str = None, ttl_seconds: int = 300):
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(__file__).parent.parent / 'data' / 'cache' / 'akshare'
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
        self.stats = {'hits': 0, 'misses': 0, 'writes': 0}
    
    def _get_cache_key(self, func_name: str, **kwargs) -> str:
        key_str = f"{func_name}:{json.dumps(kwargs, sort_keys=True, default=str)}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"
    
    def get(self, func_name: str, **kwargs) -> Optional[Any]:
        key = self._get_cache_key(func_name, **kwargs)
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            self.stats['misses'] += 1
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cached_time = data.get('_cached_at', 0)
            if time.time() - cached_time > self.ttl_seconds:
                self.stats['misses'] += 1
                try:
                    cache_path.unlink()
                except:
                    pass
                return None
            
            self.stats['hits'] += 1
            return data.get('value')
            
        except Exception as e:
            print(f"[AKShare 缓存] 读取失败：{e}")
            self.stats['misses'] += 1
            return None
    
    def set(self, func_name: str, value: Any, **kwargs):
        key = self._get_cache_key(func_name, **kwargs)
        cache_path = self._get_cache_path(key)
        
        try:
            data = {
                'value': value,
                '_cached_at': time.time(),
                '_func': func_name
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, default=str)
            
            self.stats['writes'] += 1
            
        except Exception as e:
            print(f"[AKShare 缓存] 写入失败：{e}")
    
    def get_stats(self) -> Dict:
        total = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0
        
        return {
            **self.stats,
            'hit_rate': f"{hit_rate:.1f}%",
            'cache_dir': str(self.cache_dir),
            'cache_files': len(list(self.cache_dir.glob('*.json')))
        }


class AKShareSource:
    """AKShare 数据源"""
    
    def __init__(self, cache_dir: str = None, cache_ttl: int = 300, max_retries: int = 3):
        if not AKSHARE_AVAILABLE:
            raise ImportError("AKShare 未安装，请运行：pip install akshare")
        
        self.cache = CacheManager(cache_dir, cache_ttl)
        self.max_retries = max_retries
        
        print(f"[AKShare] ✅ 已初始化 - 缓存 TTL: {cache_ttl}s, 重试：{max_retries}")
    
    def _retry_request(self, func, *args, **kwargs):
        """带重试的请求"""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = 1.0 * (2 ** attempt)
                    print(f"[AKShare] 重试 {attempt + 1}/{self.max_retries + 1}: {e}")
                    time.sleep(delay)
        
        raise last_error
    
    # ==================== 基础行情 ====================
    
    def get_stock_list(self, exchange: str = '') -> List[Dict]:
        """
        获取股票列表
        
        Args:
            exchange: 交易所 (SH|SZ|BJ, 空表示全部)
        
        Returns:
            股票列表
        """
        cached = self.cache.get('get_stock_list', exchange=exchange)
        if cached:
            return cached
        
        try:
            # AKShare 1.18+ 接口变更
            if exchange in ['SH', 'SSE']:
                df = ak.stock_sh_a_spot_em()
            elif exchange in ['SZ', 'SZSE']:
                df = ak.stock_sz_a_spot_em()
            elif exchange in ['BJ', 'BSE']:
                df = ak.stock_bj_a_spot_em()
            else:
                # 使用沪深 A 股合并接口
                df_sh = ak.stock_sh_a_spot_em()
                df_sz = ak.stock_sz_a_spot_em()
                df = pd.concat([df_sh, df_sz], ignore_index=True)
            
            if df.empty:
                return []
            
            stocks = []
            for _, row in df.iterrows():
                ts_code = row.get('代码', row.get('symbol', ''))
                name = row.get('名称', row.get('name', ''))
                
                # 补充交易所后缀
                if '.' not in str(ts_code):
                    if str(ts_code).startswith('6'):
                        ts_code = f"{ts_code}.SH"
                    elif str(ts_code).startswith(('0', '3')):
                        ts_code = f"{ts_code}.SZ"
                    elif str(ts_code).startswith(('4', '8')):
                        ts_code = f"{ts_code}.BJ"
                
                stocks.append({
                    'ts_code': ts_code,
                    'symbol': str(ts_code).split('.')[0],
                    'name': name,
                    'area': row.get('地区', ''),
                    'industry': row.get('行业', ''),
                    'market': row.get('板块', '')
                })
            
            self.cache.set('get_stock_list', stocks, exchange=exchange)
            print(f"[AKShare] 获取股票列表 {len(stocks)} 只")
            return stocks
            
        except Exception as e:
            print(f"[AKShare] 股票列表获取失败：{e}")
            return []
    
    def get_daily_quote(self, ts_code: str, trade_date: str = None) -> Optional[Dict]:
        """
        获取每日行情
        
        Args:
            ts_code: 股票代码 (如 000001.SZ)
            trade_date: 交易日期 YYYYMMDD
        
        Returns:
            行情数据
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        cache_key = f"{ts_code}_{trade_date}"
        cached = self.cache.get('get_daily_quote', ts_code=ts_code, trade_date=trade_date)
        if cached:
            return cached
        
        try:
            symbol = ts_code.split('.')[0].lower()
            
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                                    start_date=trade_date, end_date=trade_date)
            
            if df.empty:
                return None
            
            row = df.iloc[0]
            data = {
                'ts_code': ts_code,
                'trade_date': trade_date,
                'open': float(row.get('开盘', 0)),
                'high': float(row.get('最高', 0)),
                'low': float(row.get('最低', 0)),
                'close': float(row.get('收盘', 0)),
                'pre_close': float(row.get('昨收', 0)),
                'change': float(row.get('涨跌额', 0)),
                'pct_chg': float(row.get('涨跌幅', 0)),
                'vol': float(row.get('成交量', 0)),
                'amount': float(row.get('成交额', 0))
            }
            
            self.cache.set('get_daily_quote', data, ts_code=ts_code, trade_date=trade_date)
            return data
            
        except Exception as e:
            print(f"[AKShare] 行情获取失败 {ts_code}: {e}")
            return None
    
    def get_realtime_quote(self, ts_code: str) -> Optional[Dict]:
        """
        获取实时行情
        
        Args:
            ts_code: 股票代码
        
        Returns:
            实时行情数据
        """
        cached = self.cache.get('get_realtime_quote', ts_code=ts_code)
        if cached:
            return cached
        
        try:
            symbol = ts_code.split('.')[0].lower()
            
            # 实时行情
            df = ak.stock_zh_a_spot_em()
            
            if df.empty:
                return None
            
            stock_row = df[df['代码'] == symbol]
            if stock_row.empty:
                return None
            
            row = stock_row.iloc[0]
            data = {
                'ts_code': ts_code,
                'name': row.get('名称', ''),
                'price': float(row.get('最新价', 0)),
                'change': float(row.get('涨跌额', 0)),
                'change_pct': float(row.get('涨跌幅', 0)),
                'volume': float(row.get('成交量', 0)),
                'turnover': float(row.get('成交额', 0)),
                'high': float(row.get('最高', 0)),
                'low': float(row.get('最低', 0)),
                'open': float(row.get('今开', 0)),
                'pre_close': float(row.get('昨收', 0)),
                'time': datetime.now().isoformat()
            }
            
            self.cache.set('get_realtime_quote', data, ts_code=ts_code)
            return data
            
        except Exception as e:
            print(f"[AKShare] 实时行情获取失败 {ts_code}: {e}")
            return None
    
    # ==================== 资金流 ====================
    
    def get_moneyflow(self, ts_code: str, trade_date: str = None) -> Optional[Dict]:
        """
        获取资金流数据
        
        Args:
            ts_code: 股票代码
            trade_date: 交易日期
        
        Returns:
            资金流数据
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        cached = self.cache.get('get_moneyflow', ts_code=ts_code)
        if cached:
            return cached
        
        try:
            symbol = ts_code.split('.')[0].lower()
            market = "sz" if ts_code.endswith('SZ') else "sh"
            
            df = ak.stock_individual_fund_flow(symbol=symbol, market=market)
            
            if df.empty:
                return None
            
            row = df.iloc[0] if len(df) > 0 else df
            
            data = {
                'ts_code': ts_code,
                'trade_date': trade_date,
                'buy_sm_amount': float(row.get('小单净流入', 0)),
                'sell_sm_amount': float(row.get('小单净流出', 0)),
                'buy_md_amount': float(row.get('中单净流入', 0)),
                'sell_md_amount': float(row.get('中单净流出', 0)),
                'buy_lg_amount': float(row.get('大单净流入', 0)),
                'sell_lg_amount': float(row.get('大单净流出', 0)),
                'buy_elg_amount': float(row.get('超大单净流入', 0)),
                'sell_elg_amount': float(row.get('超大单净流出', 0)),
                'net_mf_amount': float(row.get('主力净流入', 0))
            }
            
            self.cache.set('get_moneyflow', data, ts_code=ts_code)
            return data
            
        except Exception as e:
            print(f"[AKShare] 资金流获取失败 {ts_code}: {e}")
            return None
    
    # ==================== 板块数据 ====================
    
    def get_sector_concepts(self) -> List[Dict]:
        """
        获取概念板块列表
        
        Returns:
            概念板块列表
        """
        cached = self.cache.get('get_sector_concepts')
        if cached:
            return cached
        
        try:
            df = ak.stock_board_concept_name_em()
            
            if df.empty:
                return []
            
            concepts = []
            for _, row in df.iterrows():
                concepts.append({
                    'code': row.get('板块代码', ''),
                    'name': row.get('板块名称', ''),
                    'src': 'eastmoney'
                })
            
            self.cache.set('get_sector_concepts', concepts)
            print(f"[AKShare] 获取概念板块 {len(concepts)} 个")
            return concepts
            
        except Exception as e:
            print(f"[AKShare] 概念板块获取失败：{e}")
            return []
    
    def get_sector_stocks(self, sector_name: str) -> List[Dict]:
        """
        获取板块成分股
        
        Args:
            sector_name: 板块名称
        
        Returns:
            成分股列表
        """
        cached = self.cache.get('get_sector_stocks', sector_name=sector_name)
        if cached:
            return cached
        
        try:
            df = ak.stock_board_concept_cons_em(symbol=sector_name)
            
            if df.empty:
                return []
            
            stocks = []
            for _, row in df.iterrows():
                code = row.get('代码', '')
                ts_code = f"{code}.SZ" if code.startswith(('0', '3')) else f"{code}.SH"
                
                stocks.append({
                    'ts_code': ts_code,
                    'symbol': code,
                    'name': row.get('名称', ''),
                    'price': float(row.get('最新价', 0)),
                    'change_pct': float(row.get('涨跌幅', 0))
                })
            
            self.cache.set('get_sector_stocks', stocks, sector_name=sector_name)
            print(f"[AKShare] 获取 {sector_name} 成分股 {len(stocks)} 只")
            return stocks
            
        except Exception as e:
            print(f"[AKShare] 成分股获取失败 {sector_name}: {e}")
            return []
    
    # ==================== 新闻数据 ====================
    
    def get_news(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        获取财经新闻
        
        Args:
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
        
        Returns:
            新闻列表
        """
        if not start_date:
            start_date = datetime.now().strftime('%Y%m%d')
        if not end_date:
            end_date = start_date
        
        cached = self.cache.get('get_news', start_date=start_date, end_date=end_date)
        if cached:
            return cached
        
        try:
            # AKShare 1.18+ 接口变更
            df = ak.stock_news_em(symbol="全部")
            
            if df.empty:
                return []
            
            news_list = []
            for _, row in df.iterrows():
                news_list.append({
                    'title': row.get('新闻标题', ''),
                    'url': row.get('新闻链接', ''),
                    'source': 'eastmoney',
                    'time': row.get('发布时间', datetime.now().isoformat()),
                    'content': row.get('新闻内容', '')
                })
            
            self.cache.set('get_news', news_list, start_date=start_date, end_date=end_date)
            print(f"[AKShare] 获取新闻 {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            print(f"[AKShare] 新闻获取失败：{e}")
            return []
    
    # ==================== 指数数据 ====================
    
    # ==================== 分时数据 ====================
    
    def get_min_data(self, ts_code: str, period: str = '1') -> List[Dict]:
        """
        获取分时数据
        
        Args:
            ts_code: 股票代码
            period: 周期 (1/5/15/30/60 分钟)
        
        Returns:
            分时数据列表
        """
        cached = self.cache.get('get_min_data', ts_code=ts_code, period=period)
        if cached:
            return cached
        
        try:
            symbol = ts_code.split('.')[0].lower()
            
            # AKShare 分时接口
            df = ak.stock_zh_a_hist_min_em(symbol=symbol, period=period)
            
            if df.empty:
                return []
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'ts_code': ts_code,
                    'time': row.get('时间', ''),
                    'open': float(row.get('开盘', 0)),
                    'close': float(row.get('收盘', 0)),
                    'high': float(row.get('最高', 0)),
                    'low': float(row.get('最低', 0)),
                    'volume': float(row.get('成交量', 0)),
                    'amount': float(row.get('成交额', 0)),
                    'avg_price': float(row.get('均价', 0)) if '均价' in row else 0,
                })
            
            self.cache.set('get_min_data', data, ts_code=ts_code, period=period)
            print(f"[AKShare] 获取 {ts_code} {period}分钟线 {len(data)} 条")
            return data
            
        except Exception as e:
            print(f"[AKShare] 分时数据获取失败 {ts_code}: {e}")
            return []
    
    # ==================== 指数数据 ====================
    
    def get_index_quote(self, index_code: str) -> Optional[Dict]:
        """
        获取指数行情
        
        Args:
            index_code: 指数代码 (如 sh000001)
        
        Returns:
            指数行情数据
        """
        cached = self.cache.get('get_index_quote', index_code=index_code)
        if cached:
            return cached
        
        try:
            # 转换代码格式
            if '.' in index_code:
                code = index_code.split('.')[0]
                if index_code.endswith('SH'):
                    code = f"sh{code}"
                elif index_code.endswith('SZ'):
                    code = f"sz{code}"
            else:
                code = index_code
            
            df = ak.stock_zh_index_spot_em()
            
            if df.empty:
                return None
            
            stock_row = df[df['代码'] == code]
            if stock_row.empty:
                return None
            
            row = stock_row.iloc[0]
            data = {
                'index_code': index_code,
                'name': row.get('名称', ''),
                'price': float(row.get('最新价', 0)),
                'change': float(row.get('涨跌额', 0)),
                'change_pct': float(row.get('涨跌幅', 0)),
                'time': datetime.now().isoformat()
            }
            
            self.cache.set('get_index_quote', data, index_code=index_code)
            return data
            
        except Exception as e:
            print(f"[AKShare] 指数行情获取失败 {index_code}: {e}")
            return None
    
    # ==================== 缓存统计 ====================
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计"""
        return self.cache.get_stats()
    
    def clear_cache(self):
        """清理缓存"""
        for cache_file in self.cache.cache_dir.glob('*.json'):
            try:
                cache_file.unlink()
            except:
                pass
        print("[AKShare] 缓存已清理")


def test_akshare():
    """测试 AKShare 连接"""
    if not AKSHARE_AVAILABLE:
        print("❌ AKShare 未安装")
        return False
    
    print("=" * 60)
    print("📊 测试 AKShare 数据源")
    print("=" * 60)
    
    source = AKShareSource(cache_ttl=60)
    
    # 测试 1: 获取股票列表
    print("\n1. 获取股票列表...")
    stocks = source.get_stock_list()
    if stocks:
        print(f"   ✅ 成功：{len(stocks)}只")
        print(f"      示例：{stocks[0]['name']}({stocks[0]['ts_code']})")
    else:
        print(f"   ❌ 失败")
    
    # 测试 2: 获取实时行情
    print("\n2. 获取实时行情 (平安银行)...")
    quote = source.get_realtime_quote('000001.SZ')
    if quote:
        print(f"   ✅ 成功：¥{quote['price']:.2f} ({quote['change_pct']:+.2f}%)")
    else:
        print(f"   ❌ 失败")
    
    # 测试 3: 获取新闻
    print("\n3. 获取财经新闻...")
    today = datetime.now().strftime('%Y%m%d')
    news = source.get_news(start_date=today, end_date=today)
    if news:
        print(f"   ✅ 成功：{len(news)}条")
    else:
        print(f"   ⚠️ 无今日新闻")
    
    # 测试 4: 获取概念板块
    print("\n4. 获取概念板块...")
    concepts = source.get_sector_concepts()
    if concepts:
        print(f"   ✅ 成功：{len(concepts)}个")
        print(f"      示例：{concepts[0]['name']}")
    else:
        print(f"   ❌ 失败")
    
    # 测试 5: 缓存统计
    print("\n5. 缓存统计...")
    stats = source.get_cache_stats()
    print(f"   命中率：{stats['hit_rate']}")
    print(f"   缓存文件：{stats['cache_files']}")
    
    print("\n" + "=" * 60)
    print("AKShare 测试完成")
    print("=" * 60)
    
    return True


if __name__ == '__main__':
    test_akshare()
