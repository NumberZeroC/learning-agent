#!/usr/bin/env python3
"""
Stock-Agent 实时交易监控启动脚本

交易时间持续运行，监控股票，实时操作
"""
import sys
import argparse
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from stock_agent import Account, Config, RealTimeMonitor, TushareSource


def main():
    parser = argparse.ArgumentParser(description='Stock-Agent 实时交易监控')
    parser.add_argument('--interval', '-i', type=int, default=60, help='监控间隔（秒）')
    parser.add_argument('--config', '-c', type=str, default='config.yaml', help='配置文件')
    parser.add_argument('--watchlist', '-w', type=str, help='监控股票列表文件')
    parser.add_argument('--initial-capital', type=float, help='初始资金')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("📈 Stock-Agent 实时交易监控")
    print("=" * 60)
    print()
    
    # 加载配置
    config = Config(args.config)
    
    # 创建账户
    initial_capital = args.initial_capital or config.initial_capital
    account = Account(
        initial_capital=initial_capital,
        commission_rate=config.commission_rate,
        stamp_duty=config.stamp_duty
    )
    print(f"✅ 账户创建成功")
    print(f"   初始资金：¥{account.initial_capital:,.2f}")
    print()
    
    # 初始化 Tushare
    ts = None
    try:
        tushare_token = config.get('tushare.token', '')
        if not tushare_token:
            import os
            tushare_token = os.getenv('TUSHARE_TOKEN', '')
        
        if tushare_token:
            ts = TushareSource(token=tushare_token)
            print(f"✅ Tushare Pro 已连接")
        else:
            print(f"⚠️ Tushare Token 未配置")
    except Exception as e:
        print(f"⚠️ Tushare 初始化失败：{e}")
    print()
    
    # 创建监控器
    monitor = RealTimeMonitor(account, config, ts)
    
    # 显示监控股票
    print(f"📊 监控股票池:")
    for stock in monitor.watchlist:
        print(f"   {stock['name']} ({stock['code']})")
    print()
    
    # 启动监控
    print(f"🚀 启动实时监控...")
    print(f"   监控间隔：{args.interval}秒")
    print(f"   按 Ctrl+C 停止监控")
    print()
    
    # 运行
    monitor.start(interval=args.interval)


if __name__ == '__main__':
    main()
