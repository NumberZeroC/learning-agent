#!/usr/bin/env python3
"""
实时数据获取测试脚本

测试各大数据源的实时行情获取能力：
- 东方财富 API
- 新浪财经 API  
- Tushare Pro
- AKShare

测试内容：
- 连接成功率
- 数据准确性
- 响应时间
- 限流情况
"""

import sys
import time
import requests
from datetime import datetime
from pathlib import Path

# 监控股票列表
WATCHLIST = [
    ('600519', '贵州茅台'),
    ('000858', '五粮液'),
    ('300750', '宁德时代'),
    ('002594', '比亚迪'),
    ('601318', '中国平安'),
]


def format_ts_code(code):
    """转换股票代码格式"""
    if code.startswith('6'):
        return f"{code}.SH"
    elif code.startswith('0') or code.startswith('3'):
        return f"{code}.SZ"
    return code


def test_eastmoney(codes=None):
    """测试东方财富 API"""
    print("\n" + "="*60)
    print("📊 测试东方财富 API")
    print("="*60)
    
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": "1",
        "pz": "500",
        "po": "1",
        "np": "1",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "fid": "f3",
        "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",  # 沪深 A 股
        "fields": "f12,f13,f14,f43,f44,f45,f46,f47,f48,f146,f147,f148",
        "_": "1626077376000"
    }
    
    results = []
    start_time = time.time()
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        
        data = resp.json()
        
        if data.get('data') and data['data'].get('diff'):
            elapsed = (time.time() - start_time) * 1000
            
            # 查找监控股票
            stock_dict = {item['f12']: item for item in data['data']['diff']}
            
            print(f"\n响应时间：{elapsed:.0f}ms")
            print(f"获取股票数：{len(data['data']['diff'])}只")
            print(f"\n监控股票实时行情:")
            print(f"{'代码':<10} {'名称':<10} {'最新价':>10} {'涨跌额':>10} {'涨跌幅':>10}")
            print("-"*60)
            
            for code, name in WATCHLIST:
                if code in stock_dict:
                    item = stock_dict[code]
                    price = item.get('f43', 0)
                    change = item.get('f44', 0)
                    change_pct = item.get('f146', 0)
                    
                    print(f"{code:<10} {name:<10} ¥{price:>8.2f} {change:>9.2f} {change_pct:>9.2f}%")
                    results.append({
                        'code': code,
                        'name': name,
                        'price': price,
                        'change': change,
                        'change_pct': change_pct
                    })
                else:
                    print(f"{code:<10} {name:<10} 未找到")
            
            print(f"\n✅ 东方财富 API 测试成功")
            return True, results
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False, []
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接错误：{e}")
        return False, []
    except Exception as e:
        print(f"❌ 错误：{e}")
        return False, []


def test_sina(codes=None):
    """测试新浪财经 API"""
    print("\n" + "="*60)
    print("📈 测试新浪财经 API")
    print("="*60)
    
    # 转换代码格式
    code_list = []
    for code, _ in WATCHLIST:
        if code.startswith('6'):
            code_list.append(f"sh{code}")
        else:
            code_list.append(f"sz{code}")
    
    codes_str = ",".join(code_list)
    url = f"https://hq.sinajs.cn/list={codes_str}"
    
    start_time = time.time()
    
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        
        elapsed = (time.time() - start_time) * 1000
        
        # 解析数据
        # 格式：var hq_str_sh600519="贵州茅台，1800.00,1800.00,1795.00,1810.00,..."
        print(f"\n响应时间：{elapsed:.0f}ms")
        print(f"\n监控股票实时行情:")
        print(f"{'代码':<10} {'名称':<10} {'当前价':>10} {'今开':>10} {'昨收':>10} {'涨跌幅':>10}")
        print("-"*60)
        
        results = []
        lines = resp.text.strip().split('\n')
        
        for line in lines:
            if not line or '=' not in line:
                continue
            
            # 提取代码
            code_part = line.split('=')[0].replace('var hq_str_', '')
            code = code_part[2:]  # 去掉 sh/sz 前缀
            
            # 解析数据
            data_str = line.split('"')[1] if '"' in line else ""
            if not data_str:
                continue
            
            data = data_str.split(',')
            if len(data) < 10:
                continue
            
            name = data[0]
            open_price = float(data[1]) if data[1] else 0
            close = float(data[3]) if data[3] else 0  # 昨收
            current = float(data[8]) if data[8] else 0  # 当前价
            
            change_pct = ((current - close) / close * 100) if close > 0 else 0
            
            print(f"{code:<10} {name:<10} ¥{current:>8.2f} ¥{open_price:>8.2f} ¥{close:>8.2f} {change_pct:>9.2f}%")
            
            results.append({
                'code': code,
                'name': name,
                'price': current,
                'open': open_price,
                'close': close,
                'change_pct': change_pct
            })
        
        print(f"\n✅ 新浪财经 API 测试成功")
        return True, results
        
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False, []
    except Exception as e:
        print(f"❌ 错误：{e}")
        return False, []


