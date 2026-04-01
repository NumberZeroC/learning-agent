#!/usr/bin/env python3
"""
增强数据源模块 - 扩展 AKShare 支持 220+ 接口
参考：tushare-finance Skill (ClawHub)

功能：
1. ETF 行情与资金流
2. 北向资金监控
3. 龙虎榜数据
4. 融资融券
5. 宏观经济指标
6. 行业/概念板块

⚠️ 要求：AKShare 1.12.0+
"""
import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any

try:
    import akshare as ak
    import pandas as pd
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    print("[增强数据源] ⚠️ AKShare 未安装，请运行：pip install akshare")


class EnhancedDataSource:
    """增强数据源 - 扩展 AKShare 功能"""
    
    def __init__(self, cache_dir: str = None, cache_ttl: int = 300):
        if not AKSHARE_AVAILABLE:
            raise ImportError("AKShare 未安装")
        
        # 缓存配置
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(__file__).parent.parent / 'data' / 'cache' / 'enhanced'
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = cache_ttl
        
        print(f"[增强数据源] ✅ 已初始化 - 缓存目录：{self.cache_dir}")
    
    # ==================== ETF 数据 ====================
    
    def get_etf_list(self) -> List[Dict]:
        """获取 ETF 列表"""
        try:
            df = ak.fund_etf_spot_em()
            if df.empty:
                return []
            
            etfs = []
            for _, row in df.iterrows():
                etfs.append({
                    'code': row.get('代码', ''),
                    'name': row.get('名称', ''),
                    'price': float(row.get('最新价', 0)) if row.get('最新价') else 0,
                    'change_pct': float(row.get('涨跌幅', 0)) if row.get('涨跌幅') else 0,
                    'volume': float(row.get('成交量', 0)) if row.get('成交量') else 0,
                    'amount': float(row.get('成交额', 0)) if row.get('成交额') else 0,
                    'net_value': float(row.get('净值', 0)) if row.get('净值') else 0,
                    'premium_rate': float(row.get('溢价率', 0)) if row.get('溢价率') else 0
                })
            
            print(f"[ETF] 获取 ETF 列表 {len(etfs)} 只")
            return etfs
            
        except Exception as e:
            print(f"[ETF] 列表获取失败：{e}")
            return []
    
    def get_etf_flow(self, top_n: int = 10) -> List[Dict]:
        """获取 ETF 资金流向（按成交额排序）"""
        import time
        import random
        
        # 重试机制
        for attempt in range(3):
            try:
                if attempt > 0:
                    delay = random.uniform(1, 3)
                    print(f"[ETF] 重试 ({attempt + 1}/3) - {delay:.1f}秒后...")
                    time.sleep(delay)
                
                df = ak.fund_etf_spot_em()
                if df.empty:
                    return []
                
                # 按成交额排序
                df_sorted = df.nlargest(top_n, '成交额')
                
                flows = []
                for _, row in df_sorted.iterrows():
                    flows.append({
                        'code': row.get('代码', ''),
                        'name': row.get('名称', ''),
                        'amount': float(row.get('成交额', 0)) if row.get('成交额') else 0,
                        'change_pct': float(row.get('涨跌幅', 0)) if row.get('涨跌幅') else 0,
                        'volume': float(row.get('成交量', 0)) if row.get('成交量') else 0
                    })
                
                print(f"[ETF] 获取资金流 TOP{top_n}")
                return flows
                
            except Exception as e:
                print(f"[ETF] 尝试 {attempt + 1} 失败：{e}")
                if attempt >= 2:
                    print(f"[ETF] 所有重试失败，返回空列表")
                    return []
        
        return []
    
    # ==================== 北向资金 ====================
    
    def get_north_flow(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        获取北向资金流向
        
        Args:
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
        """
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            
            df = ak.stock_hsgt_north_net_flow_in_em(symbol="沪股通", start_date=start_date, end_date=end_date)
            
            if df.empty:
                return []
            
            flows = []
            for _, row in df.iterrows():
                flows.append({
                    'date': row.get('日期', ''),
                    'net_inflow': float(row.get('净流入', 0)) if row.get('净流入') else 0,
                    'buy': float(row.get('买入额', 0)) if row.get('买入额') else 0,
                    'sell': float(row.get('卖出额', 0)) if row.get('卖出额') else 0,
                    'balance': float(row.get('余额', 0)) if row.get('余额') else 0
                })
            
            print(f"[北向] 获取北向资金 {len(flows)} 条")
            return flows
            
        except Exception as e:
            print(f"[北向] 资金流获取失败：{e}")
            return []
    
    def get_north_top_stocks(self, top_n: int = 10) -> List[Dict]:
        """获取北向资金持仓 TOP 股"""
        try:
            # 尝试多个接口
            for market in ["沪股通", "深股通"]:
                try:
                    df = ak.stock_hsgt_hold_stock_em(market=market)
                    if not df.empty:
                        break
                except:
                    continue
            
            if df.empty:
                return []
            
            stocks = []
            for _, row in df.head(top_n).iterrows():
                # 兼容不同字段名
                hold_ratio = row.get('持股比例', row.get('占流通股比', row.get('持股占比', 0)))
                hold_amount = row.get('持股数量', row.get('持股数', 0))
                hold_value = row.get('持股市值', row.get('市值', 0))
                
                stocks.append({
                    'code': row.get('代码', row.get('symbol', '')),
                    'name': row.get('名称', row.get('name', '')),
                    'price': float(row.get('最新价', row.get('price', 0))) if row.get('最新价', row.get('price')) else 0,
                    'change_pct': float(row.get('涨跌幅', row.get('change_pct', 0))) if row.get('涨跌幅', row.get('change_pct')) else 0,
                    'hold_ratio': float(hold_ratio) if hold_ratio else 0,
                    'hold_amount': float(hold_amount) if hold_amount else 0,
                    'hold_value': float(hold_value) if hold_value else 0,
                    'market': market
                })
            
            print(f"[北向] 获取持仓 TOP{top_n} (市场：{market})")
            return stocks
            
        except Exception as e:
            print(f"[北向] 持仓获取失败：{e}")
            return []
    
    # ==================== 龙虎榜 ====================
    
    def get_stock_lhb(self, trade_date: str = None) -> List[Dict]:
        """
        获取龙虎榜数据
        
        Args:
            trade_date: 交易日期 YYYYMMDD
        """
        try:
            if not trade_date:
                trade_date = datetime.now().strftime('%Y%m%d')
            
            df = ak.stock_lhb_detail_em(start_date=trade_date, end_date=trade_date)
            
            if df.empty:
                return []
            
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'code': row.get('代码', ''),
                    'name': row.get('名称', ''),
                    'close': float(row.get('收盘价', 0)) if row.get('收盘价') else 0,
                    'change_pct': float(row.get('涨跌幅', 0)) if row.get('涨跌幅') else 0,
                    'turnover_rate': float(row.get('换手率', 0)) if row.get('换手率') else 0,
                    'net_inflow': float(row.get('净流入', 0)) if row.get('净流入') else 0,
                    'buy_amount': float(row.get('买入金额', 0)) if row.get('买入金额') else 0,
                    'sell_amount': float(row.get('卖出金额', 0)) if row.get('卖出金额') else 0,
                    'reason': row.get('上榜原因', '')
                })
            
            print(f"[龙虎榜] 获取 {len(stocks)} 只")
            return stocks
            
        except Exception as e:
            print(f"[龙虎榜] 获取失败：{e}")
            return []
    
    # ==================== 融资融券 ====================
    
    def get_margin_data(self, market: str = 'sh', start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        获取融资融券数据
        
        Args:
            market: 市场 (sh=上交所，sz=深交所)
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
        """
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            
            if market == 'sh':
                df = ak.stock_margin_sse(start_date=start_date, end_date=end_date)
            else:
                df = ak.stock_margin_szse(start_date=start_date, end_date=end_date)
            
            if df.empty:
                return []
            
            margins = []
            for _, row in df.iterrows():
                margins.append({
                    'date': row.get('日期', ''),
                    'margin_balance': float(row.get('融资余额', 0)) if row.get('融资余额') else 0,
                    'margin_buy': float(row.get('融资买入额', 0)) if row.get('融资买入额') else 0,
                    'margin_repay': float(row.get('融资偿还额', 0)) if row.get('融资偿还额') else 0,
                    'short_balance': float(row.get('融券余额', 0)) if row.get('融券余额') else 0,
                    'short_sell': float(row.get('融券卖出量', 0)) if row.get('融券卖出量') else 0
                })
            
            print(f"[融资融券] 获取 {market}市场 {len(margins)} 条")
            return margins
            
        except Exception as e:
            print(f"[融资融券] 获取失败：{e}")
            return []
    
    # ==================== 宏观经济 ====================
    
    def get_gdp(self) -> List[Dict]:
        """获取 GDP 数据"""
        try:
            df = ak.macro_china_gdp_yearly()
            if df.empty:
                return []
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'year': row.get('年份', ''),
                    'gdp': float(row.get('国内生产总值', 0)) if row.get('国内生产总值') else 0,
                    'growth_rate': float(row.get('增长率', 0)) if row.get('增长率') else 0
                })
            
            print(f"[宏观] 获取 GDP 数据 {len(data)} 年")
            return data
            
        except Exception as e:
            print(f"[宏观] GDP 获取失败：{e}")
            return []
    
    def get_cpi_ppi(self) -> Dict:
        """获取 CPI/PPI 数据"""
        try:
            cpi_df = ak.macro_china_cpi_yearly()
            ppi_df = ak.macro_china_ppi_yearly()
            
            result = {
                'cpi': [],
                'ppi': []
            }
            
            for _, row in cpi_df.iterrows():
                result['cpi'].append({
                    'year': row.get('年份', ''),
                    'value': float(row.get('值', 0)) if row.get('值') else 0
                })
            
            for _, row in ppi_df.iterrows():
                result['ppi'].append({
                    'year': row.get('年份', ''),
                    'value': float(row.get('值', 0)) if row.get('值') else 0
                })
            
            print(f"[宏观] 获取 CPI/PPI 数据")
            return result
            
        except Exception as e:
            print(f"[宏观] CPI/PPI 获取失败：{e}")
            return {'cpi': [], 'ppi': []}
    
    def get_pmi(self) -> List[Dict]:
        """获取 PMI 数据"""
        try:
            df = ak.macro_china_pmi_yearly()
            if df.empty:
                return []
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'date': row.get('日期', ''),
                    'pmi': float(row.get('值', 0)) if row.get('值') else 0
                })
            
            print(f"[宏观] 获取 PMI 数据 {len(data)} 条")
            return data
            
        except Exception as e:
            print(f"[宏观] PMI 获取失败：{e}")
            return []
    
    # ==================== 行业/概念板块 ====================
    
    def get_industry_list(self) -> List[Dict]:
        """获取行业板块列表"""
        try:
            df = ak.stock_board_industry_name_em()
            if df.empty:
                return []
            
            industries = []
            for _, row in df.iterrows():
                industries.append({
                    'code': row.get('板块代码', ''),
                    'name': row.get('板块名称', ''),
                    'change_pct': float(row.get('涨跌幅', 0)) if row.get('涨跌幅') else 0
                })
            
            print(f"[行业] 获取行业板块 {len(industries)} 个")
            return industries
            
        except Exception as e:
            print(f"[行业] 板块列表获取失败：{e}")
            return []
    
    def get_concept_list(self) -> List[Dict]:
        """获取概念板块列表"""
        try:
            df = ak.stock_board_concept_name_em()
            if df.empty:
                return []
            
            concepts = []
            for _, row in df.iterrows():
                concepts.append({
                    'code': row.get('板块代码', ''),
                    'name': row.get('板块名称', ''),
                    'change_pct': float(row.get('涨跌幅', 0)) if row.get('涨跌幅') else 0
                })
            
            print(f"[概念] 获取概念板块 {len(concepts)} 个")
            return concepts
            
        except Exception as e:
            print(f"[概念] 板块列表获取失败：{e}")
            return []
    
    def get_industry_stocks(self, industry_name: str) -> List[Dict]:
        """获取行业成分股"""
        try:
            df = ak.stock_board_industry_cons_em(symbol=industry_name)
            if df.empty:
                return []
            
            stocks = []
            for _, row in df.iterrows():
                code = row.get('代码', '')
                ts_code = f"{code}.SZ" if code.startswith(('0', '3')) else f"{code}.SH"
                
                stocks.append({
                    'ts_code': ts_code,
                    'code': code,
                    'name': row.get('名称', ''),
                    'price': float(row.get('最新价', 0)) if row.get('最新价') else 0,
                    'change_pct': float(row.get('涨跌幅', 0)) if row.get('涨跌幅') else 0,
                    'volume': float(row.get('成交量', 0)) if row.get('成交量') else 0,
                    'turnover': float(row.get('成交额', 0)) if row.get('成交额') else 0
                })
            
            print(f"[行业] 获取 {industry_name} 成分股 {len(stocks)} 只")
            return stocks
            
        except Exception as e:
            print(f"[行业] 成分股获取失败：{e}")
            return []
    
    # ==================== 财务数据 ====================
    
    def get_financial_abstract(self, stock_code: str) -> Dict:
        """
        获取公司财务摘要
        
        Args:
            stock_code: 股票代码 (如 600519)
        """
        try:
            df = ak.stock_financial_abstract(symbol=stock_code)
            if df.empty:
                return {}
            
            # 取最新一期
            row = df.iloc[0]
            
            return {
                'code': stock_code,
                'report_date': row.get('报告期', ''),
                'revenue': float(row.get('营业总收入', 0)) if row.get('营业总收入') else 0,
                'net_profit': float(row.get('净利润', 0)) if row.get('净利润') else 0,
                'eps': float(row.get('每股收益', 0)) if row.get('每股收益') else 0,
                'roe': float(row.get('净资产收益率', 0)) if row.get('净资产收益率') else 0,
                'gross_margin': float(row.get('毛利率', 0)) if row.get('毛利率') else 0,
                'debt_ratio': float(row.get('资产负债率', 0)) if row.get('资产负债率') else 0
            }
            
        except Exception as e:
            print(f"[财务] {stock_code} 获取失败：{e}")
            return {}
    
    def get_forecast(self, stock_code: str) -> List[Dict]:
        """
        获取业绩预告
        
        Args:
            stock_code: 股票代码
        """
        try:
            df = ak.stock_info_a_profit_forecast(symbol=stock_code)
            if df.empty:
                return []
            
            forecasts = []
            for _, row in df.iterrows():
                forecasts.append({
                    'report_date': row.get('报告期', ''),
                    'forecast_type': row.get('预告类型', ''),
                    'profit_min': float(row.get('净利润下限', 0)) if row.get('净利润下限') else 0,
                    'profit_max': float(row.get('净利润上限', 0)) if row.get('净利润上限') else 0,
                    'change_pct': float(row.get('净利润变动幅度', 0)) if row.get('净利润变动幅度') else 0
                })
            
            print(f"[业绩] 获取 {stock_code} 业绩预告 {len(forecasts)} 条")
            return forecasts
            
        except Exception as e:
            print(f"[业绩] {stock_code} 预告获取失败：{e}")
            return []
    
    # ==================== 缓存工具 ====================
    
    def _get_cache_key(self, func_name: str, **kwargs) -> str:
        import hashlib
        key_str = f"{func_name}:{json.dumps(kwargs, sort_keys=True, default=str)}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_cached(self, key: str) -> Optional[Any]:
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
    
    def _set_cache(self, key: str, value: Any):
        cache_path = self.cache_dir / f"{key}.json"
        try:
            data = {'value': value, '_cached_at': time.time()}
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"[缓存] 写入失败：{e}")
    
    def cached(self, func_name: str, **kwargs):
        """缓存装饰器"""
        def decorator(func):
            def wrapper(*args, **kwargs_inner):
                key = self._get_cache_key(func_name, **kwargs_inner)
                cached = self._get_cached(key)
                if cached:
                    return cached
                
                result = func(*args, **kwargs_inner)
                if result:
                    self._set_cache(key, result)
                return result
            return wrapper
        return decorator


