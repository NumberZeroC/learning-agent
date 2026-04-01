#!/usr/bin/env python3
"""
Tushare 数据接口测试脚本

测试所有可用的数据接口，确保 2000 积分可用功能正常
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from stock_agent import TushareSource, Config


def test_all_interfaces():
    """测试所有数据接口"""
    print("=" * 70)
    print("📊 Tushare 数据接口测试 (2000 积分)")
    print("=" * 70)
    
    # 加载配置
    config = Config()
    token = config.get('tushare.token', '')
    
    if not token:
        print("❌ Tushare Token 未配置")
        return
    
    # 初始化数据源
    ts = TushareSource(token=token, cache_ttl=300)
    
    results = {
        'success': [],
        'failed': [],
        'skipped': []
    }
    
    # ==================== 基础行情 ====================
    print("\n📈 基础行情测试")
    print("-" * 70)
    
    # 1. 股票列表
    print("1. 获取股票列表...")
    try:
        stocks = ts.get_stock_basic()
        if stocks:
            print(f"   ✅ 成功：{len(stocks)}只股票")
            results['success'].append('get_stock_basic')
        else:
            print(f"   ⚠️ 返回空数据")
            results['skipped'].append('get_stock_basic')
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        results['failed'].append('get_stock_basic')
    
    # 2. 日线行情
    print("2. 获取贵州茅台日线...")
    try:
        daily = ts.get_daily('600519.SH')
        if daily:
            print(f"   ✅ 成功：{daily['close']:.2f}元 ({daily['pct_chg']:+.2f}%)")
            results['success'].append('get_daily')
        else:
            print(f"   ⚠️ 返回空数据")
            results['skipped'].append('get_daily')
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        results['failed'].append('get_daily')
    
    # 3. 批量日线
    print("3. 批量获取日线...")
    try:
        codes = ['600519.SH', '000858.SZ', '300750.SZ']
        data = ts.get_daily_batch(codes)
        if data:
            print(f"   ✅ 成功：{len(data)}只股票")
            results['success'].append('get_daily_batch')
        else:
            print(f"   ⚠️ 返回空数据")
            results['skipped'].append('get_daily_batch')
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        results['failed'].append('get_daily_batch')
    
    # ==================== 指数数据 ====================
    print("\n📊 指数数据测试")
    print("-" * 70)
    
    # 4. 主要指数
    print("4. 获取主要指数...")
    try:
        indices = ts.get_major_indices()
        if indices:
            print(f"   ✅ 成功：")
            for name, data in indices.items():
                print(f"      {name}: {data['close']:.2f} ({data['pct_chg']:+.2f}%)")
            results['success'].append('get_major_indices')
        else:
            print(f"   ⚠️ 返回空数据")
            results['skipped'].append('get_major_indices')
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        results['failed'].append('get_major_indices')
    
    # ==================== 资金流 ====================
    print("\n💰 资金流测试 (300 积分)")
    print("-" * 70)
    
    # 5. 个股资金流
    print("5. 获取贵州茅台资金流...")
    try:
        moneyflow = ts.get_moneyflow('600519.SH')
        if moneyflow:
            net = moneyflow['net_mf_amount'] / 10000
            print(f"   ✅ 成功：主力净流入 {net:+.1f}万")
            results['success'].append('get_moneyflow')
        else:
            print(f"   ⚠️ 返回空数据 (可能无权限)")
            results['skipped'].append('get_moneyflow')
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        results['failed'].append('get_moneyflow')
    
    # 6. 北向资金
    print("6. 获取北向资金...")
    try:
        north = ts.get_north_flow()
        if north:
            print(f"   ✅ 成功：净流入 {north['north_net_in']/10000:.1f}万")
            results['success'].append('get_north_flow')
        else:
            print(f"   ⚠️ 返回空数据")
            results['skipped'].append('get_north_flow')
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        results['failed'].append('get_north_flow')
    
    # 7. 龙虎榜
    print("7. 获取龙虎榜...")
    try:
        top_list = ts.get_top_list()
        if top_list:
            print(f"   ✅ 成功：{len(top_list)}只股票")
            results['success'].append('get_top_list')
        else:
            print(f"   ⚠️ 今日无龙虎榜")
            results['skipped'].append('get_top_list')
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        results['failed'].append('get_top_list')
    
    # ==================== 财务数据 ====================
    print("\n📋 财务数据测试")
    print("-" * 70)
    
    # 8. 财务指标
    print("8. 获取贵州茅台财务指标...")
    try:
        fina = ts.get_fina_indicator('600519.SH')
        if fina:
            latest = fina[0]
            print(f"   ✅ 成功：{latest['end_date']}")
            print(f"      营收：{latest['revenue']/1e8:.1f}亿")
            print(f"      净利润：{latest['net_profit']/1e8:.1f}亿")
            print(f"      ROE: {latest['roe']:.1f}%")
            results['success'].append('get_fina_indicator')
        else:
            print(f"   ⚠️ 返回空数据")
            results['skipped'].append('get_fina_indicator')
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        results['failed'].append('get_fina_indicator')
    
    # 9. 每日基本面
    print("9. 获取每日基本面指标...")
    try:
        basic = ts.get_daily_basic('600519.SH')
        if basic:
            data = basic[0]
            print(f"   ✅ 成功：PE={data['pe']:.1f}, PB={data['pb']:.1f}, 市值={data['total_mv']/1e8:.1f}亿")
            results['success'].append('get_daily_basic')
        else:
            print(f"   ⚠️ 返回空数据")
            results['skipped'].append('get_daily_basic')
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        results['failed'].append('get_daily_basic')
    
    # ==================== 特色数据 ====================
    print("\n🎯 特色数据测试")
    print("-" * 70)
    
    # 10. 复权因子
    print("10. 获取复权因子...")
    try:
        adj = ts.get_adj_factor('600519.SH')
        if adj:
            print(f"   ✅ 成功：复权因子={adj['adj_factor']:.2f}, 复权价={adj['adj_close']:.2f}")
            results['success'].append('get_adj_factor')
        else:
            print(f"   ⚠️ 返回空数据")
            results['skipped'].append('get_adj_factor')
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        results['failed'].append('get_adj_factor')
    
    # 11. 分钟线
    print("11. 获取 5 分钟线...")
    try:
        mins = ts.get_min('600519.SH', min_type='5')
        if mins:
            print(f"   ✅ 成功：{len(mins)}条")
            results['success'].append('get_min')
        else:
            print(f"   ⚠️ 返回空数据 (非交易时间)")
            results['skipped'].append('get_min')
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        results['failed'].append('get_min')
    
    # 12. 概念板块
    print("12. 获取概念板块...")
    try:
        concepts = ts.get_concept_list()
        if concepts:
            print(f"   ✅ 成功：{len(concepts)}个板块")
            results['success'].append('get_concept_list')
        else:
            print(f"   ⚠️ 返回空数据")
            results['skipped'].append('get_concept_list')
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        results['failed'].append('get_concept_list')
    
    # 13. 行业板块
    print("13. 获取行业板块...")
    try:
        industries = ts.get_industry_list()
        if industries:
            print(f"   ✅ 成功：{len(industries)}个行业")
            results['success'].append('get_industry_list')
        else:
            print(f"   ⚠️ 返回空数据")
            results['skipped'].append('get_industry_list')
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        results['failed'].append('get_industry_list')
    
    # 14. 融资融券
    print("14. 获取融资融券...")
    try:
        margin = ts.get_margin('600519.SH')
        if margin:
            data = margin[0]
            print(f"   ✅ 成功：融资余额={data['fin_balance']/1e8:.2f}亿")
            results['success'].append('get_margin')
        else:
            print(f"   ⚠️ 返回空数据")
            results['skipped'].append('get_margin')
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        results['failed'].append('get_margin')
    
    # 15. 前十大股东
    print("15. 获取前十大股东...")
    try:
        holders = ts.get_top10_holders('600519.SH')
        if holders:
            print(f"   ✅ 成功：{len(holders)}个股东")
            results['success'].append('get_top10_holders')
        else:
            print(f"   ⚠️ 返回空数据")
            results['skipped'].append('get_top10_holders')
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        results['failed'].append('get_top10_holders')
    
    # 16. 业绩预告
    print("16. 获取业绩预告...")
    try:
        forecast = ts.get_forecast('600519.SH')
        if forecast:
            print(f"   ✅ 成功：{len(forecast)}条预告")
            results['success'].append('get_forecast')
        else:
            print(f"   ⚠️ 无业绩预告")
            results['skipped'].append('get_forecast')
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        results['failed'].append('get_forecast')
    
    # 17. 停复牌
    print("17. 获取停复牌...")
    try:
        suspend = ts.get_suspend_d()
        print(f"   ✅ 成功：{len(suspend)}只股票")
        results['success'].append('get_suspend_d')
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        results['failed'].append('get_suspend_d')
    
    # ==================== 测试总结 ====================
    print("\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)
    print(f"✅ 成功：{len(results['success'])} 个接口")
    print(f"⚠️  跳过：{len(results['skipped'])} 个接口 (无数据/非交易时间)")
    print(f"❌ 失败：{len(results['failed'])} 个接口")
    print()
    
    if results['success']:
        print("成功接口列表:")
        for name in results['success']:
            print(f"  • {name}")
    
    if results['skipped']:
        print("\n跳过接口列表 (可能因权限或数据原因):")
        for name in results['skipped']:
            print(f"  • {name}")
    
    if results['failed']:
        print("\n失败接口列表:")
        for name in results['failed']:
            print(f"  • {name}")
    
    # 缓存统计
    print("\n📦 缓存统计:")
    stats = ts.get_cache_stats()
    print(f"  命中：{stats['hits']}, 未命中：{stats['misses']}, 命中率：{stats['hit_rate']}")
    print(f"  缓存文件：{stats['cache_files']} 个")
    
    # 保存测试结果
    import json
    from datetime import datetime
    
    test_report = {
        'timestamp': datetime.now().isoformat(),
        'token_points': 2000,
        'results': results,
        'cache_stats': stats
    }
    
    report_path = Path(__file__).parent / 'data' / 'tushare_test_report.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(test_report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 测试报告已保存：{report_path}")
    print("=" * 70)


if __name__ == '__main__':
    test_all_interfaces()