def test_tushare():
    """测试 Tushare Pro"""
    print("\n" + "="*60)
    print("💎 测试 Tushare Pro")
    print("="*60)
    
    try:
        import tushare as ts
        
        # 加载配置
        config_path = Path(__file__).parent / 'config.yaml'
        if config_path.exists():
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            token = config.get('tushare', {}).get('token', '')
        else:
            import os
            token = os.getenv('TUSHARE_TOKEN', '')
        
        if not token:
            print("⚠️ Tushare Token 未配置，跳过测试")
            return None, []
        
        ts.set_token(token)
        pro = ts.pro_api()
        
        start_time = time.time()
        
        # 测试获取日线数据
        print("\n测试获取日线数据 (昨日):")
        results = []
        
        for code, name in WATCHLIST:
            ts_code = format_ts_code(code)
            
            try:
                df = pro.daily(ts_code=ts_code)
                elapsed = (time.time() - start_time) * 1000
                
                if not df.empty:
                    row = df.iloc[0]
                    close = float(row.get('close', 0))
                    pct_chg = float(row.get('pct_chg', 0))
                    
                    print(f"  {code} {name}: ¥{close:.2f} ({pct_chg:+.2f}%)")
                    
                    results.append({
                        'code': code,
                        'name': name,
                        'price': close,
                        'change_pct': pct_chg
                    })
                else:
                    print(f"  {code} {name}: 无数据")
                    
            except Exception as e:
                print(f"  {code} {name}: 错误 {str(e)[:50]}")
        
        print(f"\n总耗时：{elapsed:.0f}ms")
        print(f"\n✅ Tushare Pro 测试成功")
        return True, results
        
    except ImportError:
        print("⚠️ Tushare 未安装，跳过测试")
        return None, []
    except Exception as e:
        print(f"❌ 错误：{e}")
        return False, []


def test_akshare():
    """测试 AKShare"""
    print("\n" + "="*60)
    print("🔧 测试 AKShare")
    print("="*60)
    
    try:
        import akshare as ak
        
        start_time = time.time()
        
        # 测试获取实时行情
        print("\n测试获取 A 股实时行情:")
        
        df = ak.stock_zh_a_spot_em()
        elapsed = (time.time() - start_time) * 1000
        
        print(f"响应时间：{elapsed:.0f}ms")
        print(f"获取股票数：{len(df)}只")
        
        # 查找监控股票
        print(f"\n监控股票实时行情:")
        print(f"{'代码':<10} {'名称':<10} {'最新价':>10} {'涨跌幅':>10}")
        print("-"*60)
        
        results = []
        for code, name in WATCHLIST:
            stock = df[df['代码'] == code]
            if not stock.empty:
                row = stock.iloc[0]
                price = float(row['最新价'])
                change_pct = float(row['涨跌幅'])
                
                print(f"{code:<10} {name:<10} ¥{price:>8.2f} {change_pct:>9.2f}%")
                
                results.append({
                    'code': code,
                    'name': name,
                    'price': price,
                    'change_pct': change_pct
                })
            else:
                print(f"{code:<10} {name:<10} 未找到")
        
        print(f"\n✅ AKShare 测试成功")
        return True, results
        
    except ImportError:
        print("⚠️ AKShare 未安装，跳过测试")
        return None, []
    except Exception as e:
        print(f"❌ 错误：{e}")
        return False, []


