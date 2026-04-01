#!/usr/bin/env python3
"""
Stock-Agent 回测入口脚本

用法:
    python run_backtest.py --strategy momentum --start 2025-01-01 --end 2026-03-29
    python run_backtest.py --strategy value --top-n 20
    python run_backtest.py --config backtest_config.yaml
"""
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from stock_agent import Config, TushareSource
from backtest import Backtester
from strategies import MomentumStrategy, ValueStrategy


def load_config(config_file: str) -> dict:
    """加载配置文件"""
    config_path = Path(config_file)
    
    if not config_path.exists():
        print(f"⚠️ 配置文件不存在：{config_file}")
        return {}
    
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except ImportError:
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)


def run_backtest(
    strategy_name: str,
    start_date: str,
    end_date: str,
    initial_capital: float = 1000000,
    strategy_params: dict = None,
    output_dir: str = 'reports'
):
    """
    运行回测
    
    Args:
        strategy_name: 策略名称 (momentum | value)
        start_date: 开始日期
        end_date: 结束日期
        initial_capital: 初始资金
        strategy_params: 策略参数
        output_dir: 输出目录
    """
    print("\n" + "=" * 70)
    print("📈 Stock-Agent 回测系统")
    print("=" * 70)
    print(f"策略：{strategy_name}")
    print(f"区间：{start_date} ~ {end_date}")
    print(f"资金：¥{initial_capital:,.0f}")
    print("=" * 70 + "\n")
    
    # 1. 加载配置
    config = Config()
    ts_token = config.get('tushare.token', '')
    
    if not ts_token:
        print("⚠️ 未配置 Tushare Token，使用 AKShare")
        data_source = None
    else:
        print("✅ 使用 Tushare Pro 数据源")
        data_source = TushareSource(token=ts_token, cache_ttl=3600)
    
    # 2. 创建策略
    strategy_params = strategy_params or {}
    
    if strategy_name == 'momentum':
        strategy = MomentumStrategy(strategy_params)
    elif strategy_name == 'value':
        strategy = ValueStrategy(strategy_params)
    else:
        print(f"❌ 未知策略：{strategy_name}")
        print("可用策略：momentum, value")
        return None
    
    print(f"✅ 策略：{strategy.name()}")
    print(f"   参数：{strategy.params}\n")
    
    # 3. 创建回测器
    backtester = Backtester(
        strategy=strategy,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        commission_rate=0.0003,
        stamp_duty=0.001,
        data_source=data_source,
        benchmark_code='000001.SH',
        verbose=True
    )
    
    # 4. 准备数据
    print("📊 准备历史数据...")
    # 这里可以预先获取股票池
    stock_pool = None  # 可以从策略或配置获取
    
    if not backtester.prepare_data(stock_pool):
        print("❌ 数据准备失败")
        return None
    
    print("")
    
    # 5. 运行回测
    result = backtester.run()
    
    if not result:
        print("❌ 回测失败")
        return None
    
    # 6. 生成报告
    print("\n📝 生成报告...")
    
    from backtest.analyzer import PerformanceAnalyzer
    analyzer = PerformanceAnalyzer(result)
    
    # Markdown 报告
    md_report = analyzer.generate_report(format='markdown')
    
    # 保存报告
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = output_path / f"backtest_{strategy_name}_{timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(md_report)
    
    print(f"✅ 报告已保存：{report_file}")
    
    # JSON 结果
    json_file = output_path / f"backtest_{strategy_name}_{timestamp}.json"
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(result.to_dict(), f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✅ 结果已保存：{json_file}")
    
    # 7. 输出摘要
    print("\n" + "=" * 70)
    print("📊 回测摘要")
    print("=" * 70)
    print(result.summary())
    print("=" * 70 + "\n")
    
    return result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Stock-Agent 回测系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_backtest.py --strategy momentum --start 2025-01-01 --end 2026-03-29
  python run_backtest.py --strategy value --top-n 20 --holding-period 30
  python run_backtest.py --config backtest_config.yaml
        """
    )
    
    parser.add_argument(
        '--strategy',
        type=str,
        default='momentum',
        choices=['momentum', 'value'],
        help='策略名称 (默认：momentum)'
    )
    
    parser.add_argument(
        '--start',
        type=str,
        default='2025-01-01',
        help='开始日期 (默认：2025-01-01)'
    )
    
    parser.add_argument(
        '--end',
        type=str,
        default='2026-03-29',
        help='结束日期 (默认：2026-03-29)'
    )
    
    parser.add_argument(
        '--capital',
        type=float,
        default=1000000,
        help='初始资金 (默认：1000000)'
    )
    
    parser.add_argument(
        '--top-n',
        type=int,
        default=10,
        help='选股数量 (默认：10)'
    )
    
    parser.add_argument(
        '--lookback',
        type=int,
        default=20,
        help='动量回看天数 (默认：20)'
    )
    
    parser.add_argument(
        '--holding-period',
        type=int,
        default=5,
        help='持有天数 (默认：5)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='配置文件路径'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='reports',
        help='输出目录 (默认：reports)'
    )
    
    args = parser.parse_args()
    
    # 从配置文件加载
    if args.config:
        config = load_config(args.config)
        strategy_name = config.get('strategy', args.strategy)
        start_date = config.get('start_date', args.start)
        end_date = config.get('end_date', args.end)
        initial_capital = config.get('initial_capital', args.capital)
        strategy_params = config.get('strategy_params', {})
    else:
        strategy_name = args.strategy
        start_date = args.start
        end_date = args.end
        initial_capital = args.capital
        strategy_params = {
            'top_n': args.top_n,
            'lookback_period': args.lookback,
            'holding_period': args.holding_period,
        }
    
    # 运行回测
    run_backtest(
        strategy_name=strategy_name,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        strategy_params=strategy_params,
        output_dir=args.output
    )


if __name__ == '__main__':
    main()
