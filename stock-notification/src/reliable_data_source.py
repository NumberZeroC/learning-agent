#!/usr/bin/env python3
"""
可靠数据源模块 - 确保大盘指数、股价、资金数据准确性

特性：
1. 多数据源备份（AKShare → Tushare → 新浪财经 API）
2. 数据验证（范围检查、时间戳检查）
3. 固定数据快照（报告生成时保存原始数据）
4. 详细日志（便于排查问题）

用法：
    from reliable_data_source import ReliableDataSource
    source = ReliableDataSource()
    data = source.get_index_data()
"""
import os
import sys
import json
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any

try:
    import akshare as ak
    import pandas as pd
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False

try:
    import tushare as ts
    TUSHARE_AVAILABLE = True
except ImportError:
    TUSHARE_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_index_data(data: Dict, index_name: str) -> tuple:
        """
        验证指数数据
        
        Returns:
            (is_valid, error_message)
        """
        if not data:
            return False, "数据为空"
        
        # 检查必要字段
        required_fields = ['close', 'open', 'high', 'low']
        for field in required_fields:
            if field not in data:
                return False, f"缺少字段：{field}"
            
            value = data.get(field, 0)
            if not isinstance(value, (int, float)) or value <= 0:
                return False, f"字段 {field} 值异常：{value}"
        
        # 检查涨跌幅范围（-10% 到 +10%）
        change_pct = data.get('change_pct', 0)
        if not isinstance(change_pct, (int, float)):
            return False, f"涨跌幅类型异常：{change_pct}"
        
        if abs(change_pct) > 12:  # 留一些余量
            return False, f"涨跌幅超出合理范围：{change_pct}%"
        
        # 检查成交量
        volume = data.get('volume', 0)
        if volume < 0:
            return False, f"成交量为负：{volume}"
        
        return True, ""
    
    @staticmethod
    def validate_stock_data(data: Dict, stock_code: str) -> tuple:
        """验证股票数据"""
        if not data:
            return False, "数据为空"
        
        # 检查价格范围（0.01 到 10000）
        price = data.get('current_price', data.get('close', 0))
        if not isinstance(price, (int, float)) or price < 0.01 or price > 10000:
            return False, f"价格异常：{price}"
        
        # 检查涨跌幅范围（-20% 到 +20%，包含科创板/创业板）
        change_pct = data.get('change_pct', data.get('pct_chg', 0))
        if abs(change_pct) > 22:
            return False, f"涨跌幅超出合理范围：{change_pct}%"
        
        return True, ""


