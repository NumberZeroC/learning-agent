#!/usr/bin/env python3
"""
Stock-Agent - 智能量化模拟交易系统

主程序入口
数据源：Tushare Pro（主）+ AKShare（备用）
"""
import sys
import argparse
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from stock_agent import Account, Config, StateManager, TushareSource, AKShareSource


def print_welcome():
    """打印欢迎信息"""
    print("=" * 60)
    print("📈 Stock-Agent - 智能量化模拟交易系统")
    print("=" * 60)
    print()


def print_account_summary(account: Account):
    """打印账户概览"""
    summary = account.get_summary()
    print("\n📊 账户概览")
    print("-" * 40)
    print(f"初始资金：   ¥{summary['initial_capital']:,.2f}")
    print(f"可用资金：   ¥{summary['cash']:,.2f}")
    print(f"持仓市值：   ¥{summary['market_value']:,.2f}")
    print(f"总资产：     ¥{summary['total_value']:,.2f}")
    print(f"总收益：     ¥{summary['total_return']:,.2f}")
    print(f"收益率：     {summary['return_rate']:+.2%}")
    print(f"仓位：       {summary['position_ratio']:.1%}")
    print(f"持仓数量：   {summary['position_count']}")
    print()


def print_positions(account: Account):
    """打印持仓"""
    positions = account.get_positions()
    if not positions:
        print("\n💼 当前无持仓")
        return
    
    print("\n💼 持仓明细")
    print("-" * 70)
    print(f"{'代码':<10} {'名称':<10} {'数量':>8} {'成本':>10} {'现价':>10} {'收益':>10}")
    print("-" * 70)
    
    for pos in positions:
        print(f"{pos.stock_code:<10} {pos.stock_name:<10} {pos.volume:>8} "
              f"¥{pos.avg_cost:>9.2f} ¥{pos.current_price:>9.2f} "
              f"{pos.profit_rate:>9.2%}")
    
    print()


def run_demo():
    """运行演示"""
    print_welcome()
    
    # 创建配置
    config = Config()
    
    # 创建账户
    print("📝 创建模拟账户...")
    account = Account(
        initial_capital=config.initial_capital,
        commission_rate=config.commission_rate,
        stamp_duty=config.stamp_duty
    )
    print(f"✅ 账户创建成功，初始资金：¥{account.initial_capital:,.2f}")
    
    # 创建状态管理器
    state = StateManager(account)
    
    # 初始化 Tushare 数据源
    print("\n📊 初始化数据源...")
    try:
        tushare_token = config.get('tushare.token', '')
        if not tushare_token:
            import os
            tushare_token = os.getenv('TUSHARE_TOKEN', '')
        
        if tushare_token:
            ts = TushareSource(token=tushare_token)
            print(f"✅ Tushare Pro 已连接")
            
            # 获取主要指数
            print("\n📈 获取主要指数...")
            indices = ts.get_major_indices()
            for name, data in indices.items():
                print(f"  {name}: {data['close']:.2f} ({data['pct_chg']:+.2f}%)")
        else:
            print("⚠️ Tushare Token 未配置，使用模拟数据")
    except Exception as e:
        print(f"⚠️ Tushare 初始化失败：{e}")
    
    # 模拟交易
    print("\n🔄 模拟交易...")
    
    # 买入示例
    account.buy('600519', '贵州茅台', 100, 1800.00)
    account.buy('000858', '五粮液', 200, 150.00)
    account.buy('300750', '宁德时代', 150, 200.00)
    
    # 更新价格（模拟）
    prices = {
        '600519': 1850.00,
        '000858': 155.00,
        '300750': 210.00,
    }
    account.update_prices(prices)
    
    # 打印账户
    print_account_summary(account)
    print_positions(account)
    
    # 卖出示例
    account.sell('000858', 100, 155.00)
    
    # 再次打印
    print_account_summary(account)
    print_positions(account)
    
    # 保存状态
    state.save_state()
    
    print("=" * 60)
    print("✅ 演示完成")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Stock-Agent 智能量化模拟交易系统')
    parser.add_argument('--demo', action='store_true', help='运行演示')
    parser.add_argument('--query', type=str, help='查询信息 (positions|summary|trades)')
    parser.add_argument('--config', type=str, default='config.yaml', help='配置文件路径')
    
    args = parser.parse_args()
    
    if args.demo:
        run_demo()
    elif args.query:
        # 查询模式
        config = Config(args.config)
        account = Account(initial_capital=config.initial_capital)
        
        if args.query == 'positions':
            print_positions(account)
        elif args.query == 'summary':
            print_account_summary(account)
        else:
            print(f"未知查询类型：{args.query}")
    else:
        # 默认运行演示
        run_demo()


if __name__ == '__main__':
    main()
