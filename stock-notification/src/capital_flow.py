"""
资金流分析模块 - 监控板块和个股主力资金
支持：AKShare + 重试机制 + 本地缓存 + 多数据源故障转移
"""
import os
import json
import time
import random
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# 尝试导入 AKShare
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False

import requests


class CacheManager:
    """轻量级缓存管理器（用于资金流模块）"""
    
    def __init__(self, cache_dir: str = None, ttl_seconds: int = 300):
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            script_dir = Path(__file__).parent
            self.cache_dir = script_dir.parent / 'data' / 'cache' / 'capital_flow'
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
    
    def _get_key(self, func_name: str, **kwargs) -> str:
        key_str = f"{func_name}:{json.dumps(kwargs, sort_keys=True, default=str)}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, func_name: str, **kwargs) -> Optional[Dict]:
        key = self._get_key(func_name, **kwargs)
        cache_path = self.cache_dir / f"{key}.json"
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if time.time() - data.get('_cached_at', 0) > self.ttl_seconds:
                cache_path.unlink()
                return None
            
            return data.get('value')
        except:
            return None
    
    def set(self, func_name: str, value: Dict, **kwargs):
        key = self._get_key(func_name, **kwargs)
        cache_path = self.cache_dir / f"{key}.json"
        
        try:
            data = {'value': value, '_cached_at': time.time()}
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"[缓存] 写入失败：{e}")


