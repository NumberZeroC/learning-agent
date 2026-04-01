"""
实时交易监控模块 - 交易时间持续运行

功能：
- 交易时间自动运行
- 实时监控股票池
- 自动执行买卖操作
- 记录操作日志
- 实时收益统计
"""
import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import threading

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from stock_agent import Account, Config, StateManager, TushareSource
from stock_agent.account import Order, Trade


class TradingLogger:
    """交易日志记录器"""
    
    def __init__(self, log_dir: str = None):
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = Path(__file__).parent.parent / 'data' / 'logs'
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.log_file = self.log_dir / f'trading_{self.today}.log'
        self.trade_file = self.log_dir / f'trades_{self.today}.json'
        
        # 加载历史交易记录
        self.trades_history = self._load_trades()
    
    def _load_trades(self) -> List[Dict]:
        """加载历史交易"""
        if self.trade_file.exists():
            with open(self.trade_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save_trades(self):
        """保存交易记录"""
        with open(self.trade_file, 'w', encoding='utf-8') as f:
            json.dump(self.trades_history, f, ensure_ascii=False, indent=2)
    
    def log(self, message: str, level: str = 'INFO'):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        # 写入文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
        
        # 打印到控制台
        print(log_entry)
    
    def log_order(self, order: Order, status: str = 'submitted'):
        """记录订单"""
        self.trades_history.append({
            'type': 'order',
            'timestamp': datetime.now().isoformat(),
            'order_id': order.order_id,
            'stock_code': order.stock_code,
            'stock_name': order.stock_name,
            'side': order.side,
            'volume': order.volume,
            'price': order.price,
            'status': status
        })
        self._save_trades()
        self.log(f"订单 {order.order_id}: {order.side} {order.stock_name} {order.volume}股 @¥{order.price:.2f}")
    
    def log_trade(self, trade: Trade):
        """记录成交"""
        self.trades_history.append({
            'type': 'trade',
            'timestamp': datetime.now().isoformat(),
            'stock_code': trade.stock_code,
            'stock_name': trade.stock_name,
            'side': trade.side,
            'volume': trade.volume,
            'price': trade.price,
            'amount': trade.amount,
            'commission': trade.commission,
            'stamp_duty': trade.stamp_duty
        })
        self._save_trades()
        self.log(f"成交：{trade.side} {trade.stock_name} {trade.volume}股 @¥{trade.price:.2f} 金额¥{trade.amount:.2f}")
    
    def log_performance(self, account: Account):
        """记录收益"""
        summary = account.get_summary()
        self.log(f"收益统计：总资产¥{summary['total_value']:,.2f} 收益¥{summary['total_return']:,.2f} 收益率{summary['return_rate']:+.2%}")
    
    def get_today_trades(self) -> List[Dict]:
        """获取今日交易"""
        today = datetime.now().strftime('%Y-%m-%d')
        return [t for t in self.trades_history if t['timestamp'].startswith(today)]
    
    def get_summary(self) -> Dict:
        """获取交易统计"""
        today_trades = self.get_today_trades()
        buy_count = sum(1 for t in today_trades if t.get('side') == 'BUY')
        sell_count = sum(1 for t in today_trades if t.get('side') == 'SELL')
        
        return {
            'date': today,
            'total_trades': len(today_trades),
            'buy_count': buy_count,
            'sell_count': sell_count,
            'log_file': str(self.log_file),
            'trade_file': str(self.trade_file)
        }


class RealTimeMonitor:
    """实时监控器"""
    
    def __init__(self, account: Account, config: Config, ts: TushareSource):
        self.account = account
        self.config = config
        self.ts = ts
        self.logger = TradingLogger(config.get('output.log_dir'))
        
        # 监控股票池
        self.watchlist = self._load_watchlist()
        
        # 运行状态
        self.is_running = False
        self.last_update = None
        
        # 收益记录
        self.peak_value = account.initial_capital
        self.daily_start_value = account.initial_capital
        
        # 性能统计
        self.stats = {
            'total_trades': 0,
            'profitable_trades': 0,
            'losing_trades': 0,
            'total_profit': 0,
            'total_loss': 0
        }
    
    def _load_watchlist(self) -> List[Dict]:
        """加载监控股票池"""
        # 从配置读取
        monitor_stocks = self.config.get('monitor_stocks.stocks', [])
        
        if monitor_stocks:
            watchlist = []
            for stock in monitor_stocks:
                # 补充完整代码
                code = stock['code']
                if code.startswith('6'):
                    ts_code = f"{code}.SH"
                else:
                    ts_code = f"{code}.SZ"
                
                watchlist.append({
                    'code': code,
                    'ts_code': ts_code,
                    'name': stock.get('name', '')
                })
            
            self.logger.log(f"加载监控股票池：{len(watchlist)}只")
            return watchlist
        
        # 默认监控股票
        default_watchlist = [
            {'code': '600519', 'ts_code': '600519.SH', 'name': '贵州茅台'},
            {'code': '000858', 'ts_code': '000858.SZ', 'name': '五粮液'},
            {'code': '300750', 'ts_code': '300750.SZ', 'name': '宁德时代'},
            {'code': '002594', 'ts_code': '002594.SZ', 'name': '比亚迪'},
            {'code': '601318', 'ts_code': '601318.SH', 'name': '中国平安'},
        ]
        
        self.logger.log(f"使用默认监控股票池：{len(default_watchlist)}只")
        return default_watchlist
    
    def is_trading_time(self) -> bool:
        """判断是否在交易时间"""
        now = datetime.now()
        
        # 只在工作日运行
        if now.weekday() >= 5:  # 周六=5, 周日=6
            return False
        
        # 转换为分钟数
        current_minutes = now.hour * 60 + now.minute
        
        morning_start = 9 * 60 + 15   # 9:15
        morning_end = 11 * 60 + 30    # 11:30
        afternoon_start = 13 * 60     # 13:00
        afternoon_end = 15 * 60       # 15:00
        
        return (morning_start <= current_minutes <= morning_end or 
                afternoon_start <= current_minutes <= afternoon_end)
    
    def update_prices(self) -> Dict[str, float]:
        """更新股票价格"""
        prices = {}
        today = datetime.now().strftime('%Y%m%d')
        
        for stock in self.watchlist:
            try:
                # 1. 先尝试获取今日数据
                daily = self.ts.get_daily(stock['ts_code'], today)
                
                # 2. 如果今日无数据（盘中），使用昨日数据
                if not daily:
                    # 计算昨日日期（跳过周末）
                    from datetime import timedelta
                    yesterday = datetime.now() - timedelta(days=1)
                    # 如果是周一，回溯到周五
                    if yesterday.weekday() == 5:  # 周六
                        yesterday -= timedelta(days=1)
                    elif yesterday.weekday() == 6:  # 周日
                        yesterday -= timedelta(days=2)
                    
                    yesterday_str = yesterday.strftime('%Y%m%d')
                    daily = self.ts.get_daily(stock['ts_code'], yesterday_str)
                    
                    if daily:
                        self.logger.log(f"使用昨日数据：{stock['name']} ¥{daily['close']:.2f}", 'DEBUG')
                
                if daily:
                    prices[stock['code']] = daily['close']
                    
            except Exception as e:
                self.logger.log(f"获取 {stock['name']} 价格失败：{e}", 'WARNING')
        
        # 更新账户持仓价格
        if prices:
            self.account.update_prices(prices)
            self.last_update = datetime.now()
        
        return prices
    
    def check_trading_signals(self) -> List[Dict]:
        """检查交易信号"""
        signals = []
        
        for stock in self.watchlist:
            code = stock['code']
            
            # 获取持仓
            position = self.account.get_position(code)
            
            # 获取最新价格
            prices = self.update_prices()
            current_price = prices.get(code, 0)
            
            if current_price == 0:
                continue
            
            # 检查止损
            if position:
                cost = position.avg_cost
                loss_pct = (current_price - cost) / cost
                
                # 止损检查（-8%）
                if loss_pct < -0.08:
                    signals.append({
                        'code': code,
                        'name': stock['name'],
                        'action': 'SELL',
                        'reason': f'止损：{loss_pct:.1%}',
                        'volume': position.volume,
                        'priority': 1  # 高优先级
                    })
                    self.logger.log(f"⚠️ 止损信号：{stock['name']} {loss_pct:.1%}")
                
                # 止盈检查（+20%）
                elif loss_pct > 0.20:
                    signals.append({
                        'code': code,
                        'name': stock['name'],
                        'action': 'SELL',
                        'reason': f'止盈：{loss_pct:.1%}',
                        'volume': position.volume // 2,  # 卖出一半
                        'priority': 2
                    })
                    self.logger.log(f"✅ 止盈信号：{stock['name']} {loss_pct:.1%}")
            
            # 检查买入信号
            else:
                # 买入策略：如果现金充足且无持仓，考虑建仓
                if self.account.cash > self.account.initial_capital * 0.2:  # 现金>20%
                    # 简单策略：每只股票配置 10% 资金
                    position_value = self.account.initial_capital * 0.10
                    volume = int(position_value / current_price / 100) * 100  # 100 股整数倍
                    
                    if volume >= 100:  # 至少 100 股
                        signals.append({
                            'code': code,
                            'name': stock['name'],
                            'action': 'BUY',
                            'reason': f'建仓：配置 10% 仓位',
                            'volume': volume,
                            'price': current_price,
                            'priority': 3
                        })
                        self.logger.log(f"📈 买入信号：{stock['name']} {volume}股 @¥{current_price:.2f}")
        
        # 按优先级排序
        signals.sort(key=lambda x: x.get('priority', 99))
        
        return signals
    
    def execute_signals(self, signals: List[Dict]):
        """执行交易信号"""
        for signal in signals:
            if signal['action'] == 'SELL':
                # 执行卖出
                position = self.account.get_position(signal['code'])
                if position:
                    order = self.account.sell(
                        stock_code=signal['code'],
                        volume=signal['volume'],
                        price=position.current_price
                    )
                    
                    if order:
                        self.logger.log_order(order)
                        self.stats['total_trades'] += 1
            
            elif signal['action'] == 'BUY':
                # 执行买入
                price = signal.get('price', 0)
                if price <= 0:
                    prices = self.update_prices()
                    price = prices.get(signal['code'], 0)
                
                if price > 0:
                    order = self.account.buy(
                        stock_code=signal['code'],
                        stock_name=signal['name'],
                        volume=signal['volume'],
                        price=price
                    )
                    
                    if order:
                        self.logger.log_order(order)
                        self.stats['total_trades'] += 1
    
    def calculate_performance(self) -> Dict:
        """计算 performance"""
        summary = self.account.get_summary()
        
        # 日内收益
        daily_return = (self.account.total_value - self.daily_start_value) / self.daily_start_value
        
        # 最大回撤
        if self.account.total_value > self.peak_value:
            self.peak_value = self.account.total_value
        
        drawdown = (self.peak_value - self.account.total_value) / self.peak_value
        
        performance = {
            'timestamp': datetime.now().isoformat(),
            'total_value': self.account.total_value,
            'cash': self.account.cash,
            'market_value': self.account.market_value,
            'daily_return': daily_return,
            'total_return': summary['return_rate'],
            'peak_value': self.peak_value,
            'max_drawdown': drawdown,
            'position_count': self.account.position_count,
            'position_ratio': self.account.position_ratio
        }
        
        return performance
    
    def run_monitoring_cycle(self):
        """运行一轮监控"""
        self.logger.log("=" * 60)
        self.logger.log("开始监控循环")
        
        # 1. 更新价格
        self.logger.log("更新股票价格...")
        prices = self.update_prices()
        
        # 2. 检查交易信号
        self.logger.log("检查交易信号...")
        signals = self.check_trading_signals()
        
        if signals:
            self.logger.log(f"发现 {len(signals)} 个交易信号")
            # 3. 执行信号
            self.execute_signals(signals)
        else:
            self.logger.log("无交易信号")
        
        # 4. 记录收益
        performance = self.calculate_performance()
        self.logger.log_performance(self.account)
        
        # 5. 保存状态
        self.logger.log(f"持仓数量：{self.account.position_count}, 仓位：{self.account.position_ratio:.1%}")
        self.logger.log("=" * 60)
    
    def start(self, interval: int = 60):
        """启动监控"""
        self.logger.log("🚀 实时监控系统启动")
        self.logger.log(f"监控间隔：{interval}秒")
        self.logger.log(f"监控股票：{len(self.watchlist)}只")
        self.is_running = True
        
        # 记录日内起始值
        self.daily_start_value = self.account.total_value
        
        try:
            while self.is_running:
                # 检查是否交易时间
                if self.is_trading_time():
                    self.run_monitoring_cycle()
                else:
                    # 非交易时间，每小时检查一次
                    self.logger.log("⏰ 非交易时间，休眠中...")
                    time.sleep(3600)
                    continue
                
                # 休眠
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.logger.log("⛔ 用户中断，停止监控")
            self.stop()
        except Exception as e:
            self.logger.log(f"❌ 监控异常：{e}", 'ERROR')
            self.stop()
    
    def stop(self):
        """停止监控"""
        self.is_running = False
        self.logger.log("✅ 监控系统已停止")
        
        # 输出总结
        summary = self.logger.get_summary()
        self.logger.log(f"\n📊 今日交易总结")
        self.logger.log(f"交易次数：{summary['total_trades']}")
        self.logger.log(f"买入：{summary['buy_count']}, 卖出：{summary['sell_count']}")
        self.logger.log(f"日志文件：{summary['log_file']}")
        self.logger.log(f"交易记录：{summary['trade_file']}")


def main():
    """主函数"""
    print("=" * 60)
    print("📈 Stock-Agent 实时交易监控")
    print("=" * 60)
    
    # 加载配置
    config = Config()
    
    # 创建账户
    account = Account(
        initial_capital=config.initial_capital,
        commission_rate=config.commission_rate,
        stamp_duty=config.stamp_duty
    )
    print(f"✅ 账户创建成功，初始资金：¥{account.initial_capital:,.2f}")
    
    # 初始化 Tushare
    try:
        tushare_token = config.get('tushare.token', '')
        if not tushare_token:
            import os
            tushare_token = os.getenv('TUSHARE_TOKEN', '')
        
        ts = TushareSource(token=tushare_token)
        print(f"✅ Tushare Pro 已连接")
    except Exception as e:
        print(f"⚠️ Tushare 初始化失败：{e}")
        ts = None
    
    # 创建监控器
    monitor = RealTimeMonitor(account, config, ts)
    
    # 启动监控
    print(f"\n🚀 启动实时监控...")
    print(f"监控间隔：60 秒")
    print(f"按 Ctrl+C 停止监控")
    print()
    
    # 运行
    monitor.start(interval=60)


if __name__ == '__main__':
    main()
