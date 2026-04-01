#!/usr/bin/env python3
"""
持仓监控股价修复脚本

问题：周末/节假日获取不到股价数据
修复：回退到最近交易日数据
"""
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime, timedelta

def fix_monitor_py():
    """修复 monitor.py"""
    monitor_file = Path('/home/admin/.openclaw/workspace/stock-notification/monitor.py')
    
    if not monitor_file.exists():
        print(f"❌ 文件不存在：{monitor_file}")
        return False
    
    # 读取原文件
    with open(monitor_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换 _get_stock_data 方法
    old_method = '''    def _get_stock_data(self, code: str, name: str) -> dict:
        """获取股票数据（使用 Tushare 直接获取）"""
        try:
            # 确定交易所
            if code.startswith('6'):
                ts_code = f"{code}.SH"
            else:
                ts_code = f"{code}.SZ"
            
            # 使用 Tushare 获取日线行情
            today = datetime.now().strftime('%Y%m%d')
            df = self.tushare_pro.daily(ts_code=ts_code, start_date=today, end_date=today)
            
            if df is not None and len(df) > 0:
                row = df.iloc[0]
                return {
                    'current_price': float(row.get('close', 0)),
                    'change_percent': float(row.get('pct_chg', 0)),
                    'open': float(row.get('open', 0)),
                    'high': float(row.get('high', 0)),
                    'low': float(row.get('low', 0)),
                    'pre_close': float(row.get('pre_close', 0))
                }
        except Exception as e:
            print(f"[Tushare] 获取 {code} 失败：{e}")
        
        # 降级：返回空数据
        return {'current_price': 0, 'change_percent': 0}'''
    
    new_method = '''    def _get_stock_data(self, code: str, name: str) -> dict:
        """获取股票数据（使用 Tushare 直接获取，支持周末回退）"""
        try:
            # 确定交易所
            if code.startswith('6'):
                ts_code = f"{code}.SH"
            else:
                ts_code = f"{code}.SZ"
            
            # 🔥 修复：获取最近交易日数据（回退最多 5 天）
            for i in range(5):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
                df = self.tushare_pro.daily(ts_code=ts_code, start_date=date, end_date=date)
                
                if df is not None and len(df) > 0:
                    row = df.iloc[0]
                    return {
                        'current_price': float(row.get('close', 0)),
                        'change_percent': float(row.get('pct_chg', 0)),
                        'open': float(row.get('open', 0)),
                        'high': float(row.get('high', 0)),
                        'low': float(row.get('low', 0)),
                        'pre_close': float(row.get('pre_close', 0))
                    }
            
            # 5 天内都无数据
            print(f"[Tushare] {code} 最近 5 天无交易数据")
            
        except Exception as e:
            print(f"[Tushare] 获取 {code} 失败：{e}")
        
        # 🔥 尝试从缓存获取
        cached_data = self._get_cached_price(code)
        if cached_data:
            return cached_data
        
        # 降级：返回空数据
        return {'current_price': 0, 'change_percent': 0}
    
    def _get_cached_price(self, code: str) -> dict:
        """从缓存获取股价（如果有）"""
        # 尝试从 stock-agent 的缓存读取
        cache_file = Path(f'/home/admin/.openclaw/workspace/data/stock-agent/cache/tushare/daily_{code}.json')
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {
                    'current_price': data.get('close', 0),
                    'change_percent': data.get('pct_chg', 0)
                }
            except:
                pass
        return None'''
    
    if old_method in content:
        content = content.replace(old_method, new_method)
        
        # 保存
        with open(monitor_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 修复完成：{monitor_file}")
        return True
    else:
        print(f"⚠️ 未找到目标代码，可能已修改")
        return False

if __name__ == '__main__':
    fix_monitor_py()