class CapitalFlowAnalyzer:
    """主力资金流分析器 - 2000 积分增强版"""
    
    def __init__(self, cache_dir: str = None, cache_ttl: int = 300, max_retries: int = 3):
        # 初始化缓存
        self.cache = CacheManager(cache_dir, cache_ttl)
        self.max_retries = max_retries
        
        # 全市场资金流缓存（减少 API 调用）
        self.market_moneyflow_cache = None
        self.market_moneyflow_date = None
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://quote.eastmoney.com/'
        }
        
        # 初始化 Tushare Pro（主数据源 - 2000 积分完整版）
        self.tushare_pro = None
        tushare_token = os.getenv('TUSHARE_TOKEN')
        
        # 如果环境变量没有，尝试从配置文件读取
        if not tushare_token:
            try:
                config_path = Path(__file__).parent.parent / 'config.yaml'
                if config_path.exists():
                    import yaml
                    with open(config_path, 'r') as f:
                        config = yaml.safe_load(f)
                    tushare_token = config.get('tushare', {}).get('token')
                    if tushare_token:
                        print(f"[资金流] 从 config.yaml 读取 Tushare Token")
            except Exception as e:
                print(f"[资金流] 读取配置文件失败：{e}")
        
        if tushare_token:
            try:
                from tushare_pro_source import TushareProSource
                self.tushare_pro = TushareProSource(
                    token=tushare_token,
                    cache_dir=cache_dir,
                    cache_ttl=cache_ttl
                )
                print(f"[资金流] ✅ Tushare Pro 已连接 - 主数据源 (2000 积分)")
                print(f"[资金流]    可用接口：moneyflow, top_list, top_inst, margin, margin_detail, stk_holdertrade")
            except Exception as e:
                print(f"[资金流] ⚠️ Tushare Pro 初始化失败：{e}")
        
        # 板块代码映射（扩展版）
        self.sector_codes = {
            # 科技
            '半导体': 'bk0491',
            '人工智能': 'bk1037',
            '消费电子': 'bk1016',
            '5G': 'bk1022',
            '云计算': 'bk0997',
            '软件': 'bk0479',
            # 新能源
            '新能源': 'bk1023',
            '光伏': 'bk1019',
            '风电': 'bk0970',
            '锂电': 'bk1005',
            '储能': 'bk1152',
            '氢能': 'bk1123',
            # 医药
            '医药生物': 'bk0474',
            '创新药': 'bk1052',
            'CXO': 'bk1099',
            '医疗器械': 'bk0986',
            # 大消费
            '白酒': 'bk0909',
            '食品饮料': 'bk0476',
            '家电': 'bk0467',
            '旅游': 'bk0951',
            # 金融
            '券商': 'bk0473',
            '银行': 'bk0465',
            '保险': 'bk0472',
            # 周期
            '房地产': 'bk0469',
            '建材': 'bk0470',
            '钢铁': 'bk0492',
            '煤炭': 'bk0489',
            '有色': 'bk0488',
            '化工': 'bk0475',
            # 高端制造
            '军工': 'bk0480',
            '航天': 'bk0976',
            '机器人': 'bk1036',
            '高铁': 'bk0950',
            # 其他
            '汽车': 'bk0477',
            '交运': 'bk0468',
            '传媒': 'bk0481',
            '农业': 'bk0471'
        }
        
        # 多个数据源配置
        # 注：东方财富 API 因连接持续失败已禁用 (2026-03-16)
        # 新浪财经 403 错误频发已禁用
        self.data_sources = [
            {
                'name': '腾讯财经',
                'type': 'tencent',
                'priority': 1,
                'enabled': True
            },
            {
                'name': '同花顺',
                'type': 'ths',
                'priority': 2,
                'enabled': True
            }
        ]
        
        # 注：新浪数据源已禁用 (403 错误频发)
        self.sina_source = None
        
        # AKShare 标志（备用数据源）
        if AKSHARE_AVAILABLE:
            print(f"[资金流] ✅ AKShare 可用 - 备用数据源")
        else:
            print(f"[资金流] ⚠️ AKShare 不可用 - 使用网页数据源")
    
    def _request_with_retry(self, url: str, params: dict = None, retries: int = None, 
                           source: str = 'default', use_cache: bool = True) -> Optional[dict]:
        """带重试的 HTTP 请求（支持缓存）"""
        retries = retries if retries is not None else self.max_retries
        
        # 尝试从缓存获取
        if use_cache:
            cached = self.cache.get('http_request', url=url, params=params)
            if cached:
                return cached
        
        for attempt in range(retries):
            try:
                if attempt > 0:
                    # 指数退避 + 随机抖动
                    delay = (1.0 * (2 ** attempt)) + random.uniform(0.1, 0.5)
                    delay = min(delay, 10.0)
                    print(f"[资金流] {source} 重试 ({attempt + 1}/{retries}) - {delay:.1f}秒后...")
                    time.sleep(delay)
                
                response = requests.get(
                    url,
                    params=params,
                    headers=self.headers,
                    timeout=10,
                    verify=False
                )
                response.raise_for_status()
                result = response.json()
                
                # 保存到缓存
                if use_cache and result:
                    self.cache.set('http_request', result, url=url, params=params)
                
                return result
                
            except requests.exceptions.Timeout:
                print(f"[资金流] {source} 超时 (尝试 {attempt + 1}/{retries})")
            except requests.exceptions.ConnectionError:
                print(f"[资金流] {source} 连接失败 (尝试 {attempt + 1}/{retries})")
            except Exception as e:
                print(f"[资金流] {source} 请求失败：{e}")
        
        return None
    
    def get_sector_stocks_tushare(self, sector_name: str) -> List[Dict]:
        """
        Tushare Pro 数据源 - 获取板块成分股和资金流（主数据源）
        
        使用指数成分股接口获取板块股票，再获取资金流数据
        """
        if not self.tushare_pro:
            return []
        
        try:
            # 检查缓存
            cached = self.cache.get('tushare_sector', sector=sector_name)
            if cached:
                print(f"[资金流] {sector_name}: Tushare Pro (缓存) ✅ {len(cached)}只")
                return cached
            
            # 板块代码映射到 Tushare 指数代码
            sector_index_map = {
                '半导体': '880491.TI',  # 东方财富行业指数
                '人工智能': '880485.TI',
                '白酒': '880491.TI',
                '新能源': '880479.TI',
                '券商': '880472.TI',
                '银行': '880470.TI',
                '医药生物': '880405.TI',
                '消费电子': '880493.TI',
                '房地产': '880481.TI',
                '化工': '880407.TI',
                '有色': '880410.TI',
                '汽车': '880482.TI',
                '军工': '880413.TI',
                '光伏': '880487.TI',
                '5G': '880494.TI',
                '机器人': '880495.TI',
                '保险': '880473.TI',
                '食品饮料': '880401.TI',
                '家电': '880483.TI',
                '医疗器械': '880414.TI',
                '创新药': '880505.TI',
                '云计算': '880486.TI',
                '软件': '880478.TI',
                '储能': '880488.TI',
                '锂电': '880489.TI',
            }
            
            index_code = sector_index_map.get(sector_name)
            stocks = []
            
            if index_code:
                # 尝试获取指数成分股
                try:
                    members = self.tushare_pro.get_index_member(index_code=index_code)
                    for member in members[:50]:  # 限制 50 只
                        ts_code = member.get('ts_code', '')
                        if ts_code:
                            # 获取资金流数据
                            today = datetime.now().strftime('%Y%m%d')
                            flow = self.tushare_pro.get_moneyflow(ts_code=ts_code, trade_date=today)
                            
                            stocks.append({
                                'code': ts_code.split('.')[0],
                                'ts_code': ts_code,
                                'name': member.get('name', ''),
                                'price': 0,  # 需要从行情获取
                                'change_pct': 0,
                                'change': 0,
                                'volume': 0,
                                'turnover': 0,
                                'main_force_in': flow.get('net_mf_amount', 0) if flow else 0,
                                'main_force_ratio': 0
                            })
                except Exception as e:
                    print(f"[资金流] {sector_name}: Tushare 成分股获取失败：{e}")
            
            # 如果成分股获取失败，使用股票列表筛选行业
            if not stocks:
                all_stocks = self.tushare_pro.get_stock_list()
                industry_keywords = {
                    '半导体': ['半导体', '芯片', '集成电路'],
                    '人工智能': ['人工智能', 'AI', '智能'],
                    '白酒': ['白酒', '酒业'],
                    '新能源': ['新能源', '光伏', '风电', '锂电'],
                    '券商': ['证券', '券商'],
                    '银行': ['银行'],
                    '医药生物': ['医药', '生物', '医疗'],
                    '消费电子': ['消费电子', '电子'],
                    '房地产': ['房地产', '地产'],
                    '化工': ['化工', '石化'],
                    '有色': ['有色', '金属'],
                    '汽车': ['汽车', '整车'],
                    '军工': ['军工', '航天', '航空'],
                }
                
                keywords = industry_keywords.get(sector_name, [sector_name])
                for stock in all_stocks[:500]:  # 限制检查数量
                    industry = stock.get('industry', '')
                    if any(kw in industry for kw in keywords):
                        ts_code = stock.get('ts_code', '')
                        today = datetime.now().strftime('%Y%m%d')
                        flow = self.tushare_pro.get_moneyflow(ts_code=ts_code, trade_date=today)
                        
                        stocks.append({
                            'code': ts_code.split('.')[0],
                            'ts_code': ts_code,
                            'name': stock.get('name', ''),
                            'price': 0,
                            'change_pct': 0,
                            'change': 0,
                            'volume': 0,
                            'turnover': 0,
                            'main_force_in': flow.get('net_mf_amount', 0) if flow else 0,
                            'main_force_ratio': 0
                        })
                        
                        if len(stocks) >= 50:
                            break
            
            # 保存到缓存
            if stocks:
                self.cache.set('tushare_sector', stocks, sector=sector_name)
                print(f"[资金流] {sector_name}: Tushare Pro ✅ {len(stocks)}只")
            
            return stocks
            
        except Exception as e:
            print(f"[资金流] {sector_name}: Tushare Pro ❌ {e}")
            return []
    
    def get_sector_stocks_akshare(self, sector_name: str) -> List[Dict]:
        """
        AKShare 数据源 - 获取板块成分股（备用）
        """
        if not AKSHARE_AVAILABLE:
            return []
        
        try:
            # 检查缓存
            cached = self.cache.get('akshare_sector', sector=sector_name)
            if cached:
                print(f"[资金流] {sector_name}: AKShare (缓存) ✅ {len(cached)}只")
                return cached
            
            # AKShare 概念板块成分股
            df = ak.stock_board_concept_cons_em(symbol=sector_name)
            
            if df.empty:
                return []
            
            stocks = []
            for _, row in df.iterrows():
                code = row.get('代码', '')
                ts_code = f"{code}.SZ" if code.startswith(('0', '3')) else f"{code}.SH"
                
                stocks.append({
                    'code': code,
                    'ts_code': ts_code,
                    'name': row.get('名称', ''),
                    'price': float(row.get('最新价', 0)) if row.get('最新价') else 0,
                    'change_pct': float(row.get('涨跌幅', 0)) if row.get('涨跌幅') else 0,
                    'change': float(row.get('涨跌额', 0)) if row.get('涨跌额') else 0,
                    'volume': float(row.get('成交量', 0)) if row.get('成交量') else 0,
                    'turnover': float(row.get('成交额', 0)) if row.get('成交额') else 0,
                    'main_force_in': 0,  # AKShare 成分股接口不提供资金流
                    'main_force_ratio': 0
                })
            
            # 保存到缓存
            self.cache.set('akshare_sector', stocks, sector=sector_name)
            
            print(f"[资金流] {sector_name}: AKShare ✅ {len(stocks)}只")
            return stocks
            
        except Exception as e:
            print(f"[资金流] {sector_name}: AKShare ❌ {e}")
            return []
    
    def get_sector_stocks_eastmoney(self, sector_name: str) -> List[Dict]:
        """东方财富数据源 - 获取板块成分股"""
        sector_code = self.sector_codes.get(sector_name)
        if not sector_code:
            return []
        
        url = 'http://push2.eastmoney.com/api/qt/clist/get'
        params = {
            'pn': 1,
            'pz': 50,
            'po': 1,
            'np': 1,
            'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
            'fltt': 2,
            'invt': 2,
            'fid': 'f3',
            'fs': f'b:{sector_code}',
            'fields': 'f12,f14,f2,f3,f4,f5,f6,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205,f124'
        }
        
        data = self._request_with_retry(url, params, source='东方财富')
        if not data:
            return []
        
        stocks = []
        if data.get('data') and data['data'].get('diff'):
            for stock in data['data']['diff']:
                try:
                    stocks.append({
                        'code': str(stock.get('f12', '')),
                        'name': stock.get('f14', ''),
                        'price': float(stock.get('f2', 0)) if stock.get('f2') else 0,
                        'change_pct': float(stock.get('f3', 0)) if stock.get('f3') else 0,
                        'change': float(stock.get('f4', 0)) if stock.get('f4') else 0,
                        'volume': float(stock.get('f5', 0)) if stock.get('f5') else 0,
                        'turnover': float(stock.get('f6', 0)) if stock.get('f6') else 0,
                        'main_force_in': float(stock.get('f62', 0)) if stock.get('f62') else 0,
                        'main_force_ratio': float(stock.get('f184', 0)) if stock.get('f184') else 0
                    })
                except (ValueError, TypeError):
                    continue
        
        return stocks
    
    def get_sector_stocks_tencent(self, sector_name: str) -> List[Dict]:
        """腾讯财经数据源 - 获取板块成分股"""
        sector_code = self.sector_codes.get(sector_name)
        if not sector_code:
            return []
        
        # 腾讯板块成分股 API
        url = 'https://web.ifzq.gtimg.cn/fund/newFund/fundList/getFundInfoRelatedFund'
        params = {
            'index': 0,
            'size': 50,
            'type': 1,
            'order': 3,
            'fundType': 2,
            'plateCode': sector_code
        }
        
        data = self._request_with_retry(url, params, source='腾讯财经')
        if not data or not data.get('data'):
            return []
        
        stocks = []
        try:
            for item in data.get('data', []):
                stocks.append({
                    'code': str(item.get('fcode', '')),
                    'name': item.get('shortname', ''),
                    'price': float(item.get('nav', 0)),
                    'change_pct': float(item.get('growth', 0)),
                    'main_force_in': 0,  # 腾讯不提供资金流
                    'main_force_ratio': 0
                })
        except Exception:
            pass
        
        return stocks
    
    def get_sector_stocks_sina(self, sector_name: str) -> List[Dict]:
        """新浪财经数据源 - 获取板块成分股"""
        sector_code = self.sector_codes.get(sector_name)
        if not sector_code:
            return []
        
        # 新浪板块成分股 API
        url = f'http://money.finance.sina.com.cn/d/api/openapi.php/PlateController.getPlateStockList'
        params = {
            'plate': sector_code,
            'page': 1,
            'num': 50
        }
        
        data = self._request_with_retry(url, params, source='新浪财经')
        if not data:
            return []
        
        stocks = []
        try:
            result = data.get('result', {})
            for item in result.get('data', []):
                stocks.append({
                    'code': str(item.get('symbol', '')),
                    'name': item.get('name', ''),
                    'price': float(item.get('price', 0)),
                    'change_pct': float(item.get('changepercent', 0)),
                    'main_force_in': 0,
                    'main_force_ratio': 0
                })
        except Exception:
            pass
        
        return stocks
    
    def _get_sector_with_market_flow(self, sector_name: str, market_flow: List[Dict]) -> List[Dict]:
        """
        使用本地板块成分股 + Tushare 市场资金流
        快速获取板块资金流数据（包含涨跌幅）
        """
        # 本地板块成分股映射
        sector_stocks_map = {
            '半导体': ['688981', '002371', '603986', '300782', '688012', '002156', '600584', '300661', '688396', '603005'],
            '人工智能': ['002230', '300624', '002153', '600845', '300033', '002405', '600570', '300271', '002065', '600588'],
            '白酒': ['600519', '000858', '000568', '600809', '600779', '000799', '600702', '603198', '603369', '002646'],
            '新能源': ['300750', '002594', '002466', '300014', '601012', '002129', '600438', '300274', '603799', '002709'],
            '券商': ['300059', '600030', '601688', '600837', '600999', '000776', '600958', '601375', '002673', '601198'],
            '银行': ['601398', '601288', '600036', '601166', '600000', '601939', '601988', '601328', '600016', '601169'],
            '医药生物': ['300760', '000538', '300122', '600276', '000963', '300015', '600436', '002007', '600196', '300142'],
            '消费电子': ['002475', '002241', '300433', '002384', '601138', '002036', '300115', '002600', '600745', '300088'],
            '房地产': ['000002', '001979', '600048', '601155', '000671', '600383', '000961', '600325', '000402', '600823'],
            '化工': ['600309', '002497', '000792', '600426', '002648', '600141', '002001', '600352', '002588', '600096'],
            '有色': ['601899', '000878', '000630', '600547', '600489', '000975', '601600', '002460', '600362', '000807'],
            '汽车': ['000625', '002594', '000100', '601238', '600104', '000338', '601689', '002126', '600741', '000550'],
            '军工': ['002013', '600765', '000768', '600893', '002179', '600316', '002025', '600150', '000738', '600495'],
            '光伏': ['002459', '002129', '300274', '601012', '600438', '002056', '300118', '600732', '002610', '601778'],
            '5G': ['000063', '002792', '300308', '002194', '600498', '300394', '002281', '600260', '300134', '002446'],
            '机器人': ['002747', '300024', '002164', '603666', '300170', '002011', '600835', '300024', '002527', '603960'],
            '保险': ['601318', '601628', '601601', '601336', '601339', '002958', '601136', '600116', '000627', '600705'],
            '食品饮料': ['000858', '600887', '002714', '603288', '000568', '600597', '600873', '002557', '603345', '002216'],
            '家电': ['000651', '000333', '600690', '002032', '600060', '002242', '600983', '002508', '603196', '002050'],
            '医疗器械': ['300760', '300015', '300529', '603392', '300203', '300633', '603882', '300482', '600998', '300595'],
            '创新药': ['600276', '000963', '600196', '300122', '688266', '688180', '688363', '688029', '688520', '688166'],
            '云计算': ['002230', '600845', '002153', '603881', '300383', '002368', '600850', '300212', '002065', '600588'],
            '软件': ['002230', '600570', '300170', '601360', '300454', '600588', '300271', '002065', '300166', '600410'],
            '储能': ['300750', '002594', '300014', '002466', '601012', '002129', '300274', '600438', '002056', '603799'],
            '锂电': ['300750', '002466', '002129', '300014', '601012', '002709', '603799', '300274', '600438', '002056'],
        }
        
        stock_codes = sector_stocks_map.get(sector_name, [])
        if not stock_codes:
            return []
        
        # 创建代码到资金流的映射
        flow_map = {item['code']: item for item in market_flow}
        
        result = []
        for code in stock_codes[:15]:  # 取前 15 只
            flow_data = flow_map.get(code, {})
            # 优先使用 moneyflow 的主力资金流（真实数据），其次使用龙虎榜数据
            main_force = flow_data.get('main_force_in', 0)
            if main_force == 0:
                main_force = flow_data.get('top_net_in', 0)
            
            # 🔥 修复：从 market_flow 获取真实的涨跌幅数据
            change_pct = flow_data.get('change_pct', 0)
            price = flow_data.get('close', 0) or flow_data.get('price', 0)
            
            result.append({
                'code': code,
                'name': flow_data.get('name', ''),
                'price': price,
                'change_pct': change_pct,  # 🔥 使用真实涨跌幅
                'main_force_in': main_force,  # 主力净流入 (优先 moneyflow)
                'inst_net': flow_data.get('inst_net', 0),  # 机构净买入
                'financing_net': flow_data.get('financing_net', 0),  # 融资净买入
                'top_reason': flow_data.get('top_reason', ''),  # 上榜原因
                'main_force_ratio': 0
            })
        
        return result
    
    def get_sector_stocks_fallback(self, sector_name: str) -> List[Dict]:
        """
        使用本地板块成分股列表（备用方案）
        当所有 API 都失败时使用
        """
        # 预定义的板块成分股（简化版，每个板块 10 只代表性股票）
        sector_stocks_map = {
            '半导体': ['688981.SH', '002371.SZ', '603986.SH', '300782.SZ', '688012.SH',
                      '002156.SZ', '600584.SH', '300661.SZ', '688396.SH', '603005.SH'],
            '人工智能': ['002230.SZ', '300624.SZ', '002153.SZ', '600845.SH', '300033.SZ',
                        '002405.SZ', '600570.SH', '300271.SZ', '002065.SZ', '600588.SH'],
            '白酒': ['600519.SH', '000858.SZ', '000568.SZ', '600809.SH', '600779.SH',
                    '000799.SZ', '600702.SH', '603198.SH', '603369.SH', '002646.SZ'],
            '新能源': ['300750.SZ', '002594.SZ', '002466.SZ', '300014.SZ', '601012.SH',
                      '002129.SZ', '600438.SH', '300274.SZ', '603799.SH', '002709.SZ'],
            '券商': ['300059.SZ', '600030.SH', '601688.SH', '600837.SH', '600999.SH',
                    '000776.SZ', '600958.SH', '601375.SH', '002673.SZ', '601198.SH'],
            '银行': ['601398.SH', '601288.SH', '600036.SH', '601166.SH', '600000.SH',
                    '601939.SH', '601988.SH', '601328.SH', '600016.SH', '601169.SH'],
            '医药生物': ['300760.SZ', '000538.SZ', '300122.SZ', '600276.SH', '000963.SZ',
                        '300015.SZ', '600436.SH', '002007.SZ', '600196.SH', '300142.SZ'],
            '消费电子': ['002475.SZ', '002241.SZ', '300433.SZ', '002384.SZ', '601138.SH',
                        '002036.SZ', '300115.SZ', '002600.SZ', '600745.SH', '300088.SZ'],
            '房地产': ['000002.SZ', '001979.SZ', '600048.SH', '601155.SH', '000671.SZ',
                      '600383.SH', '000961.SZ', '600325.SH', '000402.SZ', '600823.SH'],
            '化工': ['600309.SH', '002497.SZ', '000792.SZ', '600426.SH', '002648.SZ',
                    '600141.SH', '002001.SZ', '600352.SH', '002588.SZ', '600096.SH'],
            '有色': ['601899.SH', '000878.SZ', '000630.SZ', '600547.SH', '600489.SH',
                    '000975.SZ', '601600.SH', '002460.SZ', '600362.SH', '000807.SZ'],
            '汽车': ['000625.SZ', '002594.SZ', '000100.SZ', '601238.SH', '600104.SH',
                    '000338.SZ', '601689.SH', '002126.SZ', '600741.SH', '000550.SZ'],
            '军工': ['002013.SZ', '600765.SH', '000768.SZ', '600893.SH', '002179.SZ',
                    '600316.SH', '002025.SZ', '600150.SH', '000738.SZ', '600495.SH'],
            '光伏': ['002459.SZ', '002129.SZ', '300274.SZ', '601012.SH', '600438.SH',
                    '002056.SZ', '300118.SZ', '600732.SH', '002610.SZ', '601778.SH'],
            '5G': ['000063.SZ', '002792.SZ', '300308.SZ', '002194.SZ', '600498.SH',
                  '300394.SZ', '002281.SZ', '600260.SH', '300134.SZ', '002446.SZ'],
            '机器人': ['002747.SZ', '300024.SZ', '002164.SZ', '603666.SH', '300170.SZ',
                      '002011.SZ', '600835.SH', '300024.SZ', '002527.SZ', '603960.SH'],
            '保险': ['601318.SH', '601628.SH', '601601.SH', '601336.SH', '601339.SH',
                    '002958.SZ', '601136.SH', '600116.SH', '000627.SZ', '600705.SH'],
            '食品饮料': ['000858.SZ', '600887.SH', '002714.SZ', '603288.SH', '000568.SZ',
                        '600597.SH', '600873.SH', '002557.SZ', '603345.SH', '002216.SZ'],
            '家电': ['000651.SZ', '000333.SZ', '600690.SH', '002032.SZ', '600060.SH',
                    '002242.SZ', '600983.SH', '002508.SZ', '603196.SH', '002050.SZ'],
            '医疗器械': ['300760.SZ', '300015.SZ', '300529.SZ', '603392.SH', '300203.SZ',
                        '300633.SZ', '603882.SH', '300482.SZ', '600998.SH', '300595.SZ'],
            '创新药': ['600276.SH', '000963.SZ', '600196.SH', '300122.SZ', '688266.SH',
                      '688180.SH', '688363.SH', '688029.SH', '688520.SH', '688166.SH'],
            '云计算': ['002230.SZ', '600845.SH', '002153.SZ', '603881.SH', '300383.SZ',
                      '002368.SZ', '600850.SH', '300212.SZ', '002065.SZ', '600588.SH'],
            '软件': ['002230.SZ', '600570.SH', '300170.SZ', '601360.SH', '300454.SZ',
                    '600588.SH', '300271.SZ', '002065.SZ', '300166.SZ', '600410.SH'],
            '储能': ['300750.SZ', '002594.SZ', '300014.SZ', '002466.SZ', '601012.SH',
                    '002129.SZ', '300274.SZ', '600438.SH', '002056.SZ', '603799.SH'],
            '锂电': ['300750.SZ', '002466.SZ', '002129.SZ', '300014.SZ', '601012.SH',
                    '002709.SZ', '603799.SH', '300274.SZ', '600438.SH', '002056.SZ'],
        }
        
        stocks = sector_stocks_map.get(sector_name, [])
        if not stocks:
            return []
        
        # 注：新浪数据源已禁用，返回基础成分股列表（无实时行情）
        # 使用本地板块成分股列表（备用方案）
        result = []
        for ts_code in stocks[:10]:  # 限制 10 只
            code = ts_code.split('.')[0]
            result.append({
                'code': code,
                'ts_code': ts_code,
                'name': '',  # 名称需要从其他数据源获取
                'price': 0,
                'change_pct': 0,
                'change': 0,
                'volume': 0,
                'turnover': 0,
                'main_force_in': 0,
                'main_force_ratio': 0
            })
        return result
    
    def get_market_moneyflow(self, trade_date: str = None) -> List[Dict]:
        """
        获取全市场资金流（Tushare 2000 积分）
        优先使用 moneyflow 接口（有真实数据）
        """
        if not self.tushare_pro:
            return []
        
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        # 检查缓存（同一交易日不重复获取）
        if self.market_moneyflow_cache and self.market_moneyflow_date == trade_date:
            return self.market_moneyflow_cache
        
        try:
            print(f"[资金流] 获取全市场资金流数据...")
            
            # 1. 获取龙虎榜数据（上榜股票）
            top_list = self.tushare_pro.get_top_list(trade_date=trade_date)
            top_inst = self.tushare_pro.get_top_inst(trade_date=trade_date)
            
            # 2. 获取融资融券
            margin = []
            margin_detail = []
            try:
                margin = self.tushare_pro.get_margin(trade_date=trade_date)
                margin_detail = self.tushare_pro.get_margin_detail(trade_date=trade_date)
            except Exception as e:
                print(f"[资金流] 融资融券获取失败：{e}")
            
            # 合并数据
            market_flow = {}
            
            # 龙虎榜数据（字段：net_amount, l_buy, l_sell, amount）
            for item in top_list:
                code = item.get('ts_code', '').split('.')[0]
                if code:
                    market_flow[code] = {
                        'code': code,
                        'name': item.get('name', ''),
                        'top_net_in': item.get('net_in', 0),  # 龙虎榜净流入 (net_amount)
                        'top_amount': item.get('amount', 0),  # 总成交额
                        'top_l_buy': item.get('l_buy', 0),  # 龙虎榜买入
                        'top_l_sell': item.get('l_sell', 0),  # 龙虎榜卖出
                        'top_reason': item.get('reason', ''),  # 上榜原因
                        'change_pct': item.get('change_pct', 0)  # 涨跌幅
                    }
            
            # 机构交易数据
            for item in top_inst:
                code = item.get('ts_code', '').split('.')[0]
                if code:
                    if code not in market_flow:
                        market_flow[code] = {'code': code, 'name': item.get('name', '')}
                    market_flow[code]['inst_buy'] = item.get('buy_amount', 0)
                    market_flow[code]['inst_sell'] = item.get('sell_amount', 0)
                    market_flow[code]['inst_net'] = item.get('net_amount', 0)
            
            # 融资融券数据
            for item in margin:
                code = item.get('ts_code', '').split('.')[0]
                if code:
                    if code not in market_flow:
                        market_flow[code] = {'code': code, 'name': item.get('name', '')}
                    market_flow[code]['financing_net'] = item.get('net_financing', 0)
            
            # 获取所有板块成分股的主力资金流（moneyflow 接口有真实数据）
            print(f"[资金流] 获取板块成分股主力资金流...")
            all_sector_stocks = {
                '半导体': ['688981', '002371', '603986', '300782', '688012', '002156', '600584', '300661', '688396', '603005'],
                '人工智能': ['002230', '300624', '002153', '600845', '300033', '002405', '600570', '300271', '002065', '600588'],
                '消费电子': ['002475', '002241', '300433', '002384', '601138', '002036', '300115', '002600', '600745', '300088'],
                '5G': ['000063', '002792', '300308', '002194', '600498', '300394', '002281', '600260', '300134', '002446'],
                '云计算': ['002230', '600845', '002153', '603881', '300383', '002368', '600850', '300212', '002065', '600588'],
                '软件': ['002230', '600570', '300170', '601360', '300454', '600588', '300271', '002065', '300166', '600410'],
                '新能源': ['300750', '002594', '002466', '300014', '601012', '002129', '600438', '300274', '603799', '002709'],
                '光伏': ['002459', '002129', '300274', '601012', '600438', '002056', '300118', '600732', '002610', '601778'],
                '储能': ['300750', '002594', '300014', '002466', '601012', '002129', '300274', '600438', '002056', '603799'],
                '锂电': ['300750', '002466', '002129', '300014', '601012', '002709', '603799', '300274', '600438', '002056'],
                '白酒': ['600519', '000858', '000568', '600809', '600779', '000799', '600702', '603198', '603369', '002646'],
                '食品饮料': ['000858', '600887', '002714', '603288', '000568', '600597', '600873', '002557', '603345', '002216'],
                '医药生物': ['300760', '000538', '300122', '600276', '000963', '300015', '600436', '002007', '600196', '300142'],
                '创新药': ['600276', '000963', '600196', '300122', '688266', '688180', '688363', '688029', '688520', '688166'],
                '医疗器械': ['300760', '300015', '300529', '603392', '300203', '300633', '603882', '300482', '600998', '300595'],
                '家电': ['000651', '000333', '600690', '002032', '600060', '002242', '600983', '002508', '603196', '002050'],
                '券商': ['300059', '600030', '601688', '600837', '600999', '000776', '600958', '601375', '002673', '601198'],
                '银行': ['601398', '601288', '600036', '601166', '600000', '601939', '601988', '601328', '600016', '601169'],
                '保险': ['601318', '601628', '601601', '601336', '601339', '002958', '601136', '600116', '000627', '600705'],
                '房地产': ['000002', '001979', '600048', '601155', '000671', '600383', '000961', '600325', '000402', '600823'],
                '化工': ['600309', '002497', '000792', '600426', '002648', '600141', '002001', '600352', '002588', '600096'],
                '有色': ['601899', '000878', '000630', '600547', '600489', '000975', '601600', '002460', '600362', '000807'],
                '汽车': ['000625', '002594', '000100', '601238', '600104', '000338', '601689', '002126', '600741', '000550'],
                '军工': ['002013', '600765', '000768', '600893', '002179', '600316', '002025', '600150', '000738', '600495'],
                '机器人': ['002747', '300024', '002164', '603666', '300170', '002011', '600835', '300024', '002527', '603960'],
            }
            
            # 合并所有股票代码
            all_codes = set()
            for stocks in all_sector_stocks.values():
                all_codes.update(stocks)
            
            print(f"[资金流] 获取 {len(all_codes)} 只成分股资金流和行情...")
            success_count = 0
            for code in all_codes:
                try:
                    ts_code = f"{code}.SZ" if code.startswith(('0', '3')) else f"{code}.SH"
                    
                    # 🔥 获取日线行情（包含涨跌幅）
                    daily = self.tushare_pro.get_daily(ts_code=ts_code, trade_date=trade_date)
                    
                    # 获取资金流
                    mf = self.tushare_pro.get_moneyflow(ts_code=ts_code, trade_date=trade_date)
                    
                    if daily or mf:
                        if code not in market_flow:
                            market_flow[code] = {'code': code, 'name': ''}
                        
                        # 🔥 从日线获取涨跌幅和价格
                        if daily:
                            market_flow[code]['close'] = daily.get('close', 0)
                            market_flow[code]['change_pct'] = daily.get('pct_chg', 0)
                            market_flow[code]['name'] = daily.get('name', market_flow[code].get('name', ''))
                        
                        # 从资金流获取主力资金
                        if mf:
                            net_mf = mf.get('net_mf_amount', 0)
                            market_flow[code]['main_force_in'] = net_mf
                            market_flow[code]['buy_elg'] = mf.get('buy_elg_amount', 0)
                            market_flow[code]['sell_elg'] = mf.get('sell_elg_amount', 0)
                        
                        success_count += 1
                except Exception as e:
                    pass
            
            print(f"[资金流] ✅ 成功获取 {success_count}/{len(all_codes)} 只股票资金流和行情")
            
            result = list(market_flow.values())
            
            # 缓存结果
            self.market_moneyflow_cache = result
            self.market_moneyflow_date = trade_date
            
            print(f"[资金流] ✅ 获取全市场资金流 {len(result)} 只")
            return result
            
        except Exception as e:
            print(f"[资金流] 全市场资金流获取失败：{e}")
            return []
    
    def get_sector_stocks(self, sector_name: str) -> List[Dict]:
        """获取板块成分股（多数据源智能选择）"""
        # 数据源优先级：Tushare Pro (2000 积分) > AKShare > 腾讯财经 > 本地列表
        
        # 1. 优先使用 Tushare Pro（主数据源，2000 积分包含资金流）
        if self.tushare_pro:
            # 先尝试获取全市场资金流，然后筛选板块
            market_flow = self.get_market_moneyflow()
            if market_flow:
                # 使用本地板块成分股映射 + Tushare 资金流
                stocks = self._get_sector_with_market_flow(sector_name, market_flow)
                if stocks:
                    print(f"[资金流] {sector_name}: Tushare 资金流 ✅ {len(stocks)}只")
                    return stocks
            
            # 回退到成分股 + 个股资金流
            stocks = self.get_sector_stocks_tushare(sector_name)
            if stocks:
                return stocks
            print(f"[资金流] {sector_name}: Tushare Pro ❌ 尝试其他数据源...")
        
        # 2. 使用 AKShare（免费、开源）
        if AKSHARE_AVAILABLE:
            stocks = self.get_sector_stocks_akshare(sector_name)
            if stocks:
                return stocks
            print(f"[资金流] {sector_name}: AKShare ❌ 尝试其他数据源...")
        
        # 3. 腾讯财经（备用）
        stocks = self.get_sector_stocks_tencent(sector_name)
        if stocks:
            print(f"[资金流] {sector_name}: 腾讯财经 ✅ {len(stocks)}只")
            return stocks
        
        # 4. 使用本地成分股列表 + 行情（最终备选）
        print(f"[资金流] {sector_name}: 使用本地成分股列表...")
        stocks = self.get_sector_stocks_fallback(sector_name)
        if stocks:
            print(f"[资金流] {sector_name}: 本地列表 ✅ {len(stocks)}只")
            return stocks
        
        print(f"[资金流] {sector_name}: ❌ 所有数据源失败")
        return []
    
    def analyze_sector_flow(self, sector_name: str, threshold: int = 10000) -> Dict:
        """分析板块资金流（单位：万元）"""
        stocks = self.get_sector_stocks(sector_name)
        
        if not stocks:
            return {'error': '无数据', 'stock_count': 0}
        
        # 计算板块总体资金流
        stocks_with_flow = [s for s in stocks if s.get('main_force_in', 0) != 0]
        
        if stocks_with_flow:
            total_inflow = sum(s['main_force_in'] for s in stocks_with_flow if s['main_force_in'] > 0)
            total_outflow = sum(s['main_force_in'] for s in stocks_with_flow if s['main_force_in'] < 0)
            net_flow = total_inflow + total_outflow
        else:
            # 没有资金流数据，用涨跌幅估算
            total_inflow = sum(s.get('change_pct', 0) * 100 for s in stocks if s.get('change_pct', 0) > 0)
            total_outflow = sum(s.get('change_pct', 0) * 100 for s in stocks if s.get('change_pct', 0) < 0)
            net_flow = total_inflow + total_outflow
        
        # 找出资金流入最多的股票
        inflow_stocks = sorted(
            [s for s in stocks if s.get('main_force_in', 0) > threshold],
            key=lambda x: x.get('main_force_in', 0),
            reverse=True
        )
        
        # 找出领涨股票
        leader_stocks = sorted(
            [s for s in stocks if s.get('change_pct', 0) > 0],
            key=lambda x: x.get('change_pct', 0),
            reverse=True
        )[:5]
        
        # 找出资金流入龙头
        flow_leaders = sorted(
            [s for s in stocks if s.get('main_force_in', 0) > 0],
            key=lambda x: x.get('main_force_in', 0),
            reverse=True
        )[:3]
        
        return {
            'sector': sector_name,
            'stock_count': len(stocks),
            'stocks_with_flow': len(stocks_with_flow),
            'total_inflow': round(total_inflow, 2),
            'total_outflow': round(total_outflow, 2),
            'net_flow': round(net_flow, 2),
            'trend': '流入' if net_flow > 0 else '流出',
            'inflow_stocks': inflow_stocks[:5],
            'flow_leaders': flow_leaders,
            'leaders': leader_stocks,
            'update_time': datetime.now().isoformat()
        }
    
    def get_top_sectors_by_flow(self, sectors: List[str], top_n: int = 5) -> List[Dict]:
        """获取资金流入最多的板块"""
        results = []
        
        for sector in sectors:
            flow_data = self.analyze_sector_flow(sector)
            if 'error' not in flow_data or flow_data.get('stock_count', 0) > 0:
                results.append(flow_data)
        
        # 按净流入排序
        results.sort(key=lambda x: x.get('net_flow', 0), reverse=True)
        
        return results[:top_n]
    
    def identify_sector_leader(self, sector_name: str) -> Optional[Dict]:
        """识别板块龙头股（综合资金流和涨幅）"""
        stocks = self.get_sector_stocks(sector_name)
        
        if not stocks:
            return None
        
        # 综合评分：资金流权重 60% + 涨幅权重 40%
        scored_stocks = []
        for stock in stocks:
            flow_score = stock.get('main_force_in', 0) / 1000000  # 归一化
            change_score = stock.get('change_pct', 0)
            total_score = flow_score * 0.6 + change_score * 0.4
            
            scored_stocks.append({
                **stock,
                'score': total_score
            })
        
        # 按综合评分排序
        scored_stocks.sort(key=lambda x: x['score'], reverse=True)
        
        if scored_stocks:
            leader = scored_stocks[0]
            return {
                'code': leader['code'],
                'name': leader['name'],
                'price': leader.get('price', 0),
                'change_pct': leader.get('change_pct', 0),
                'main_force_in': leader.get('main_force_in', 0),
                'main_force_ratio': leader.get('main_force_ratio', 0),
                'score': round(leader['score'], 2),
                'reason': self._get_leader_reason(leader)
            }
        
        return None
    
    def _get_leader_reason(self, stock: Dict) -> str:
        """生成龙头股推荐理由"""
        reasons = []
        
        if stock.get('main_force_in', 0) > 5000:
            reasons.append(f"主力净流入{stock['main_force_in']/10000:.1f}亿")
        if stock.get('change_pct', 0) > 5:
            reasons.append(f"涨幅{stock['change_pct']:.2f}%领涨板块")
        if stock.get('main_force_ratio', 0) > 10:
            reasons.append(f"主力占比{stock['main_force_ratio']:.1f}%")
        
        return '，'.join(reasons) if reasons else '综合评分最高'
    
    def run(self, sectors: List[str], threshold: int = 10000) -> Dict:
        """执行完整资金流分析"""
        print("[资金流] 开始分析板块资金流...")
        print(f"[资金流] 数据源优先级：Tushare Pro (主) > AKShare > 腾讯财经 > 本地列表")
        print(f"[资金流] 已禁用：东方财富 (连接失败), 新浪财经 (403 错误)")
        
        results = {}
        successful_sectors = []
        failed_sectors = []
        
        for sector in sectors:
            print(f"[资金流] 分析 {sector}...")
            flow_data = self.analyze_sector_flow(sector, threshold)
            leader = self.identify_sector_leader(sector)
            
            if flow_data.get('stock_count', 0) > 0:
                successful_sectors.append(sector)
            else:
                failed_sectors.append(sector)
            
            results[sector] = {
                'flow': flow_data,
                'leader': leader
            }
        
        # 找出资金流入最多的板块
        top_sectors = self.get_top_sectors_by_flow(sectors)
        
        print(f"[资金流] 分析完成：成功 {len(successful_sectors)} 个，失败 {len(failed_sectors)} 个")
        if failed_sectors:
            print(f"[资金流] 失败板块：{', '.join(failed_sectors)}")
        
        return {
            'sector_analysis': results,
            'top_inflow_sectors': top_sectors,
            'successful_sectors': successful_sectors,
            'failed_sectors': failed_sectors,
            'update_time': datetime.now().isoformat()
        }


if __name__ == '__main__':
    # 测试
    analyzer = CapitalFlowAnalyzer()
    sectors = ['半导体', '人工智能', '新能源', '医药生物', '白酒', '券商']
    result = analyzer.run(sectors)
    
    print("\n=== 资金流入前三板块 ===")
    for i, sector in enumerate(result['top_inflow_sectors'][:3], 1):
        print(f"{i}. {sector['sector']}: 净流入 {sector['net_flow']:.2f}万")
    
    print("\n=== 板块龙头 ===")
    for sector, data in result['sector_analysis'].items():
        if data['leader']:
            l = data['leader']
            print(f"{sector}: {l['name']}({l['code']}) - {l['reason']}")