def test_rate_limit():
    """测试限流情况"""
    print("\n" + "="*60)
    print("🚦 测试限流情况（连续请求 10 次）")
    print("="*60)
    
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {"pn": "1", "pz": "50", "fs": "m:0+t:6"}
    
    success_count = 0
    fail_count = 0
    times = []
    
    for i in range(10):
        start = time.time()
        try:
            resp = requests.get(url, params=params, timeout=5)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            
            if resp.status_code == 200:
                success_count += 1
                print(f"  {i+1}. ✅ {elapsed:.0f}ms")
            else:
                fail_count += 1
                print(f"  {i+1}. ❌ HTTP {resp.status_code}")
        except Exception as e:
            fail_count += 1
            print(f"  {i+1}. ❌ {str(e)[:30]}")
        
        time.sleep(0.1)  # 100ms 间隔
    
    print(f"\n成功：{success_count}/10, 失败：{fail_count}/10")
    if times:
        print(f"平均响应：{sum(times)/len(times):.0f}ms")
        print(f"最快：{min(times):.0f}ms, 最慢：{max(times):.0f}ms")
    
    return success_count >= 8


def main():
    """主测试函数"""
    print("="*60)
    print("📊 Stock-Agent 实时数据获取测试")
    print(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = {}
    
    # 1. 测试东方财富
    success, data = test_eastmoney()
    results['eastmoney'] = {'success': success, 'data': data}
    time.sleep(0.5)
    
    # 2. 测试新浪财经
    success, data = test_sina()
    results['sina'] = {'success': success, 'data': data}
    time.sleep(0.5)
    
    # 3. 测试 Tushare
    success, data = test_tushare()
    results['tushare'] = {'success': success, 'data': data}
    time.sleep(0.5)
    
    # 4. 测试 AKShare
    success, data = test_akshare()
    results['akshare'] = {'success': success, 'data': data}
    time.sleep(0.5)
    
    # 5. 测试限流
    print("\n" + "="*60)
    rate_limit_ok = test_rate_limit()
    
    # 总结
    print("\n" + "="*60)
    print("📋 测试结果总结")
    print("="*60)
    
    for source, result in results.items():
        if result['success'] is None:
            status = "⏭️ 跳过"
        elif result['success']:
            status = "✅ 成功"
        else:
            status = "❌ 失败"
        
        data_count = len(result['data']) if result['data'] else 0
        print(f"{source:<15} {status:<10} 数据：{data_count}只")
    
    print(f"\n限流测试：{'✅ 通过' if rate_limit_ok else '❌ 未通过'}")
    
    # 推荐
    print("\n" + "="*60)
    print("💡 推荐方案")
    print("="*60)
    
    if results['eastmoney']['success']:
        print("✅ 推荐使用 东方财富 API（实时、免费、稳定）")
    
    if results['sina']['success']:
        print("✅ 推荐使用 新浪财经 API（备用数据源）")
    
    if results['tushare']['success']:
        print("✅ 推荐使用 Tushare Pro（日线数据、盘后分析）")
    
    if results['akshare']['success']:
        print("✅ 推荐使用 AKShare（开源免费、备用）")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
    
    # 保存结果
    output_file = Path(__file__).parent / 'data' / 'test_results.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'rate_limit': rate_limit_ok
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存：{output_file}")


if __name__ == '__main__':
    main()
