#!/usr/bin/env python3
"""
双数据源故障切换测试
测试 Tushare + AKShare 的自动切换功能
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from stock_agent import TushareSource, AKShareSource, Config


def test_dual_source():
    """测试双数据源"""
    print("=" * 70)
    print("🔄 双数据源故障切换测试")
    print("=" * 70)
    
    config = Config()
    
    # ==================== 初始化 Tushare ====================
    print("\n1️⃣  初始化 Tushare Pro")
    print("-" * 70)
    
    ts_token = config.get('tushare.token', '')
    ts_available = False
    
    try:
        ts = TushareSource(token=ts_token, cache_ttl=300)
        print(f"   ✅ Tushare 已连接")
        ts_available = True
    except Exception as e:
        print(f"   ❌ Tushare 初始化失败：{e}")
        ts = None
    
    # ==================== 初始化 AKShare ====================
    print("\n2️⃣  初始化 AKShare")
    print("-" * 70)
    
    ak_available = False
    
    try:
        ak = AKShareSource(cache_ttl=300, max_retries=2)
        print(f"   ✅ AKShare 已连接")
        ak_available = True
    except Exception as e:
        print(f"   ❌ AKShare 初始化失败：{e}")
        ak = None
    
    # ==================== 数据源状态 ====================
    print("\n📊 数据源状态")
    print("-" * 70)
    print(f"   Tushare: {'✅ 可用' if ts_available else '❌ 不可用'}")
    print(f"   AKShare: {'✅ 可用' if ak_available else '❌ 不可用'}")
    
    if not ts_available and not ak_available:
        print("\n❌ 无可用数据源，测试终止")
        return
    
    # ==================== 故障切换测试 ====================
    print("\n🔄 故障切换测试")
    print("-" * 70)
    
    test_stocks = [
        ('600519.SH', '贵州茅台'),
        ('000858.SZ', '五粮液'),
        ('300750.SZ', '宁德时代'),
    ]
    
    results = {
        'tushare_only': 0,
        'akshare_only': 0,
        'both_success': 0,
        'both_failed': 0,
    }
    
    for ts_code, name in test_stocks:
        print(f"\n测试：{name} ({ts_code})")
        
        ts_data = None
        ak_data = None
        
        # Tushare 获取
        if ts_available:
            try:
                ts_data = ts.get_daily(ts_code)
                if ts_data:
                    print(f"   Tushare: ✅ {ts_data['close']:.2f}元 ({ts_data['pct_chg']:+.2f}%)")
                else:
                    print(f"   Tushare: ⚠️ 无数据")
            except Exception as e:
                print(f"   Tushare: ❌ {e}")
        
        # AKShare 获取
        if ak_available:
            try:
                ak_data = ak.get_daily_quote(ts_code)
                if ak_data:
                    print(f"   AKShare: ✅ {ak_data['close']:.2f}元 ({ak_data['pct_chg']:+.2f}%)")
                else:
                    print(f"   AKShare: ⚠️ 无数据")
            except Exception as e:
                print(f"   AKShare: ❌ {e}")
        
        # 统计
        if ts_data and ak_data:
            results['both_success'] += 1
            # 数据对比
            if abs(ts_data['close'] - ak_data['close']) < 0.1:
                print(f"   📊 数据一致 ✓")
            else:
                print(f"   ⚠️ 数据差异：{abs(ts_data['close'] - ak_data['close']):.2f}元")
        elif ts_data:
            results['tushare_only'] += 1
        elif ak_data:
            results['akshare_only'] += 1
        else:
            results['both_failed'] += 1
    
    # ==================== 测试总结 ====================
    print("\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)
    
    print(f"\n双数据源成功：{results['both_success']} 只")
    print(f"仅 Tushare 成功：{results['tushare_only']} 只")
    print(f"仅 AKShare 成功：{results['akshare_only']} 只")
    print(f"都失败：{results['both_failed']} 只")
    
    # 故障切换策略
    print("\n🔄 故障切换策略")
    print("-" * 70)
    print("""
    def get_price(ts_code):
        # 1. 优先使用 Tushare
        if ts_available:
            data = ts.get_daily(ts_code)
            if data:
                return data
        
        # 2. Tushare 失败，切换 AKShare
        if ak_available:
            data = ak.get_daily_quote(ts_code)
            if data:
                return data
        
        # 3. 都失败
        return None
    
    优先级：Tushare (主) > AKShare (备用)
    """)
    
    # 缓存统计
    print("\n📦 缓存统计")
    print("-" * 70)
    
    if ts_available:
        ts_stats = ts.get_cache_stats()
        print(f"   Tushare: 命中{ts_stats['hits']}, 未命中{ts_stats['misses']}, 命中率{ts_stats['hit_rate']}")
    
    if ak_available:
        ak_stats = ak.get_cache_stats()
        print(f"   AKShare: 命中{ak_stats['hits']}, 未命中{ak_stats['misses']}, 命中率{ak_stats['hit_rate']}")
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)


if __name__ == '__main__':
    test_dual_source()
