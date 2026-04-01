#!/usr/bin/env python3
"""
东方财富批量获取测试

使用 Playwright 批量获取多只股票的实时行情
"""

import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("❌ Playwright 未安装")
    sys.exit(1)


def batch_get_stocks(codes: list, timeout: int = 30000) -> dict:
    """
    批量获取股票价格
    
    Args:
        codes: 股票代码列表
        timeout: 超时时间
    
    Returns:
        结果字典
    """
    results = {
        'timestamp': datetime.now().isoformat(),
        'total': len(codes),
        'success': 0,
        'failed': 0,
        'data': []
    }
    
    try:
        with sync_playwright() as p:
            # 启动浏览器
            browser = p.chromium.launch(
                headless=True,
                args=['--disable-gpu', '--no-sandbox']
            )
            
            # 创建页面
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = context.new_page()
            page.set_default_timeout(timeout)
            
            start_time = time.time()
            
            for i, code in enumerate(codes, 1):
                # 转换代码格式
                if code.startswith('6'):
                    market = 'sh'
                else:
                    market = 'sz'
                
                full_code = f"{market}{code}"
                url = f"https://quote.eastmoney.com/{full_code}.html"
                
                print(f"[{i}/{len(codes)}] 获取 {code}...", end=' ')
                
                try:
                    # 访问页面
                    page.goto(url, wait_until="domcontentloaded", timeout=timeout)
                    
                    # 等待并提取数据
                    time.sleep(2)  # 等待数据加载
                    
                    # 获取价格
                    price_elem = page.query_selector(".hq-hq")
                    price = float(price_elem.inner_text()) if price_elem else None
                    
                    # 获取涨跌幅
                    change_elem = page.query_selector(".hq-zdf")
                    change_pct = None
                    if change_elem:
                        text = change_elem.inner_text().replace('%', '')
                        try:
                            change_pct = float(text)
                        except:
                            pass
                    
                    if price:
                        results['data'].append({
                            'code': code,
                            'price': price,
                            'change_pct': change_pct,
                            'timestamp': datetime.now().isoformat()
                        })
                        results['success'] += 1
                        print(f"✅ ¥{price:.2f}")
                    else:
                        results['failed'] += 1
                        print(f"❌ 无数据")
                    
                    # 延迟避免限流
                    if i < len(codes):
                        time.sleep(3)
                        
                except Exception as e:
                    results['failed'] += 1
                    print(f"❌ {str(e)[:30]}")
            
            elapsed = (time.time() - start_time) * 1000
            browser.close()
            
            print(f"\n总耗时：{elapsed/1000:.1f}秒")
            
    except Exception as e:
        print(f"❌ 错误：{e}")
        import traceback
        traceback.print_exc()
    
    return results


def main():
    print("="*60)
    print("🌐 东方财富批量获取测试")
    print(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 测试股票
    codes = ['600519', '000858', '300750', '002594', '601318']
    
    print(f"\n测试股票：{len(codes)}只")
    for code in codes:
        print(f"  - {code}")
    print()
    
    # 执行批量获取
    results = batch_get_stocks(codes)
    
    # 总结
    print("\n" + "="*60)
    print("📋 测试结果")
    print("="*60)
    print(f"成功：{results['success']}/{results['total']}")
    print(f"失败：{results['failed']}")
    
    if results['data']:
        print("\n获取到的数据:")
        for item in results['data']:
            sign = '+' if item['change_pct'] and item['change_pct'] > 0 else ''
            print(f"  {item['code']}: ¥{item['price']:.2f} ({sign}{item['change_pct']:.2f}%)")
    
    # 保存结果
    output_file = Path(__file__).parent / 'batch_results.json'
    import json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存：{output_file}")
    print("="*60)
    
    return results['success'] == len(codes)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
