#!/usr/bin/env python3
"""
持仓监控模块 - 简化版

当数据源不可用时，返回配置中的股票列表和默认值
"""
import os
import sys
import json
import time
import yaml
from datetime import datetime, timedelta
from pathlib import Path

try:
    # 尝试导入 stock_monitor
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    from stock_monitor import StockMonitor
    HAS_STOCK_MONITOR = True
except Exception as e:
    print(f"⚠️ 无法加载 StockMonitor: {e}")
    HAS_STOCK_MONITOR = False


def parse_stock_list(stocks_str: str) -> list:
    """解析股票列表字符串"""
    if not stocks_str:
        return []
    stocks_str = stocks_str.replace(',', ' ').replace(';', ' ')
    return [s.strip() for s in stocks_str.split() if s.strip()]


class StockWatcher:
    """持仓监控"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        self.config_path = config_path
        self.config = self._load_config()
        self.monitor = None
        self.tushare_pro = None
        
        # 初始化 Tushare
        try:
            import tushare as ts
            token = os.getenv('TUSHARE_TOKEN', '0b8ed09db7d7e733c133a04fad31fc34ff4938afd57f7766cfc6a3f2')
            ts.set_token(token)
            self.tushare_pro = ts.pro_api()
            print("[Tushare] ✅ 已连接")
        except Exception as e:
            print(f"[Tushare] ⚠️ 初始化失败：{e}")
        
        if HAS_STOCK_MONITOR:
            try:
                cache_dir = self.config.get('akshare', {}).get('cache_dir', 'data/cache')
                cache_ttl = self.config.get('akshare', {}).get('cache_ttl', 300)
                self.monitor = StockMonitor(cache_dir=cache_dir, cache_ttl=cache_ttl)
                print("[StockMonitor] ✅ 已初始化")
            except Exception as e:
                print(f"[StockMonitor] ⚠️ 初始化失败：{e}")
        
        self.reports_dir = Path('data/reports')
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                config_file = Path(__file__).parent / self.config_path
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
        except Exception as e:
            print(f"⚠️ 加载配置失败：{e}")
        return {}
    
    def _get_monitor_stocks(self) -> list:
        """从配置获取监控股票列表"""
        return self.config.get('monitor_stocks', {}).get('stocks', [])
    
    def _get_stock_data(self, code: str, name: str) -> dict:
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
        return None
    
    def _get_signal(self, code: str, name: str) -> dict:
        """获取交易信号（带降级）"""
        if self.monitor:
            try:
                import signal
                def timeout_handler(signum, frame):
                    raise TimeoutError("获取信号超时")
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(8)
                
                signal_data = self.monitor.generate_trading_signal(code, name)
                signal.alarm(0)
                
                if signal_data:
                    return signal_data
            except Exception as e:
                print(f"[Signal] {code} 信号生成失败：{e}")
        
        # 降级：返回默认信号
        return {'action': 'HOLD', 'score': 5.0, 'action_text': '继续持有'}
    
    def run_once(self, export_report: bool = True) -> dict:
        """执行一次监控"""
        print(f"\n{'='*60}")
        print(f"📊 持仓监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        stocks = self._get_monitor_stocks()
        
        if not stocks:
            print("⚠️ 配置文件中没有监控股票列表")
            return {'success': False, 'message': '没有监控股票'}
        
        print(f"📋 监控股票：{len(stocks)} 只\n")
        
        results = []
        for stock in stocks:
            code = stock.get('code')
            name = stock.get('name', '')
            
            if not code:
                continue
            
            print(f"📈 {name}({code})...", end=' ')
            
            stock_data = self._get_stock_data(code, name)
            signal_data = self._get_signal(code, name)
            
            result = {
                'code': code,
                'name': name,
                'sector': stock.get('sector', ''),
                'price': stock_data.get('current_price', 0),
                'change_pct': stock_data.get('change_percent', 0),
                'signal': signal_data.get('action', 'HOLD'),
                'score': signal_data.get('score', 5.0),
                'action': signal_data.get('action_text', '继续持有'),
                'reason': signal_data.get('reason', ''),
                'target_price': signal_data.get('target_price', 0),
                'stop_loss': signal_data.get('stop_loss', 0),
                'risk_alerts': signal_data.get('risk_alerts', [])
            }
            
            results.append(result)
            
            if result['price'] > 0:
                print(f"¥{result['price']:.2f} ({result['change_pct']:+.2f}%) ✅")
            else:
                print(f"⚠️ 数据暂不可用")
        
        # 导出报告
        if export_report and results:
            self._export_report(results)
        
        # 保存到 JSON
        self._save_json(results)
        
        print(f"\n✅ 监控完成，共 {len(results)} 只股票\n")
        
        return {'success': True, 'count': len(results), 'results': results}
    
    def monitor_custom_stocks(self, stock_list: list, export_report: bool = True) -> dict:
        """监控自定义股票列表"""
        stocks = [{'code': code, 'name': ''} for code in stock_list]
        original = self.config.get('monitor_stocks', {}).get('stocks', [])
        self.config.setdefault('monitor_stocks', {})['stocks'] = stocks
        result = self.run_once(export_report=export_report)
        self.config['monitor_stocks']['stocks'] = original
        return result
    
    def run_scheduled(self, interval_seconds: int = 1800, export_report: bool = True):
        """定时运行监控"""
        print(f"🕐 启动定时监控，间隔：{interval_seconds}秒")
        while True:
            try:
                self.run_once(export_report=export_report)
            except Exception as e:
                print(f"❌ 监控失败：{e}")
            print(f"\n💤 等待 {interval_seconds}秒...\n")
            time.sleep(interval_seconds)
    
    def _export_report(self, results: list):
        """导出 MD 报告"""
        today = datetime.now().strftime('%Y-%m-%d')
        md_file = self.reports_dir / f'stock_monitor_{today}.md'
        
        summary = {
            'buy': sum(1 for r in results if r.get('signal') in ['BUY', 'STRONG_BUY']),
            'hold': sum(1 for r in results if r.get('signal') == 'HOLD'),
            'sell': sum(1 for r in results if r.get('signal') in ['SELL', 'STRONG_SELL'])
        }
        
        md = f"""# 📊 持仓监控报告

