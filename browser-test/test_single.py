#!/usr/bin/env python3
"""
东方财富单只股票测试

使用 Playwright 模拟浏览器获取单只股票的实时行情
"""

import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("❌ Playwright 未安装，请运行：pip install playwright")
    print("然后运行：playwright install chromium")
    sys.exit(1)


def get_stock_price_eastmoney(code: str, timeout: int = 30000) -> dict:
    """
    获取股票实时价格（东方财富）
    
    Args:
        code: 股票代码（如 600519）
        timeout: 超时时间（毫秒）
    
    Returns:
        股票数据字典
    """
    # 转换代码格式
    if code.startswith('6'):
        market = 'sh'
    elif code.startswith('0') or code.startswith('3'):
        market = 'sz'
    else:
        market = ''
    
    full_code = f"{market}{code}"
    url = f"https://quote.eastmoney.com/{full_code}.html"
    
    result = {
        'code': code,
        'success': False,
        'error': None,
        'data': None,
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        with sync_playwright() as p:
            # 启动浏览器
            browser = p.chromium.launch(
                headless=True,  # 无头模式
                args=[
                    '--disable-gpu',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )
            
            # 创建页面
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080},
                ignore_https_errors=True
            )
            
            page = context.new_page()
            
            # 设置超时
            page.set_default_timeout(timeout)
            
            # 访问页面
            print(f"📊 访问：{url}")
            start_time = time.time()
            
            response = page.goto(url, wait_until="domcontentloaded")
            
            # 等待关键元素加载
            try:
                # 等待价格元素（东方财富的价格元素类名）
                page.wait_for_selector(".hq-hq, .current-price, [data-name='currentPrice']", timeout=10000)
            except PlaywrightTimeout:
                print("⚠️ 等待元素超时，尝试直接获取")
            
            # 小延迟确保数据加载
            time.sleep(2)
            
            # 尝试多种方式获取价格
            price = None
            change = None
            change_pct = None
            high = None
            low = None
            open_price = None
            prev_close = None
            volume = None
            amount = None
            
            # 方法 1：通过 CSS 选择器
            selectors = {
                'price': ['.hq-hq', '.current-price', '[data-name="currentPrice"]'],
                'change': ['.hq-zde', '.change-value', '[data-name="diffPrice"]'],
                'change_pct': ['.hq-zdf', '.change-percent', '[data-name="diffRate"]'],
                'high': ['.hq-high', '[data-name="highPrice"]'],
                'low': ['.hq-low', '[data-name="lowPrice"]'],
                'open': ['.hq-open', '[data-name="openPrice"]'],
                'prev_close': ['.hq-preclose', '[data-name="lastClosePrice"]'],
            }
            
            for key, selector_list in selectors.items():
                for selector in selector_list:
                    try:
                        element = page.query_selector(selector)
                        if element:
                            text = element.inner_text().strip()
                            # 清理数据（移除¥、%等符号）
                            text = text.replace('¥', '').replace('%', '').replace(',', '')
                            if text and text not in ['--', '-', '']:
                                value = float(text)
                                locals()[key] = value
                                break
                    except:
                        continue
            
            # 方法 2：通过 JavaScript 获取
            if not price:
                try:
                    js_data = page.evaluate("""
                        () => {
                            // 尝试从全局变量获取
                            if (window.quoteData) {
                                return window.quoteData;
                            }
                            // 尝试从页面数据属性获取
                            const dataElement = document.querySelector('[data-quote]');
                            if (dataElement) {
                                try {
                                    return JSON.parse(dataElement.dataset.quote);
                                } catch(e) {}
                            }
                            return null;
                        }
                    """)
                    
                    if js_data:
                        price = js_data.get('price') or js_data.get('currentPrice')
                        change = js_data.get('change') or js_data.get('diffPrice')
                        change_pct = js_data.get('changePercent') or js_data.get('diffRate')
                        
                except Exception as e:
                    print(f"⚠️ JS 获取失败：{e}")
            
            # 方法 3：从页面文本提取
            if not price:
                try:
                    page_content = page.content()
                    # 简单的文本搜索（不推荐，仅作备用）
                    import re
                    price_match = re.search(r'当前价.*?(\d+\.\d+)', page_content)
                    if price_match:
                        price = float(price_match.group(1))
                except:
                    pass
            
            elapsed = (time.time() - start_time) * 1000
            
            # 关闭浏览器
            browser.close()
            
            # 检查结果
            if price:
                result['success'] = True
                result['data'] = {
                    'code': code,
                    'full_code': full_code,
                    'price': float(price),
                    'change': float(change) if change else 0,
                    'change_pct': float(change_pct) if change_pct else 0,
                    'high': float(high) if high else 0,
                    'low': float(low) if low else 0,
                    'open': float(open_price) if open_price else 0,
                    'prev_close': float(prev_close) if prev_close else 0,
                }
                
                print(f"✅ 获取成功 ({elapsed:.0f}ms)")
                print(f"   代码：{code}")
                print(f"   价格：¥{price:.2f}")
                if change_pct:
                    sign = '+' if change_pct > 0 else ''
                    print(f"   涨跌：{sign}{change:.2f} ({sign}{change_pct:.2f}%)")
            else:
                result['error'] = '无法提取价格数据'
                print(f"❌ 获取失败：无法提取价格数据")
                print(f"   耗时：{elapsed:.0f}ms")
            
    except PlaywrightTimeout as e:
        result['error'] = f'超时：{str(e)}'
        print(f"❌ 请求超时：{e}")
    except Exception as e:
        result['error'] = str(e)
        print(f"❌ 错误：{e}")
        import traceback
        traceback.print_exc()
    
    return result


def test_stocks():
    """测试多只股票"""
    print("="*60)
    print("🌐 东方财富浏览器自动化测试")
    print(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 测试股票列表
    test_stocks = [
        ('600519', '贵州茅台'),
        ('000858', '五粮液'),
        ('300750', '宁德时代'),
        ('002594', '比亚迪'),
        ('601318', '中国平安'),
    ]
    
    results = []
    
    for i, (code, name) in enumerate(test_stocks, 1):
        print(f"\n[{i}/{len(test_stocks)}] 测试 {name}({code})...")
        
        result = get_stock_price_eastmoney(code)
        results.append(result)
        
        # 添加延迟避免限流
        if i < len(test_stocks):
            delay = 5  # 5 秒间隔
            print(f"⏳ 等待 {delay}秒...")
            time.sleep(delay)
    
    # 总结
    print("\n" + "="*60)
    print("📋 测试结果总结")
    print("="*60)
    
    success_count = sum(1 for r in results if r['success'])
    print(f"\n成功：{success_count}/{len(test_stocks)}")
    
    if success_count > 0:
        print(f"\n成功获取的股票:")
        for r in results:
            if r['success'] and r['data']:
                data = r['data']
                sign = '+' if data['change_pct'] > 0 else ''
                print(f"  {data['code']}: ¥{data['price']:.2f} ({sign}{data['change_pct']:.2f}%)")
    
    print("\n" + "="*60)
    
    # 保存结果
    output_file = Path(__file__).parent / 'test_results.json'
    import json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total': len(test_stocks),
            'success': success_count,
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存：{output_file}")
    
    return success_count == len(test_stocks)


if __name__ == '__main__':
    success = test_stocks()
    sys.exit(0 if success else 1)