def test_enhanced_data_source():
    """测试增强数据源"""
    if not AKSHARE_AVAILABLE:
        print("❌ AKShare 未安装")
        return
    
    print("=" * 60)
    print("测试增强数据源")
    print("=" * 60)
    
    source = EnhancedDataSource(cache_ttl=60)
    
    # 测试 1: ETF 列表
    print("\n1. 获取 ETF 列表...")
    etfs = source.get_etf_list()
    if etfs:
        print(f"   ✅ 成功，获取 {len(etfs)} 只")
        print(f"      示例：{etfs[0]['name']}({etfs[0]['code']}) - ¥{etfs[0]['price']:.2f}")
    
    # 测试 2: ETF 资金流
    print("\n2. 获取 ETF 资金流 TOP10...")
    flows = source.get_etf_flow(top_n=10)
    if flows:
        print(f"   ✅ 成功")
        for i, f in enumerate(flows[:3], 1):
            print(f"      {i}. {f['name']}: {f['amount']/10000:.1f}亿")
    
    # 测试 3: 北向资金
    print("\n3. 获取北向资金持仓 TOP10...")
    north = source.get_north_top_stocks(top_n=10)
    if north:
        print(f"   ✅ 成功")
        for i, n in enumerate(north[:3], 1):
            print(f"      {i}. {n['name']}: 持股{n['hold_ratio']:.2f}%")
    
    # 测试 4: 龙虎榜
    print("\n4. 获取今日龙虎榜...")
    lhb = source.get_stock_lhb()
    if lhb:
        print(f"   ✅ 成功，{len(lhb)} 只")
    
    # 测试 5: 行业板块
    print("\n5. 获取行业板块...")
    industries = source.get_industry_list()
    if industries:
        print(f"   ✅ 成功，{len(industries)} 个")
    
    # 测试 6: 宏观数据
    print("\n6. 获取 GDP 数据...")
    gdp = source.get_gdp()
    if gdp:
        print(f"   ✅ 成功，{len(gdp)} 年")
    
    print("\n" + "=" * 60)
    print("增强数据源测试完成")
    print("=" * 60)


if __name__ == '__main__':
    test_enhanced_data_source()
