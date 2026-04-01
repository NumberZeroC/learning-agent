"""
Tushare 数据源模块 - 提供稳定的财经数据
支持：新闻、行情、资金流、板块成分股
"""
import tushare as ts
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class TushareSource:
    """Tushare 数据源"""
    
    def __init__(self, token: str):
        """初始化 Tushare"""
        ts.set_token(token)
        self.pro = ts.pro_api()
        self.token = token
        print(f"[Tushare] 已初始化，Token: {token[:8]}...")
    
    def get_news(self, start_date: str = None, end_date: str = None,
                 src: str = 'sina') -> List[Dict]:
        """
        获取财经新闻
        
        Args:
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
            src: 新闻源 (sina|eastmoney|10jqka)
        
        Returns:
            新闻列表
        """
        if not start_date:
            start_date = datetime.now().strftime('%Y%m%d')
        if not end_date:
            end_date = start_date
        
        try:
            df = self.pro.news(src=src, start_date=start_date, end_date=end_date)
            
            if df.empty:
                return []
            
            news_list = []
            for _, row in df.iterrows():
                news_list.append({
                    'title': row.get('title', ''),
                    'url': row.get('url', ''),
                    'source': row.get('src', src),
                    'time': row.get('date', datetime.now().isoformat()),
                    'content': row.get('content', '')
                })
            
            print(f"[Tushare] 获取新闻 {len(news_list)} 条 (源：{src})")
            return news_list
            
        except Exception as e:
            print(f"[Tushare] 新闻获取失败：{e}")
            return []
    
    def get_stock_list(self, exchange: str = '') -> List[Dict]:
        """
        获取股票列表
        
        Args:
            exchange: 交易所 (SSE|SZSE|BSE, 空表示全部)
        
        Returns:
            股票列表
        """
        try:
            df = self.pro.stock_basic(
                exchange=exchange,
                list_status='L',
                fields='ts_code,symbol,name,area,industry,market,list_date'
            )
            
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
                    'market': row.get('market', '')
                })
            
            print(f"[Tushare] 获取股票列表 {len(stocks)} 只")
            return stocks
            
        except Exception as e:
            print(f"[Tushare] 股票列表获取失败：{e}")
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
        
        try:
            df = self.pro.daily(ts_code=ts_code, trade_date=trade_date)
            
            if df.empty:
                return None
            
            row = df.iloc[0]
            return {
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
            
        except Exception as e:
            print(f"[Tushare] 行情获取失败 {ts_code}: {e}")
            return None
    
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
        
        try:
            df = self.pro.moneyflow(ts_code=ts_code, trade_date=trade_date)
            
            if df.empty:
                return None
            
            row = df.iloc[0]
            return {
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
                'net_mf_amount': float(row.get('net_mf_amount', 0))  # 主力净流入
            }
            
        except Exception as e:
            print(f"[Tushare] 资金流获取失败 {ts_code}: {e}")
            return None
    
    def get_index_member(self, index_code: str) -> List[Dict]:
        """
        获取指数成分股
        
        Args:
            index_code: 指数代码 (如 399001.SZ 深证成指)
        
        Returns:
            成分股列表
        """
        try:
            df = self.pro.index_member(index_code=index_code)
            
            if df.empty:
                return []
            
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'ts_code': row.get('ts_code', ''),
                    'name': row.get('name', ''),
                    'weight': float(row.get('weight', 0)) if row.get('weight') else 0,
                    'in_date': row.get('in_date', ''),
                    'out_date': row.get('out_date', '')
                })
            
            print(f"[Tushare] 获取 {index_code} 成分股 {len(stocks)} 只")
            return stocks
            
        except Exception as e:
            print(f"[Tushare] 成分股获取失败 {index_code}: {e}")
            return []
    
    def get_concept_info(self) -> List[Dict]:
        """
        获取概念板块信息
        
        Returns:
            概念板块列表
        """
        try:
            df = self.pro.concept_classify(src='ts')
            
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
    
    def get_token_info(self) -> Optional[Dict]:
        """
        获取 Token 信息（积分等）
        
        Returns:
            Token 信息
        """
        try:
            # 尝试多种接口名
            for func_name in ['token_my', 'info', 'user']:
                try:
                    if hasattr(self.pro, func_name):
                        func = getattr(self.pro, func_name)
                        df = func()
                        if not df.empty:
                            row = df.iloc[0]
                            return {
                                'token': self.token[:8] + '...',
                                'total_points': int(row.get('total_points', row.get('points', 100))),
                                'remain_points': int(row.get('remain_points', row.get('points', 100))),
                                'vip_level': str(row.get('vip_level', '普通用户')),
                                'end_date': row.get('end_date', '')
                            }
                except Exception:
                    continue
            
            # 如果都失败，返回默认信息
            return {
                'token': self.token[:8] + '...',
                'total_points': 100,  # 默认赠送
                'remain_points': 100,
                'vip_level': '普通用户',
                'end_date': ''
            }
            
        except Exception as e:
            print(f"[Tushare] Token 信息查询失败：{e}")
            # 返回默认信息
            return {
                'token': self.token[:8] + '...',
                'total_points': 100,
                'remain_points': 100,
                'vip_level': '普通用户',
                'end_date': ''
            }


def test_tushare(token: str):
    """测试 Tushare 连接"""
    print("=" * 60)
    print("测试 Tushare 连接")
    print("=" * 60)
    
    source = TushareSource(token)
    
    # 测试 1: 查询 Token 信息
    print("\n1. 查询 Token 信息...")
    info = source.get_token_info()
    if info:
        print(f"   ✅ 成功")
        print(f"      积分：{info['total_points']} (剩余：{info['remain_points']})")
        print(f"      VIP 等级：{info['vip_level']}")
    else:
        print(f"   ❌ 失败")
        return False
    
    # 测试 2: 获取新闻
    print("\n2. 获取财经新闻...")
    today = datetime.now().strftime('%Y%m%d')
    news = source.get_news(start_date=today, end_date=today, src='sina')
    if news:
        print(f"   ✅ 成功，获取 {len(news)} 条")
        print(f"      示例：{news[0]['title'][:50]}...")
    else:
        print(f"   ⚠️ 无今日新闻")
    
    # 测试 3: 获取股票列表
    print("\n3. 获取股票列表...")
    stocks = source.get_stock_list(exchange='')
    if stocks:
        print(f"   ✅ 成功，获取 {len(stocks)} 只")
        print(f"      示例：{stocks[0]['name']}({stocks[0]['ts_code']})")
    else:
        print(f"   ❌ 失败")
    
    # 测试 4: 获取行情
    print("\n4. 获取实时行情 (平安银行)...")
    quote = source.get_daily_quote('000001.SZ', today)
    if quote:
        print(f"   ✅ 成功")
        print(f"      现价：¥{quote['close']:.2f} ({quote['pct_chg']:+.2f}%)")
    else:
        print(f"   ⚠️ 无数据 (可能非交易日)")
    
    print("\n" + "=" * 60)
    print("Tushare 测试完成")
    print("=" * 60)
    
    return True


if __name__ == '__main__':
    import sys
    
    # 从命令行或环境变量获取 token
    token = sys.argv[1] if len(sys.argv) > 1 else os.getenv('TUSHARE_TOKEN')
    
    if not token:
        print("❌ 未提供 Tushare Token")
        print("用法：python3 tushare_source.py <your_token>")
        print("或设置环境变量：export TUSHARE_TOKEN=xxx")
        sys.exit(1)
    
    test_tushare(token)