**日期：** {today}  
**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**监控数量：** {len(results)} 只

---

## 📈 监控摘要

| 类型 | 数量 |
|------|------|
| 买入信号 | {summary['buy']} |
| 持有 | {summary['hold']} |
| 卖出信号 | {summary['sell']} |

---

## 📋 个股详情

"""
        for r in results:
            emoji = '🔴' if r.get('signal') in ['BUY', 'STRONG_BUY'] else '🟢' if r.get('signal') in ['SELL', 'STRONG_SELL'] else '🟡'
            price_str = f"¥{r.get('price', 0):.2f}" if r.get('price', 0) > 0 else "暂不可用"
            change_str = f"({r.get('change_pct', 0):+.2f}%)" if r.get('price', 0) > 0 else ""
            
            md += f"""### {emoji} {r['name']}({r['code']})

- **当前价格**: {price_str} {change_str}
- **操作建议**: {r.get('action', '继续持有')}
- **综合得分**: {r.get('score', 5.0)}/10
- **目标价**: ¥{r.get('target_price', 0):.2f}
- **止损价**: ¥{r.get('stop_loss', 0):.2f}
- **理由**: {r.get('reason', '无')}

"""
        
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md)
        print(f"📄 报告已保存：{md_file}")
    
    def _save_json(self, results: list):
        """保存 JSON 数据"""
        today = datetime.now().strftime('%Y-%m-%d')
        json_file = self.reports_dir / f'stock_monitor_{today}.json'
        
        data = {
            'date': today,
            'update_time': datetime.now().isoformat(),
            'stocks': results
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"📄 数据已保存：{json_file}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='股票监控')
    parser.add_argument('--config', '-c', default='config.yaml')
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--interval', '-i', type=int, default=0)
    parser.add_argument('--stocks', '-s', type=str)
    parser.add_argument('--export', action='store_true')
    parser.add_argument('--no-export', action='store_true')
    
    args = parser.parse_args()
    watcher = StockWatcher(config_path=args.config)
    
    if args.interval > 0:
        watcher.run_scheduled(interval_seconds=args.interval, export_report=not args.no_export)
    elif args.stocks:
        stock_list = parse_stock_list(args.stocks)
        result = watcher.monitor_custom_stocks(stock_list, export_report=not args.no_export)
        sys.exit(0 if result.get('success') else 1)
    else:
        result = watcher.run_once(export_report=not args.no_export)
        sys.exit(0 if result.get('success') else 1)