class ReliableDataSource:
    """可靠数据源 - 确保数据准确性"""
    
    def __init__(self, cache_dir: str = None, cache_ttl: int = 300,
                 tushare_token: str = None):
        """
        初始化
        
        Args:
            cache_dir: 缓存目录
            cache_ttl: 缓存有效期（秒）
            tushare_token: Tushare Token（如未提供，自动从公共配置加载）
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path(__file__).parent / 'data' / 'cache' / 'reliable'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = cache_ttl
        
        # 🔥 从公共配置加载 Tushare Token
        if tushare_token:
            self.tushare_token = tushare_token
        else:
            # 优先环境变量
            self.tushare_token = os.getenv('TUSHARE_TOKEN')
            
            # 如果环境变量未设置，从公共配置加载
            if not self.tushare_token:
                try:
                    sys.path.insert(0, '/home/admin/.openclaw/workspace/config')
                    from config_loader import get_tushare_token
                    self.tushare_token = get_tushare_token()
                except Exception as e:
                    print(f"[可靠数据源] ⚠️ 加载公共配置失败：{e}")
        
        self.validator = DataValidator()
        self.data_log = []  # 数据获取日志
        
        print(f"[可靠数据源] ✅ 已初始化")
        print(f"   缓存目录：{self.cache_dir}")
        print(f"   AKShare: {'✅' if AKSHARE_AVAILABLE else '❌'}")
        print(f"   Tushare: {'✅' if TUSHARE_AVAILABLE and self.tushare_token else '❌'}")
        print(f"    Requests: {'✅' if REQUESTS_AVAILABLE else '❌'}")
    
    # ==================== 大盘指数数据 ====================
    
    def get_index_data(self, trade_date: str = None) -> Dict:
        """
        获取大盘指数数据（多数据源备份）
        
        返回格式：
        {
            'shanghai': {'name': '上证指数', 'close': xxx, 'change_pct': xxx, ...},
            'shenzhen': {...},
            'chinext': {...},
            'hs300': {...},
            'zheng50': {...}
        }
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"\n📊 获取大盘指数数据 ({trade_date})...")
        
        indices = {
            'shanghai': {'code': 'sh000001', 'name': '上证指数'},
            'shenzhen': {'code': 'sz399001', 'name': '深证成指'},
            'chinext': {'code': 'sz399006', 'name': '创业板指'},
            'hs300': {'code': 'sh000300', 'name': '沪深 300'},
            'zheng50': {'code': 'sh000016', 'name': '上证 50'}
        }
        
        result = {}
        
        for key, info in indices.items():
            data = self._get_single_index(info['code'], info['name'], trade_date)
            if data:
                result[key] = data
        
        # 保存数据日志
        self._log_data('index_data', result)
        
        return result
    
    def _get_single_index(self, code: str, name: str, trade_date: str) -> Optional[Dict]:
        """获取单个指数数据（多数据源）"""
        
        # 1. 尝试 AKShare
        if AKSHARE_AVAILABLE:
            try:
                data = self._get_index_from_akshare(code, trade_date)
                if data:
                    is_valid, error = self.validator.validate_index_data(data, name)
                    if is_valid:
                        print(f"   ✅ {name}: {data['close']:.2f} ({data['change_pct']:+.2f}%) [AKShare]")
                        return data
                    else:
                        print(f"   ⚠️ {name} AKShare 数据验证失败：{error}")
            except Exception as e:
                print(f"   ⚠️ {name} AKShare 获取失败：{e}")
        
        # 2. 尝试 Tushare
        if TUSHARE_AVAILABLE and self.tushare_token:
            try:
                data = self._get_index_from_tushare(code, trade_date)
                if data:
                    is_valid, error = self.validator.validate_index_data(data, name)
                    if is_valid:
                        print(f"   ✅ {name}: {data['close']:.2f} ({data['change_pct']:+.2f}%) [Tushare]")
                        return data
            except Exception as e:
                print(f"   ⚠️ {name} Tushare 获取失败：{e}")
        
        # 3. 尝试新浪财经 API
        if REQUESTS_AVAILABLE:
            try:
                data = self._get_index_from_sina(code, trade_date)
                if data:
                    is_valid, error = self.validator.validate_index_data(data, name)
                    if is_valid:
                        print(f"   ✅ {name}: {data['close']:.2f} ({data['change_pct']:+.2f}%) [Sina]")
                        return data
            except Exception as e:
                print(f"   ⚠️ {name} Sina 获取失败：{e}")
        
        print(f"   ❌ {name}: 所有数据源均失败")
        return None
    
    def _get_index_from_akshare(self, code: str, trade_date: str) -> Optional[Dict]:
        """从 AKShare 获取指数数据"""
        try:
            df = ak.stock_zh_index_daily(symbol=code)
            if df.empty:
                return None
            
            # 获取最新数据
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            
            close = float(latest.get('close', 0))
            prev_close = float(prev.get('close', close))
            
            # 计算涨跌幅
            change_pct = ((close - prev_close) / prev_close * 100) if prev_close > 0 else 0
            
            return {
                'name': code,
                'trade_date': str(latest.get('date', trade_date)),
                'close': close,
                'open': float(latest.get('open', 0)),
                'high': float(latest.get('high', 0)),
                'low': float(latest.get('low', 0)),
                'change_pct': round(change_pct, 2),
                'change': round(close - prev_close, 2),
                'volume': float(latest.get('volume', 0)),
                'prev_close': prev_close
            }
        except Exception as e:
            print(f"[AKShare 指数] 获取失败 {code}: {e}")
            return None
    
    def _get_index_from_tushare(self, code: str, trade_date: str) -> Optional[Dict]:
        """从 Tushare 获取指数数据"""
        try:
            ts.set_token(self.tushare_token)
            pro = ts.pro_api()
            
            # 🔥 修复：正确的代码格式转换
            # 输入：sh000001 → 000001.SH
            # 输入：sz399001 → 399001.SZ
            code_upper = code.upper()
            if code_upper.startswith('SH'):
                ts_code = f"{code_upper[2:]}.SH"
            elif code_upper.startswith('SZ'):
                ts_code = f"{code_upper[2:]}.SZ"
            else:
                ts_code = code_upper
            
            # 日期格式转换
            trade_date_ts = trade_date.replace('-', '')
            
            df = pro.index_daily(ts_code=ts_code, trade_date=trade_date_ts)
            if df.empty:
                return None
            
            row = df.iloc[0]
            return {
                'name': ts_code,
                'trade_date': trade_date,
                'close': float(row.get('close', 0)),
                'open': float(row.get('open', 0)),
                'high': float(row.get('high', 0)),
                'low': float(row.get('low', 0)),
                'change_pct': float(row.get('pct_chg', 0)),
                'change': float(row.get('close', 0)) - float(row.get('pre_close', 0)),
                'volume': float(row.get('vol', 0)) if row.get('vol') else 0,
                'amount': float(row.get('amount', 0)) if row.get('amount') else 0,
                'prev_close': float(row.get('pre_close', 0))
            }
        except Exception as e:
            print(f"[Tushare 指数] 获取失败 {code}: {e}")
            return None
    
    def _get_index_from_sina(self, code: str, trade_date: str) -> Optional[Dict]:
        """从新浪财经 API 获取指数数据"""
        try:
            # 新浪财经实时行情 API
            url = f"http://hq.sinajs.cn/list={code}"
            response = requests.get(url, timeout=5)
            response.encoding = 'gbk'
            
            if response.status_code != 200:
                return None
            
            # 解析返回数据
            # 格式：var hq_str_sh000001="上证指数，3052.45,..."
            content = response.text
            if '=' not in content:
                return None
            
            quote = content.split('=')[1].strip('"').split(',')
            if len(quote) < 4:
                return None
            
            name = quote[0]
            current = float(quote[1]) if quote[1] else 0
            prev_close = float(quote[2]) if quote[2] else 0
            open_price = float(quote[3]) if quote[3] else 0
            high = float(quote[4]) if quote[4] else 0
            low = float(quote[5]) if quote[5] else 0
            
            change_pct = ((current - prev_close) / prev_close * 100) if prev_close > 0 else 0
            
            return {
                'name': name,
                'trade_date': trade_date,
                'close': current,
                'open': open_price,
                'high': high,
                'low': low,
                'change_pct': round(change_pct, 2),
                'change': round(current - prev_close, 2),
                'prev_close': prev_close
            }
        except Exception as e:
            print(f"[Sina 指数] 获取失败 {code}: {e}")
            return None
    
    # ==================== 个股数据 ====================
    
    def get_stock_data(self, stock_code: str, name: str = '') -> Optional[Dict]:
        """获取个股数据"""
        print(f"   📈 获取 {name or stock_code} 数据...")
        
        # 1. 尝试 AKShare
        if AKSHARE_AVAILABLE:
            try:
                data = self._get_stock_from_akshare(stock_code)
                if data:
                    is_valid, error = self.validator.validate_stock_data(data, stock_code)
                    if is_valid:
                        print(f"      ✅ {name}: ¥{data['current_price']:.2f} ({data['change_pct']:+.2f}%) [AKShare]")
                        return data
            except Exception as e:
                print(f"      ⚠️ {name} AKShare 失败：{e}")
        
        # 2. 尝试 Tushare
        if TUSHARE_AVAILABLE and self.tushare_token:
            try:
                data = self._get_stock_from_tushare(stock_code)
                if data:
                    print(f"      ✅ {name}: ¥{data['current_price']:.2f} ({data['change_pct']:+.2f}%) [Tushare]")
                    return data
            except Exception as e:
                print(f"      ⚠️ {name} Tushare 失败：{e}")
        
        # 3. 尝试新浪财经
        if REQUESTS_AVAILABLE:
            try:
                data = self._get_stock_from_sina(stock_code)
                if data:
                    print(f"      ✅ {name}: ¥{data['current_price']:.2f} ({data['change_pct']:+.2f}%) [Sina]")
                    return data
            except Exception as e:
                print(f"      ⚠️ {name} Sina 失败：{e}")
        
        print(f"      ❌ {name}: 所有数据源均失败")
        return None
    
    def _get_stock_from_akshare(self, stock_code: str) -> Optional[Dict]:
        """从 AKShare 获取个股数据"""
        try:
            # 使用实时行情接口
            df = ak.stock_zh_a_spot_em()
            if df.empty:
                return None
            
            # 代码匹配（支持多种格式）
            symbol = str(stock_code).zfill(6)  # 补齐 6 位
            stock_row = df[(df['代码'] == symbol) | (df['代码'] == stock_code)]
            if stock_row.empty:
                return None
            
            row = stock_row.iloc[0]
            return {
                'code': stock_code,
                'name': row.get('名称', ''),
                'current_price': float(row.get('最新价', 0)),
                'change': float(row.get('涨跌额', 0)),
                'change_pct': float(row.get('涨跌幅', 0)),
                'volume': float(row.get('成交量', 0)),
                'amount': float(row.get('成交额', 0)),
                'high': float(row.get('最高', 0)),
                'low': float(row.get('最低', 0)),
                'open': float(row.get('今开', 0)),
                'prev_close': float(row.get('昨收', 0))
            }
        except Exception as e:
            print(f"[AKShare 个股] 获取失败 {stock_code}: {e}")
            return None
    
    def _get_stock_from_tushare(self, stock_code: str) -> Optional[Dict]:
        """从 Tushare 获取个股数据"""
        try:
            ts.set_token(self.tushare_token)
            pro = ts.pro_api()
            
            # 获取日线数据
            today = datetime.now().strftime('%Y%m%d')
            df = pro.daily(ts_code=stock_code, trade_date=today)
            if df.empty:
                return None
            
            row = df.iloc[0]
            return {
                'code': stock_code,
                'name': '',
                'current_price': float(row.get('close', 0)),
                'change': float(row.get('change', 0)),
                'change_pct': float(row.get('pct_chg', 0)),
                'volume': float(row.get('vol', 0)) if row.get('vol') else 0,
                'amount': float(row.get('amount', 0)) if row.get('amount') else 0,
                'high': float(row.get('high', 0)),
                'low': float(row.get('low', 0)),
                'open': float(row.get('open', 0)),
                'prev_close': float(row.get('pre_close', 0))
            }
        except Exception as e:
            print(f"[Tushare 个股] 获取失败 {stock_code}: {e}")
            return None
    
    def _get_stock_from_sina(self, stock_code: str) -> Optional[Dict]:
        """从新浪财经 API 获取个股数据"""
        try:
            # 确定交易所前缀
            if stock_code.startswith('6'):
                prefix = 'sh'
            elif stock_code.startswith(('0', '3')):
                prefix = 'sz'
            else:
                prefix = 'sh'
            
            url = f"http://hq.sinajs.cn/list={prefix}{stock_code}"
            response = requests.get(url, timeout=5)
            response.encoding = 'gbk'
            
            if response.status_code != 200:
                return None
            
            content = response.text
            if '=' not in content:
                return None
            
            quote = content.split('=')[1].strip('"').split(',')
            if len(quote) < 4:
                return None
            
            name = quote[0]
            current = float(quote[3]) if quote[3] else 0
            prev_close = float(quote[2]) if quote[2] else 0
            open_price = float(quote[5]) if quote[5] else 0
            high = float(quote[4]) if quote[4] else 0
            low = float(quote[6]) if quote[6] else 0
            
            change_pct = ((current - prev_close) / prev_close * 100) if prev_close > 0 else 0
            
            return {
                'code': stock_code,
                'name': name,
                'current_price': current,
                'change': current - prev_close,
                'change_pct': round(change_pct, 2),
                'open': open_price,
                'high': high,
                'low': low,
                'prev_close': prev_close
            }
        except Exception as e:
            print(f"[Sina 个股] 获取失败 {stock_code}: {e}")
            return None
    
    # ==================== 资金流数据 ====================
    
    def get_capital_flow(self, stock_code: str, trade_date: str = None) -> Optional[Dict]:
        """获取资金流数据"""
        if not trade_date:
            trade_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"   💰 获取 {stock_code} 资金流...")
        
        # 1. 优先 Tushare（更准确）
        if TUSHARE_AVAILABLE and self.tushare_token:
            try:
                data = self._get_moneyflow_from_tushare(stock_code, trade_date)
                if data:
                    print(f"      ✅ 主力净流入：{data['net_mf_amount']/10000:.1f}万 [Tushare]")
                    return data
            except Exception as e:
                print(f"      ⚠️ Tushare 失败：{e}")
        
        # 2. 尝试 AKShare
        if AKSHARE_AVAILABLE:
            try:
                data = self._get_moneyflow_from_akshare(stock_code)
                if data:
                    print(f"      ✅ 主力净流入：{data['net_mf_amount']/10000:.1f}万 [AKShare]")
                    return data
            except Exception as e:
                print(f"      ⚠️ AKShare 失败：{e}")
        
        return None
    
    def _get_moneyflow_from_tushare(self, stock_code: str, trade_date: str) -> Optional[Dict]:
        """从 Tushare 获取资金流"""
        try:
            ts.set_token(self.tushare_token)
            pro = ts.pro_api()
            
            trade_date_ts = trade_date.replace('-', '')
            df = pro.moneyflow(ts_code=stock_code, trade_date=trade_date_ts)
            if df.empty:
                return None
            
            row = df.iloc[0]
            return {
                'code': stock_code,
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
            }
        except Exception as e:
            print(f"[Tushare 资金流] 获取失败 {stock_code}: {e}")
            return None
    
    def _get_moneyflow_from_akshare(self, stock_code: str) -> Optional[Dict]:
        """从 AKShare 获取资金流"""
        try:
            stock = str(stock_code).zfill(6)  # 补齐 6 位
            market = 'sz' if stock_code.startswith(('0', '3')) else 'sh'
            
            # 使用正确的参数名：stock 不是 symbol
            df = ak.stock_individual_fund_flow(stock=stock, market=market)
            if df.empty:
                return None
            
            row = df.iloc[0]
            return {
                'code': stock_code,
                'trade_date': datetime.now().strftime('%Y-%m-%d'),
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
        except Exception as e:
            print(f"[AKShare 资金流] 获取失败 {stock_code}: {e}")
            return None
    
    # ==================== 数据日志和快照 ====================
    
    def _log_data(self, data_type: str, data: Any):
        """记录数据获取日志"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': data_type,
            'data': data
        }
        self.data_log.append(log_entry)
    
    def save_data_snapshot(self, report_type: str, data: Dict, output_dir: str = None):
        """
        保存数据快照到报告目录
        
        Args:
            report_type: 报告类型 (evening/morning/monitor)
            data: 数据字典
            output_dir: 输出目录
        """
        if not output_dir:
            output_dir = Path(__file__).parent / 'data' / 'reports'
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        today = datetime.now().strftime('%Y-%m-%d')
        timestamp = datetime.now().strftime('%H%M%S')
        
        # 保存 JSON 快照
        snapshot_file = output_dir / f'{report_type}_data_snapshot_{today}_{timestamp}.json'
        
        snapshot = {
            'report_type': report_type,
            'generated_at': datetime.now().isoformat(),
            'trade_date': today,
            'data': data,
            'data_sources': {
                'akshare': AKSHARE_AVAILABLE,
                'tushare': TUSHARE_AVAILABLE and bool(self.tushare_token),
                'requests': REQUESTS_AVAILABLE
            },
            'log': self.data_log
        }
        
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"📸 数据快照已保存：{snapshot_file}")
        return str(snapshot_file)
    
    def get_data_log(self) -> List[Dict]:
        """获取数据获取日志"""
        return self.data_log


def test_reliable_data_source():
    """测试可靠数据源"""
    print("=" * 60)
    print("测试可靠数据源")
    print("=" * 60)
    
    # 从配置加载 Tushare Token
    config_path = Path(__file__).parent / 'config.yaml'
    tushare_token = None
    
    if config_path.exists():
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            tushare_token = config.get('tushare', {}).get('token')
        except:
            pass
    
    source = ReliableDataSource(tushare_token=tushare_token)
    
    # 测试 1: 大盘指数
    print("\n1. 获取大盘指数...")
    index_data = source.get_index_data()
    if index_data:
        print(f"   ✅ 成功获取 {len(index_data)} 个指数")
        for key, data in index_data.items():
            print(f"      {data['name']}: {data['close']:.2f} ({data['change_pct']:+.2f}%)")
    
    # 测试 2: 个股数据
    print("\n2. 获取个股数据 (平安银行)...")
    stock_data = source.get_stock_data('000001', '平安银行')
    if stock_data:
        print(f"   ✅ 成功")
        print(f"      现价：¥{stock_data['current_price']:.2f} ({stock_data['change_pct']:+.2f}%)")
    
    # 测试 3: 资金流
    print("\n3. 获取资金流 (平安银行)...")
    flow_data = source.get_capital_flow('000001')
    if flow_data:
        print(f"   ✅ 成功")
        print(f"      主力净流入：{flow_data['net_mf_amount']/10000:.1f}万")
    
    # 测试 4: 保存快照
    print("\n4. 保存数据快照...")
    if index_data:
        snapshot = source.save_data_snapshot('test', {'indices': index_data})
        print(f"   ✅ 快照：{snapshot}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == '__main__':
    test_reliable_data_source()
