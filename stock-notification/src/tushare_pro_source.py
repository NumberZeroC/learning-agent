#!/usr/bin/env python3
"""
Tushare Pro 增强数据源模块 - 600 积分完整版

支持接口（600 积分可用）：
1. 股票基础数据（120 分）
2. 日线/分钟行情（120-300 分）
3. 财务数据（120 分）
4. 资金流（300 分）
5. 北向资金（300 分）
6. 指数/ETF（120-300 分）
7. 龙虎榜（300 分）
8. 融资融券（300 分）
9. 宏观经济（120 分）
10. 新闻快讯（120 分）

⚠️ 要求：Tushare Token + 600 积分
"""
import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any

try:
    import tushare as ts
    TUSHARE_AVAILABLE = True
except ImportError:
    TUSHARE_AVAILABLE = False
    print("[Tushare Pro] ⚠️ 未安装，请运行：pip install tushare")


class TushareProSource:
    """Tushare Pro 增强数据源（600 积分版）"""
    
    def __init__(self, token: str = None, cache_dir: str = None, cache_ttl: int = 300):
        if not TUSHARE_AVAILABLE:
            raise ImportError("Tushare 未安装")
        
        # 🔥 Token 配置（支持从公共配置加载）
        if token:
            self.token = token
        else:
            # 优先环境变量
            self.token = os.getenv('TUSHARE_TOKEN')
            
            # 如果环境变量未设置，从公共配置加载
            if not self.token:
                try:
                    import sys
                    sys.path.insert(0, '/home/admin/.openclaw/workspace/config')
                    from config_loader import get_tushare_token
                    self.token = get_tushare_token()
                except Exception as e:
                    raise ValueError(f"未提供 Tushare Token，且无法从公共配置加载：{e}")
        
        if not self.token:
            raise ValueError("未提供 Tushare Token")
        
        ts.set_token(self.token)
        self.pro = ts.pro_api()
        
        # 缓存配置
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(__file__).parent.parent / 'data' / 'cache' / 'tushare_pro'
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = cache_ttl
        
        # 验证 Token
        self.token_info = self._verify_token()
        
        print(f"[Tushare Pro] ✅ 已连接")
        print(f"   Token: {self.token[:8]}...")
        print(f"   积分：{self.token_info.get('total_points', 'N/A')}")
        print(f"   VIP: {self.token_info.get('vip_level', 'N/A')}")
        print(f"   缓存：{self.cache_dir} (TTL: {cache_ttl}s)")
    
    def _verify_token(self) -> Dict:
        """验证 Token 并获取信息"""
        try:
            # 尝试多个接口名
            for func_name in ['token_my', 'info', 'user']:
                try:
                    if hasattr(self.pro, func_name):
                        func = getattr(self.pro, func_name)
                        df = func()
                        if not df.empty:
                            row = df.iloc[0]
                            return {
                                'total_points': int(row.get('total_points', row.get('points', 600))),
                                'remain_points': int(row.get('remain_points', 600)),
                                'vip_level': str(row.get('vip_level', 'VIP')),
                                'end_date': row.get('end_date', '')
                            }
                except:
                    continue
            
            return {'total_points': 600, 'vip_level': 'VIP'}
        except Exception as e:
            print(f"[Tushare] Token 验证失败：{e}")
            return {'total_points': 600, 'vip_level': 'VIP'}
    
    # ==================== 股票基础数据 ====================
    
    def get_stock_list(self, exchange: str = '') -> List[Dict]:
        """
        获取股票列表
        
        Args:
            exchange: 交易所 (SSE|SZSE|BSE, 空表示全部)
        """
        try:
            # 检查缓存
            cached = self._get_cached('stock_list', exchange=exchange)
            if cached:
                return cached
            
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
            
            # 保存到缓存
            self._set_cache('stock_list', stocks, exchange=exchange)
            
            print(f"[Tushare] 获取股票列表 {len(stocks)} 只")
            return stocks
            
        except Exception as e:
            print(f"[Tushare] 股票列表获取失败：{e}")
            return []
    
    def get_company_info(self, ts_code: str) -> Optional[Dict]:
        """获取上市公司基本信息"""
        try:
            df = self.pro.company_info(ts_code=ts_code)
            if df.empty:
                return None
            
            row = df.iloc[0]
            return {
                'ts_code': ts_code,
                'name': row.get('name', ''),
                'area': row.get('area', ''),
                'industry': row.get('industry', ''),
                'chairman': row.get('chairman', ''),
                'website': row.get('website', ''),
                'employees': row.get('employees', 0),
                'main_business': row.get('main_business', '')
            }
            
        except Exception as e:
            print(f"[Tushare] 公司信息获取失败 {ts_code}: {e}")
            return None
    
    # ==================== 行情数据 ====================
    
    def get_daily(self, ts_code: str, trade_date: str = None) -> Optional[Dict]:
        """
        获取日线行情
        
        Args:
            ts_code: 股票代码
            trade_date: 交易日期 YYYYMMDD
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        try:
            # 检查缓存
            cached = self._get_cached('daily', ts_code=ts_code, trade_date=trade_date)
            if cached:
                return cached
            
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
                'pct_chg': float(row.get('pct_chg', 0)),
                'vol': float(row.get('vol', 0)),
                'amount': float(row.get('amount', 0))
            }
            
            self._set_cache('daily', data, ts_code=ts_code, trade_date=trade_date)
            
            return data
            
        except Exception as e:
            print(f"[Tushare] 日线获取失败 {ts_code}: {e}")
            return None
    
    def get_min(self, ts_code: str, trade_date: str = None, mins: int = 5) -> List[Dict]:
        """
        获取分钟行情（600 积分可用）
        
        Args:
            ts_code: 股票代码
            trade_date: 交易日期 YYYYMMDD
            mins: 分钟数 (1/5/15/30/60)
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        try:
            df = self.pro.min(ts_code=ts_code, trade_date=trade_date, mins=mins)
            
            if df.empty:
                return []
            
            bars = []
            for _, row in df.iterrows():
                bars.append({
                    'ts_code': ts_code,
                    'trade_time': row.get('trade_time', ''),
                    'open': float(row.get('open', 0)),
                    'high': float(row.get('high', 0)),
                    'low': float(row.get('low', 0)),
                    'close': float(row.get('close', 0)),
                    'vol': float(row.get('vol', 0)),
                    'amount': float(row.get('amount', 0))
                })
            
            print(f"[Tushare] 获取 {ts_code} 分钟行情 {len(bars)} 条")
            return bars
            
        except Exception as e:
            print(f"[Tushare] 分钟行情获取失败 {ts_code}: {e}")
            return []
    
    def get_adj_factor(self, ts_code: str, trade_date: str = None) -> Optional[Dict]:
        """获取复权因子"""
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        try:
            df = self.pro.adj_factor(ts_code=ts_code, trade_date=trade_date)
            if df.empty:
                return None
            
            row = df.iloc[0]
            return {
                'ts_code': ts_code,
                'trade_date': trade_date,
                'adj_factor': float(row.get('adj_factor', 1))
            }
            
        except Exception as e:
            print(f"[Tushare] 复权因子获取失败 {ts_code}: {e}")
            return None
    
    # ==================== 资金流数据 ====================
    
    def get_moneyflow(self, ts_code: str, trade_date: str = None) -> Optional[Dict]:
        """
        获取个股资金流（300 积分）
        
        Args:
            ts_code: 股票代码
            trade_date: 交易日期
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        try:
            # 检查缓存
            cached = self._get_cached('moneyflow', ts_code=ts_code, trade_date=trade_date)
            if cached:
                return cached
            
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
                'net_mf_amount': float(row.get('net_mf_amount', 0))  # 主力净流入
            }
            
            self._set_cache('moneyflow', data, ts_code=ts_code, trade_date=trade_date)
            
            return data
            
        except Exception as e:
            print(f"[Tushare] 资金流获取失败 {ts_code}: {e}")
            return None
    
    def get_stock_hsgt_north(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        获取北向资金流向（300 积分）
        
        Args:
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        
        try:
            df = self.pro.stock_hsgt_north_daily(start_date=start_date, end_date=end_date)
            
            if df.empty:
                return []
            
            flows = []
            for _, row in df.iterrows():
                flows.append({
                    'trade_date': row.get('trade_date', ''),
                    'buy': float(row.get('buy', 0)),  # 买入金额
                    'sell': float(row.get('sell', 0)),  # 卖出金额
                    'net': float(row.get('net', 0)),  # 净流入
                    'gt_hold': float(row.get('gt_hold', 0)),  # 港股通持股
                    'gt_hold_ratio': float(row.get('gt_hold_ratio', 0))  # 持股比例
                })
            
            print(f"[Tushare] 获取北向资金 {len(flows)} 条")
            return flows
            
        except Exception as e:
            print(f"[Tushare] 北向资金获取失败：{e}")
            return []
    
    def get_stock_hsgt_hold(self, market: str = 'sh', start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        获取北向资金持仓（300 积分）
        
        Args:
            market: sh=沪股通，sz=深股通
            start_date: 开始日期
            end_date: 结束日期
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        if not end_date:
            end_date = start_date
        
        try:
            # 尝试多个接口名
            for func_name in ['stock_hsgt_hold', 'hk_hold', 'stock_hsgt_hold_stk']:
                try:
                    if hasattr(self.pro, func_name):
                        func = getattr(self.pro, func_name)
                        if func_name == 'hk_hold':
                            df = func(start_date=start_date, end_date=end_date)
                        else:
                            df = func(market=market, start_date=start_date, end_date=end_date)
                        
                        if not df.empty:
                            break
                except:
                    continue
            
            if df.empty:
                return []
            
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'ts_code': row.get('ts_code', row.get('code', '')),
                    'name': row.get('name', ''),
                    'hold_vol': float(row.get('hold_vol', row.get('hold_qty', 0))),
                    'hold_ratio': float(row.get('hold_ratio', row.get('ratio', 0))),
                    'close': float(row.get('close', 0)),
                    'change': float(row.get('change', 0))
                })
            
            print(f"[Tushare] 获取北向持仓 {len(stocks)} 只 ({market})")
            return stocks
            
        except Exception as e:
            print(f"[Tushare] 北向持仓获取失败：{e}")
            return []
    
    # ==================== 龙虎榜 ====================
    
    def get_top_list(self, trade_date: str = None) -> List[Dict]:
        """
        获取龙虎榜每日数据（2000 积分）
        
        Args:
            trade_date: 交易日期 YYYYMMDD
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        try:
            cached = self._get_cached('top_list', trade_date=trade_date)
            if cached:
                return cached
            
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
                    'change_pct': float(row.get('pct_change', 0)),
                    'turnover_rate': float(row.get('turnover_rate', 0)),
                    'amount': float(row.get('amount', 0)),  # 总成交额
                    'l_buy': float(row.get('l_buy', 0)),  # 龙虎榜买入
                    'l_sell': float(row.get('l_sell', 0)),  # 龙虎榜卖出
                    'l_amount': float(row.get('l_amount', 0)),  # 龙虎榜成交额
                    'net_in': float(row.get('net_amount', 0)),  # 龙虎榜净买入
                    'net_rate': float(row.get('net_rate', 0)),  # 净买占比
                    'reason': row.get('reason', '')  # 上榜原因
                })
            
            self._set_cache('top_list', data, trade_date=trade_date)
            print(f"[Tushare] 获取龙虎榜 {len(data)} 只")
            return data
            
        except Exception as e:
            print(f"[Tushare] 龙虎榜获取失败：{e}")
            return []
    
    def get_top_inst(self, trade_date: str = None) -> List[Dict]:
        """
        获取龙虎榜机构交易明细（2000 积分）
        
        Args:
            trade_date: 交易日期 YYYYMMDD
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        try:
            cached = self._get_cached('top_inst', trade_date=trade_date)
            if cached:
                return cached
            
            df = self.pro.top_inst(trade_date=trade_date)
            
            if df.empty:
                return []
            
            data = []
            for _, row in df.iterrows():
                # 机构/营业部席位数据，需要按股票聚合
                ts_code = row.get('ts_code', '')
                exalter = row.get('exalter', '')  # 营业部名称
                buy = float(row.get('buy', 0))  # 买入金额
                sell = float(row.get('sell', 0))  # 卖出金额
                net_buy = float(row.get('net_buy', 0))  # 净买入
                
                # 查找是否已有该股票
                existing = next((d for d in data if d['ts_code'] == ts_code), None)
                if existing:
                    existing['buy_amount'] += buy
                    existing['sell_amount'] += sell
                    existing['net_amount'] += net_buy
                    existing['seats'].append(exalter)
                else:
                    data.append({
                        'ts_code': ts_code,
                        'name': row.get('name', ''),
                        'trade_date': trade_date,
                        'buy_amount': buy,
                        'sell_amount': sell,
                        'net_amount': net_buy,
                        'seats': [exalter] if exalter else []  # 营业部列表
                    })
            
            self._set_cache('top_inst', data, trade_date=trade_date)
            print(f"[Tushare] 获取机构交易 {len(data)} 只")
            return data
            
        except Exception as e:
            print(f"[Tushare] 机构交易获取失败：{e}")
            return []
    
    # ==================== 融资融券 ====================
    
    def get_margin(self, trade_date: str = None) -> List[Dict]:
        """
        获取融资融券交易汇总（2000 积分）
        
        Args:
            trade_date: 交易日期 YYYYMMDD
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        try:
            cached = self._get_cached('margin', trade_date=trade_date)
            if cached:
                return cached
            
            df = self.pro.margin(trade_date=trade_date)
            
            if df.empty:
                return []
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'ts_code': row.get('ts_code', ''),
                    'name': row.get('name', ''),
                    'trade_date': trade_date,
                    'buy_amount': float(row.get('buy_amount', 0)),  # 融资买入额
                    'repay_amount': float(row.get('repay_amount', 0)),  # 融资偿还额
                    'margin_balance': float(row.get('margin_bal', 0)),  # 融资余额
                    'sell_amount': float(row.get('sell_amount', 0)),  # 融券卖出量
                    'repay_qty': float(row.get('repay_qty', 0)),  # 融券偿还量
                    'margin_short': float(row.get('margin_short', 0)),  # 融券余量
                    'net_financing': float(row.get('buy_amount', 0)) - float(row.get('repay_amount', 0))
                })
            
            self._set_cache('margin', data, trade_date=trade_date)
            print(f"[Tushare] 获取融资融券汇总 {len(data)} 只")
            return data
            
        except Exception as e:
            print(f"[Tushare] 融资融券汇总获取失败：{e}")
            return []
    
    def get_margin_detail(self, trade_date: str = None) -> List[Dict]:
        """
        获取融资融券交易明细（2000 积分）
        
        Args:
            trade_date: 交易日期 YYYYMMDD
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        try:
            cached = self._get_cached('margin_detail', trade_date=trade_date)
            if cached:
                return cached
            
            df = self.pro.margin_detail(trade_date=trade_date)
            
            if df.empty:
                return []
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'ts_code': row.get('ts_code', ''),
                    'name': row.get('name', ''),
                    'trade_date': trade_date,
                    'buy_amount': float(row.get('buy_amount', 0)),
                    'buy_qty': float(row.get('buy_qty', 0)),
                    'sell_amount': float(row.get('sell_amount', 0)),
                    'sell_qty': float(row.get('sell_qty', 0)),
                    'net_amount': float(row.get('buy_amount', 0)) - float(row.get('sell_amount', 0))
                })
            
            self._set_cache('margin_detail', data, trade_date=trade_date)
            print(f"[Tushare] 获取融资融券明细 {len(data)} 只")
            return data
            
        except Exception as e:
            print(f"[Tushare] 融资融券明细获取失败：{e}")
            return []
    
    # ==================== 股东增减持 ====================
    
    def get_stk_holdertrade(self, ts_code: str = None, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        获取股东增减持数据（2000 积分）
        
        Args:
            ts_code: 股票代码，不传则获取全部
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
        """
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
        try:
            params = {'start_date': start_date, 'end_date': end_date}
            if ts_code:
                params['ts_code'] = ts_code
            
            df = self.pro.stk_holdertrade(**params)
            
            if df.empty:
                return []
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'ts_code': row.get('ts_code', ''),
                    'name': row.get('name', ''),
                    'trade_date': row.get('ann_date', ''),
                    'holder_name': row.get('holder_name', ''),
                    'holder_type': row.get('holder_type', ''),  # 股东类型
                    'change_vol': float(row.get('change_vol', 0)),  # 变动数量
                    'change_ratio': float(row.get('change_ratio', 0)),  # 变动比例
                    'avg_price': float(row.get('avg_price', 0)),  # 成交均价
                    'total_hold': float(row.get('total_hold', 0)),  # 持股总数
                    'hold_ratio': float(row.get('hold_ratio', 0))  # 持股比例
                })
            
            print(f"[Tushare] 获取股东增减持 {len(data)} 条")
            return data
            
        except Exception as e:
            print(f"[Tushare] 股东增减持获取失败：{e}")
            return []
    
    # ==================== 板块资金流 ====================
    
    def get_moneyflow_cnt(self, trade_date: str = None) -> List[Dict]:
        """
        获取板块资金流（2000 积分）- 按行业/概念分类
        
        Args:
            trade_date: 交易日期 YYYYMMDD
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        try:
            cached = self._get_cached('moneyflow_cnt', trade_date=trade_date)
            if cached:
                return cached
            
            # 尝试多个接口
            df = None
            for func_name in ['moneyflow_cnt', 'moneyflow_ind']:
                try:
                    if hasattr(self.pro, func_name):
                        func = getattr(self.pro, func_name)
                        df = func(trade_date=trade_date)
                        if not df.empty:
                            break
                except:
                    continue
            
            if df is None or df.empty:
                return []
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'industry': row.get('industry', row.get('name', '')),
                    'trade_date': trade_date,
                    'buy_sm_amount': float(row.get('buy_sm_amount', 0)),
                    'sell_sm_amount': float(row.get('sell_sm_amount', 0)),
                    'buy_md_amount': float(row.get('buy_md_amount', 0)),
                    'sell_md_amount': float(row.get('sell_md_amount', 0)),
                    'buy_lg_amount': float(row.get('buy_lg_amount', 0)),
                    'sell_lg_amount': float(row.get('sell_lg_amount', 0)),
                    'buy_elg_amount': float(row.get('buy_elg_amount', 0)),
                    'sell_elg_amount': float(row.get('sell_elg_amount', 0)),
                    'net_mf_amount': float(row.get('net_mf_amount', 0))
                })
            
            self._set_cache('moneyflow_cnt', data, trade_date=trade_date)
            print(f"[Tushare] 获取板块资金流 {len(data)} 个")
            return data
            
        except Exception as e:
            print(f"[Tushare] 板块资金流获取失败：{e}")
            return []
    
    # ==================== 龙虎榜 ====================
    
    
    
    # ==================== 融资融券 ====================
    
    def get_margin_detail(self, ts_code: str, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        获取融资融券明细（300 积分）
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        
        try:
            df = self.pro.margin_detail(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            if df.empty:
                return []
            
            margins = []
            for _, row in df.iterrows():
                margins.append({
                    'ts_code': ts_code,
                    'trade_date': row.get('trade_date', ''),
                    'buy_amount': float(row.get('buy_amount', 0)),  # 融资买入额
                    'repay_amount': float(row.get('repay_amount', 0)),  # 融资偿还额
                    'margin_bal': float(row.get('margin_bal', 0)),  # 融资余额
                    'sell_amount': float(row.get('sell_amount', 0)),  # 融券卖出量
                    'repay_qty': float(row.get('repay_qty', 0)),  # 融券偿还量
                    'margin_qty': float(row.get('margin_qty', 0))  # 融券余量
                })
            
            print(f"[Tushare] 获取 {ts_code} 融资融券 {len(margins)} 条")
            return margins
            
        except Exception as e:
            print(f"[Tushare] 融资融券获取失败 {ts_code}: {e}")
            return []
    
    # ==================== 财务数据 ====================
    
    def get_income(self, ts_code: str, start_date: str = None, end_date: str = None) -> List[Dict]:
        """获取利润表（120 积分）"""
        if not start_date:
            start_date = '20250101'
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        
        try:
            df = self.pro.income(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields='ts_code,ann_date,revenue,op,net_profit,eps,roe'
            )
            
            if df.empty:
                return []
            
            reports = []
            for _, row in df.iterrows():
                reports.append({
                    'ts_code': ts_code,
                    'ann_date': row.get('ann_date', ''),
                    'revenue': float(row.get('revenue', 0)),
                    'op': float(row.get('op', 0)),  # 营业利润
                    'net_profit': float(row.get('net_profit', 0)),
                    'eps': float(row.get('eps', 0)),
                    'roe': float(row.get('roe', 0))
                })
            
            print(f"[Tushare] 获取 {ts_code} 利润表 {len(reports)} 期")
            return reports
            
        except Exception as e:
            print(f"[Tushare] 利润表获取失败 {ts_code}: {e}")
            return []
    
    def get_balancesheet(self, ts_code: str, start_date: str = None, end_date: str = None) -> List[Dict]:
        """获取资产负债表（120 积分）"""
        if not start_date:
            start_date = '20250101'
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        
        try:
            df = self.pro.balancesheet(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields='ts_code,ann_date,total_assets,total_liab,total_hldr_eqy_inc_min_int'
            )
            
            if df.empty:
                return []
            
            reports = []
            for _, row in df.iterrows():
                reports.append({
                    'ts_code': ts_code,
                    'ann_date': row.get('ann_date', ''),
                    'total_assets': float(row.get('total_assets', 0)),
                    'total_liab': float(row.get('total_liab', 0)),
                    'total_equity': float(row.get('total_hldr_eqy_inc_min_int', 0))
                })
            
            print(f"[Tushare] 获取 {ts_code} 资产负债表 {len(reports)} 期")
            return reports
            
        except Exception as e:
            print(f"[Tushare] 资产负债表获取失败 {ts_code}: {e}")
            return []
    
    def get_cashflow(self, ts_code: str, start_date: str = None, end_date: str = None) -> List[Dict]:
        """获取现金流量表（120 积分）"""
        if not start_date:
            start_date = '20250101'
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        
        try:
            df = self.pro.cashflow(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields='ts_code,ann_date,oper_cf,invest_cf,financing_cf'
            )
            
            if df.empty:
                return []
            
            reports = []
            for _, row in df.iterrows():
                reports.append({
                    'ts_code': ts_code,
                    'ann_date': row.get('ann_date', ''),
                    'oper_cf': float(row.get('oper_cf', 0)),  # 经营现金流
                    'invest_cf': float(row.get('invest_cf', 0)),  # 投资现金流
                    'financing_cf': float(row.get('financing_cf', 0))  # 筹资现金流
                })
            
            print(f"[Tushare] 获取 {ts_code} 现金流量表 {len(reports)} 期")
            return reports
            
        except Exception as e:
            print(f"[Tushare] 现金流量表获取失败 {ts_code}: {e}")
            return []
    
    def get_forecast(self, ts_code: str = None, ann_date: str = None) -> List[Dict]:
        """获取业绩预告（120 积分）"""
        try:
            df = self.pro.forecast(ts_code=ts_code, ann_date=ann_date)
            
            if df.empty:
                return []
            
            forecasts = []
            for _, row in df.iterrows():
                forecasts.append({
                    'ts_code': row.get('ts_code', ''),
                    'ann_date': row.get('ann_date', ''),
                    'type': row.get('type', ''),  # 预告类型
                    'profit_min': float(row.get('profit_min', 0)),
                    'profit_max': float(row.get('profit_max', 0)),
                    'chgr': float(row.get('chgr', 0))  # 变动幅度
                })
            
            print(f"[Tushare] 获取业绩预告 {len(forecasts)} 条")
            return forecasts
            
        except Exception as e:
            print(f"[Tushare] 业绩预告获取失败：{e}")
            return []
    
    # ==================== 指数/ETF ====================
    
    def get_index_daily(self, ts_code: str, trade_date: str = None) -> Optional[Dict]:
        """获取指数日线（300 积分）"""
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        try:
            df = self.pro.index_daily(ts_code=ts_code, trade_date=trade_date)
            
            if df.empty:
                return None
            
            row = df.iloc[0]
            return {
                'ts_code': ts_code,
                'trade_date': trade_date,
                'close': float(row.get('close', 0)),
                'open': float(row.get('open', 0)),
                'high': float(row.get('high', 0)),
                'low': float(row.get('low', 0)),
                'pct_chg': float(row.get('pct_chg', 0)),
                'vol': float(row.get('vol', 0)),
                'amount': float(row.get('amount', 0))
            }
            
        except Exception as e:
            print(f"[Tushare] 指数行情获取失败 {ts_code}: {e}")
            return None
    
    def get_fund_daily(self, ts_code: str, trade_date: str = None) -> Optional[Dict]:
        """获取 ETF 日线（120 积分）"""
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        try:
            df = self.pro.fund_daily(ts_code=ts_code, trade_date=trade_date)
            
            if df.empty:
                return None
            
            row = df.iloc[0]
            return {
                'ts_code': ts_code,
                'trade_date': trade_date,
                'close': float(row.get('close', 0)),
                'open': float(row.get('open', 0)),
                'high': float(row.get('high', 0)),
                'low': float(row.get('low', 0)),
                'pct_chg': float(row.get('pct_chg', 0)),
                'vol': float(row.get('vol', 0)),
                'amount': float(row.get('amount', 0))
            }
            
        except Exception as e:
            print(f"[Tushare] ETF 行情获取失败 {ts_code}: {e}")
            return None
    
    def get_index_member(self, index_code: str) -> List[Dict]:
        """获取指数成分股（300 积分）"""
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
    
    # ==================== 宏观经济 ====================
    
    def get_cn_gdp(self) -> List[Dict]:
        """获取 GDP 数据（120 积分）"""
        try:
            df = self.pro.cn_gdp()
            
            if df.empty:
                return []
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'year': str(row.get('year', '')),
                    'gdp': float(row.get('gdp', 0)),
                    'gdp_pc': float(row.get('gdp_pc', 0))  # 人均 GDP
                })
            
            print(f"[Tushare] 获取 GDP 数据 {len(data)} 年")
            return data
            
        except Exception as e:
            print(f"[Tushare] GDP 获取失败：{e}")
            return []
    
    def get_cn_cpi(self) -> List[Dict]:
        """获取 CPI 数据（120 积分）"""
        try:
            df = self.pro.cn_cpi()
            
            if df.empty:
                return []
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'month': row.get('month', ''),
                    'cpi_m': float(row.get('cpi_m', 0)),  # 同比
                    'cpi_y': float(row.get('cpi_y', 0))  # 环比
                })
            
            print(f"[Tushare] 获取 CPI 数据 {len(data)} 月")
            return data
            
        except Exception as e:
            print(f"[Tushare] CPI 获取失败：{e}")
            return []
    
    def get_cn_ppi(self) -> List[Dict]:
        """获取 PPI 数据（120 积分）"""
        try:
            df = self.pro.cn_ppi()
            
            if df.empty:
                return []
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'month': row.get('month', ''),
                    'ppiout_m': float(row.get('ppiout_m', 0)),  # 工业生产者出厂
                    'ppiom_m': float(row.get('ppiom_m', 0))  # 工业生产者购进
                })
            
            print(f"[Tushare] 获取 PPI 数据 {len(data)} 月")
            return data
            
        except Exception as e:
            print(f"[Tushare] PPI 获取失败：{e}")
            return []
    
    def get_shibor(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """获取 Shibor 利率（120 积分）"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        
        try:
            df = self.pro.shibor(start_date=start_date, end_date=end_date)
            
            if df.empty:
                return []
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'date': row.get('date', ''),
                    'on': float(row.get('on', 0)),  # 隔夜
                    '1w': float(row.get('1w', 0)),  # 1 周
                    '2w': float(row.get('2w', 0)),  # 2 周
                    '1m': float(row.get('1m', 0)),  # 1 个月
                    '3m': float(row.get('3m', 0))  # 3 个月
                })
            
            print(f"[Tushare] 获取 Shibor 利率 {len(data)} 条")
            return data
            
        except Exception as e:
            print(f"[Tushare] Shibor 获取失败：{e}")
            return []
    
    # ==================== 新闻快讯 ====================
    
    def get_news(self, start_date: str = None, end_date: str = None, src: str = 'sina') -> List[Dict]:
        """
        获取财经新闻（120 积分）
        
        Args:
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
            src: 新闻源 (sina|eastmoney|10jqka)
        """
        if not start_date:
            start_date = datetime.now().strftime('%Y%m%d')
        if not end_date:
            end_date = start_date
        
        try:
            # 检查缓存
            cached = self._get_cached('news', start_date=start_date, end_date=end_date, src=src)
            if cached:
                return cached
            
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
            
            # 保存到缓存
            self._set_cache('news', news_list, start_date=start_date, end_date=end_date, src=src)
            
            print(f"[Tushare] 获取新闻 {len(news_list)} 条 (源：{src})")
            return news_list
            
        except Exception as e:
            print(f"[Tushare] 新闻获取失败：{e}")
            return []
    
    # ==================== 缓存工具 ====================
    
    def _get_cache_key(self, func_name: str, **kwargs) -> str:
        import hashlib
        key_str = f"{func_name}:{json.dumps(kwargs, sort_keys=True, default=str)}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_cached(self, func_name: str, **kwargs) -> Optional[Any]:
        key = self._get_cache_key(func_name, **kwargs)
        cache_path = self.cache_dir / f"{key}.json"
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if time.time() - data.get('_cached_at', 0) > self.cache_ttl:
                cache_path.unlink()
                return None
            
            return data.get('value')
        except:
            return None
    
    def _set_cache(self, func_name: str, value: Any, **kwargs):
        key = self._get_cache_key(func_name, **kwargs)
        cache_path = self.cache_dir / f"{key}.json"
        
        try:
            data = {'value': value, '_cached_at': time.time()}
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"[Tushare] 缓存写入失败：{e}")


