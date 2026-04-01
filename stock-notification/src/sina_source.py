"""
新浪财经数据源 - 提供实时行情和资金流
"""
import requests
import time
from datetime import datetime
from typing import List, Dict, Optional


class SinaSource:
    """新浪财经数据源"""
    
    def __init__(self):
        self.base_url = 'https://hq.sinajs.cn/'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Referer': 'https://finance.sina.com.cn/'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_quote(self, symbol: str) -> Optional[Dict]:
        """
        获取实时行情
        
        Args:
            symbol: 股票代码 (如 s_sh600000, sz000001)
        
        Returns:
            行情数据
        """
        try:
            url = f'{self.base_url}list={symbol}'
            response = self.session.get(url, timeout=10, verify=False)
            
            if response.status_code != 200:
                return None
            
            # 解析新浪行情格式
            # var hq_str_s_sh600000="浦发银行，9.890,0.110,1.12,727260,71478";
            text = response.text.strip()
            if not text or '=' not in text:
                return None
            
            parts = text.split('=')
            if len(parts) < 2:
                return None
            
            # 清理引号和多余字符
            data_str = parts[1].strip().strip('"').strip(';').strip('"')
            fields = data_str.split(',')
            
            if len(fields) < 5:
                return None
            
            # 安全转换函数
            def safe_float(val, default=0):
                try:
                    return float(val) if val else default
                except (ValueError, TypeError):
                    return default
            
            def safe_int(val, default=0):
                try:
                    return int(float(val)) if val else default
                except (ValueError, TypeError):
                    return default
            
            return {
                'name': fields[0],
                'price': safe_float(fields[1]),
                'change': safe_float(fields[2]),
                'change_pct': safe_float(fields[3]),
                'volume': safe_int(fields[4]),
                'turnover': safe_float(fields[5]),
                'time': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"[新浪] 行情获取失败 {symbol}: {e}")
            return None
    
    def get_quotes_batch(self, symbols: List[str]) -> List[Dict]:
        """
        批量获取行情（最多 1020 个）
        
        Args:
            symbols: 股票代码列表
        
        Returns:
            行情数据列表
        """
        if not symbols:
            return []
        
        # 新浪支持批量查询，用逗号分隔
        symbol_str = ','.join(symbols[:1020])
        
        try:
            url = f'{self.base_url}list={symbol_str}'
            response = self.session.get(url, timeout=15, verify=False)
            
            if response.status_code != 200:
                return []
            
            def safe_float(val, default=0):
                try:
                    return float(val) if val else default
                except (ValueError, TypeError):
                    return default
            
            def safe_int(val, default=0):
                try:
                    return int(float(val)) if val else default
                except (ValueError, TypeError):
                    return default
            
            results = []
            for line in response.text.strip().split('\n'):
                if '=' not in line:
                    continue
                
                parts = line.split('=')
                if len(parts) < 2:
                    continue
                
                symbol = parts[0].replace('var hq_str_', '')
                data_str = parts[1].strip().strip('"').strip(';').strip('"')
                fields = data_str.split(',')
                
                if len(fields) >= 5 and fields[1]:
                    results.append({
                        'symbol': symbol,
                        'name': fields[0],
                        'price': safe_float(fields[1]),
                        'change': safe_float(fields[2]),
                        'change_pct': safe_float(fields[3]),
                        'volume': safe_int(fields[4]),
                        'turnover': safe_float(fields[5])
                    })
            
            return results
            
        except Exception as e:
            print(f"[新浪] 批量行情获取失败：{e}")
            return []
    
    def symbol_to_sina(self, ts_code: str) -> str:
        """
        转换 Tushare 代码为新浪格式
        
        Args:
            ts_code: Tushare 代码 (如 600000.SH)
        
        Returns:
            新浪代码 (如 s_sh600000)
        """
        if '.' in ts_code:
            code, exchange = ts_code.split('.')
            if exchange in ['SH', 'SSE']:
                return f's_sh{code}'
            elif exchange in ['SZ', 'SZSE']:
                return f'sz{code}'
        return ts_code.lower()
    
    def get_sector_quotes(self, sector_stocks: List[str]) -> List[Dict]:
        """
        获取板块成分股行情
        
        Args:
            sector_stocks: 股票代码列表
        
        Returns:
            行情数据
        """
        sina_symbols = [self.symbol_to_sina(s) for s in sector_stocks]
        return self.get_quotes_batch(sina_symbols)
    
    def calculate_sector_flow(self, quotes: List[Dict]) -> Dict:
        """
        根据行情计算板块资金流（估算）
        
        Args:
            quotes: 行情数据
        
        Returns:
            板块资金流统计
        """
        if not quotes:
            return {'error': '无数据'}
        
        # 估算：用涨跌幅和成交量模拟资金流
        total_volume = sum(q.get('volume', 0) for q in quotes)
        avg_change_pct = sum(q.get('change_pct', 0) for q in quotes) / len(quotes)
        
        # 估算主力净流入（简化模型）
        estimated_inflow = total_volume * avg_change_pct * 0.01  # 粗略估算
        
        # 找出领涨股票
        leaders = sorted(quotes, key=lambda x: x.get('change_pct', 0), reverse=True)[:5]
        
        return {
            'stock_count': len(quotes),
            'total_volume': total_volume,
            'avg_change_pct': round(avg_change_pct, 2),
            'estimated_net_flow': round(estimated_inflow, 2),
            'trend': '流入' if avg_change_pct > 0 else '流出',
            'leaders': leaders
        }


def test_sina():
    """测试新浪数据源"""
    print("=" * 60)
    print("测试新浪财经数据源")
    print("=" * 60)
    
    source = SinaSource()
    
    # 测试 1: 单只股票
    print("\n1. 测试单只股票行情...")
    symbols = ['s_sh600000', 's_sh601318', 'sz000001']
    for sym in symbols:
        quote = source.get_quote(sym)
        if quote:
            print(f"   ✅ {sym}: {quote['name']} ¥{quote['price']:.2f} ({quote['change_pct']:+.2f}%)")
        else:
            print(f"   ❌ {sym}: 失败")
    
    # 测试 2: 批量查询
    print("\n2. 测试批量查询...")
    quotes = source.get_quotes_batch(symbols)
    print(f"   获取 {len(quotes)} 只股票行情")
    
    # 测试 3: 代码转换
    print("\n3. 测试代码转换...")
    test_codes = ['600000.SH', '000001.SZ', '300750.SZ']
    for code in test_codes:
        sina_code = source.symbol_to_sina(code)
        print(f"   {code} -> {sina_code}")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    test_sina()
