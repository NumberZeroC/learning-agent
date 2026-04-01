#!/usr/bin/env python3
"""
Stock-Agent 自动化交易主程序

功能：
- 自动选股（多因子量化）
- 自动交易（风控 + 执行）
- 实时监控（止损止盈）
- 日志记录

使用：
    python auto_trade.py --mode full      # 完整流程（选股 + 交易）
    python auto_trade.py --mode screen    # 仅选股
    python auto_trade.py --mode trade     # 仅交易
    python auto_trade.py --mode monitor   # 监控持仓
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from stock_agent import Account, Config, TushareSource, AKShareSource
from stock_agent.stock_screener import StockScreener
from stock_agent.trade_executor import TradeExecutor


def is_trading_time() -> bool:
    """判断是否交易时间"""
    now = datetime.now()
    
    # 非交易日
    if now.weekday() >= 5:
        return False
    
    # 交易时段
    current = now.hour * 60 + now.minute
    morning = 9*60+15 <= current <= 11*60+30
    afternoon = 13*60 <= current <= 15*60
    
    return morning or afternoon


def run_screening(config: Config, strategy: str, top_n: int) -> list:
    """执行选股"""
    print("\n" + "=" * 70)
    print("📈 第一步：自动选股")
    print("=" * 70)
    
    # 初始化数据源
    ts_token = config.get('tushare.token', '')
    ts = TushareSource(token=ts_token, cache_ttl=600)
    
    try:
        ak = AKShareSource(cache_ttl=300)
    except ImportError:
        print("⚠️ AKShare 未安装")
        ak = None
    
    # 创建筛选器
    screener = StockScreener(ts, ak, config.get('stock_selection', {}))
    
    # 执行选股
    recommendations = screener.screen(strategy=strategy, top_n=top_n)
    
    # 保存结果
    if recommendations:
        result_file = Path(__file__).parent / 'data' / f'selection_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        result_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(recommendations, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📄 结果已保存：{result_file}")
        
        return recommendations, str(result_file)
    
    return [], None


def run_trading(config: Config, recommendations: list, strategy: str) -> dict:
    """执行交易"""
    print("\n" + "=" * 70)
    print("💰 第二步：自动交易")
    print("=" * 70)
    
    # 创建账户
    account = Account(
        initial_capital=config.initial_capital,
        commission_rate=config.commission_rate,
        stamp_duty=config.stamp_duty
    )
    
    # 创建执行器
    executor = TradeExecutor(account, config.get('risk_limits', {}))
    
    # 执行推荐
    results = executor.execute_recommendations(recommendations, strategy)
    
    # 保存交易记录
    if results['orders']:
        trade_file = Path(__file__).parent / 'data' / f'trades_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        trade_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(trade_file, 'w', encoding='utf-8') as f:
            json.dump({
                'date': datetime.now().isoformat(),
                'strategy': strategy,
                'results': results,
                'account_summary': account.get_summary()
            }, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📄 交易记录已保存：{trade_file}")
    
    return results


def run_monitoring(config: Config, interval: int = 60):
    """监控持仓（止损止盈）"""
    print("\n" + "=" * 70)
    print("👁️  实时监控持仓")
    print("=" * 70)
    
    # 创建账户
    account = Account(
        initial_capital=config.initial_capital,
        commission_rate=config.commission_rate,
        stamp_duty=config.stamp_duty
    )
    
    # 创建执行器
    executor = TradeExecutor(account, config.get('risk_limits', {}))
    
    print(f"监控间隔：{interval}秒")
    print("按 Ctrl+C 停止监控\n")
    
    try:
        while True:
            if is_trading_time():
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 检查风控...")
                
                # 检查止损
                stop_orders = executor.check_stop_loss()
                if stop_orders:
                    print(f"  ⚠️  止损：{len(stop_orders)}个订单")
                
                # 检查止盈
                profit_orders = executor.check_take_profit()
                if profit_orders:
                    print(f"  ✅ 止盈：{len(profit_orders)}个订单")
                
                # 无操作
                if not stop_orders and not profit_orders:
                    print(f"  ✓ 无需操作")
                
                # 打印账户状态
                summary = account.get_summary()
                print(f"  总资产：¥{summary['total_value']:,.2f}  收益率：{summary['return_rate']:+.2%}")
                
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 非交易时间...")
            
            # 休眠
            import time
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\n⛔ 用户中断，停止监控")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Stock-Agent 自动化交易')
    parser.add_argument('--mode', '-m', default='full',
                       choices=['full', 'screen', 'trade', 'monitor'],
                       help='运行模式')
    parser.add_argument('--strategy', '-s', default='balanced',
                       choices=['balanced', 'value', 'momentum', 'capital'],
                       help='选股策略')
    parser.add_argument('--top', '-t', type=int, default=10, help='推荐数量')
    parser.add_argument('--config', '-c', default='config.yaml', help='配置文件')
    parser.add_argument('--interval', '-i', type=int, default=60, help='监控间隔（秒）')
    parser.add_argument('--recommendations', '-r', type=str, help='推荐文件（交易模式）')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🤖 Stock-Agent 自动化交易系统")
    print("=" * 70)
    print(f"模式：{args.mode}")
    print(f"策略：{args.strategy}")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 加载配置
    config = Config(args.config)
    
    recommendations = []
    rec_file = None
    
    # 模式 1: 完整流程（选股 + 交易）
    if args.mode == 'full':
        # 选股
        recommendations, rec_file = run_screening(config, args.strategy, args.top)
        
        if not recommendations:
            print("\n⚠️  无推荐股票，跳过交易")
            return
        
        # 交易
        results = run_trading(config, recommendations, args.strategy)
        
        # 总结
        print("\n" + "=" * 70)
        print("✅ 自动化交易完成")
        print("=" * 70)
        print(f"推荐：{len(recommendations)}只")
        print(f"成交：{results.get('success', 0)}只")
        print(f"金额：¥{results.get('total_amount', 0):,.2f}")
    
    # 模式 2: 仅选股
    elif args.mode == 'screen':
        run_screening(config, args.strategy, args.top)
    
    # 模式 3: 仅交易
    elif args.mode == 'trade':
        if args.recommendations:
            with open(args.recommendations, 'r', encoding='utf-8') as f:
                recommendations = json.load(f)
        else:
            print("❌ 请提供推荐文件 (--recommendations)")
            return
        
        run_trading(config, recommendations, args.strategy)
    
    # 模式 4: 监控持仓
    elif args.mode == 'monitor':
        run_monitoring(config, args.interval)


if __name__ == '__main__':
    main()