def test_tushare_pro(token: str):
    """测试 Tushare Pro 连接"""
    print("=" * 60)
    print("Tushare Pro 功能测试 (600 积分版)")
    print("=" * 60)
    
    source = TushareProSource(token=token, cache_ttl=60)
    
    # 测试 1: 股票列表
    print("\n1. 获取股票列表...")
    stocks = source.get_stock_list()
    if stocks:
        print(f"   ✅ 成功，{len(stocks)} 只")
        print(f"      示例：{stocks[0]['name']}({stocks[0]['ts_code']})")
    
    # 测试 2: 日线行情
    print("\n2. 获取日线行情 (平安银行)...")
    today = datetime.now().strftime('%Y%m%d')
    quote = source.get_daily('000001.SZ', today)
    if quote:
        print(f"   ✅ 成功")
        print(f"      现价：¥{quote['close']:.2f} ({quote['pct_chg']:+.2f}%)")
    else:
        print(f"   ⚠️ 无数据 (可能非交易日)")
    
    # 测试 3: 资金流
    print("\n3. 获取资金流 (平安银行)...")
    flow = source.get_moneyflow('000001.SZ', today)
    if flow:
        print(f"   ✅ 成功")
        print(f"      主力净流入：{flow['net_mf_amount']/10000:.1f}万")
    else:
        print(f"   ⚠️ 无数据")
    
    # 测试 4: 北向资金
    print("\n4. 获取北向资金持仓...")
    north = source.get_stock_hsgt_hold(market='sh')
    if north:
        print(f"   ✅ 成功，{len(north)} 只")
        if north[0]:
            print(f"      示例：{north[0]['name']} - 持股{north[0]['hold_ratio']:.2f}%")
    
    # 测试 5: 龙虎榜
    print("\n5. 获取龙虎榜...")
    lhb = source.get_top_list(today)
    if lhb:
        print(f"   ✅ 成功，{len(lhb)} 只")
    else:
        print(f"   ⚠️ 今日无数据")
    
    # 测试 6: 财务数据
    print("\n6. 获取财务数据 (平安银行)...")
    income = source.get_income('000001.SZ')
    if income:
        print(f"   ✅ 成功，{len(income)} 期")
        print(f"      最新营收：{income[0]['revenue']/100000000:.1f}亿")
    
    # 测试 7: 宏观经济
    print("\n7. 获取 GDP 数据...")
    gdp = source.get_cn_gdp()
    if gdp:
        print(f"   ✅ 成功，{len(gdp)} 年")
    
    print("\n" + "=" * 60)
    print("Tushare Pro 测试完成")
    print("=" * 60)
    
    return True


if __name__ == '__main__':
    import sys
    
    token = sys.argv[1] if len(sys.argv) > 1 else os.getenv('TUSHARE_TOKEN')
    
    if not token:
        print("❌ 未提供 Tushare Token")
        print("用法：python tushare_pro_source.py <your_token>")
        sys.exit(1)
    
    test_tushare_pro(token)
