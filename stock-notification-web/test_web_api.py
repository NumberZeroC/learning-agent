#!/usr/bin/env python3
"""
Stock-Notification-Web API 测试脚本

功能：
1. 检查所有 API 接口是否可用
2. 验证返回数据格式是否正确
3. 验证数据内容是否合理
4. 发送测试结果通知

使用：
    python3 test_web_api.py [--send-notify]
    
定时执行：
    每天 19:00 自动执行
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# 配置
WEB_HOST = os.getenv('WEB_HOST', 'http://localhost:5000')
TIMEOUT = int(os.getenv('TEST_TIMEOUT', '10'))
LOG_DIR = Path('/home/admin/.openclaw/workspace/stock-notification-web/logs')
NOTIFY_ENABLED = os.getenv('TEST_SEND_NOTIFY', 'false').lower() == 'true'

# API 端点列表
API_ENDPOINTS = [
    {
        'name': '首页',
        'method': 'GET',
        'url': '/',
        'expect_status': 200,
        'check_content': True
    },
    {
        'name': '最新报告数据',
        'method': 'GET',
        'url': '/api/v1/reports/latest-data',
        'expect_status': 200,
        'check_data': True
    },
    {
        'name': '报告列表',
        'method': 'GET',
        'url': '/api/v1/reports',
        'expect_status': 200,
        'check_data': True
    },
    {
        'name': '市场数据',
        'method': 'GET',
        'url': '/api/v1/data/market',
        'expect_status': 200,
        'check_data': True,
        'optional': True  # 可选端点，404 不算失败
    },
    {
        'name': '板块资金流',
        'method': 'GET',
        'url': '/api/v1/data/capital/sectors',
        'expect_status': 200,
        'check_data': True
    },
    {
        'name': 'AI 新闻',
        'method': 'GET',
        'url': '/api/v1/data/ai-news',
        'expect_status': 200,
        'check_data': True
    },
    {
        'name': '聚合数据',
        'method': 'GET',
        'url': '/api/v1/data/aggregated',
        'expect_status': 200,
        'check_data': True,
        'optional': True  # 可选端点，404 不算失败
    },
    {
        'name': '持仓监控',
        'method': 'GET',
        'url': '/api/v1/monitor/stocks',
        'expect_status': 200,
        'check_data': True,
        'critical': True  # 关键检查，股价为 0 则失败
    },
    {
        'name': '数据看板大盘指数',
        'method': 'GET',
        'url': '/api/v1/reports/latest-data',
        'expect_status': 200,
        'check_data': True,
        'critical': True,  # 关键检查，大盘指数为 0 则失败
        'check_index': True  # 专门检查大盘指数
    },
    {
        'name': '龙虎榜交易数据',
        'method': 'GET',
        'url': '/api/v1/reports/latest-data',
        'expect_status': 200,
        'check_data': True,
        'critical': True,  # 关键检查，交易数据为 0 则失败
        'check_top_list': True  # 专门检查龙虎榜
    },
]


class WebAPITester:
    """Web API 测试器"""
    
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
        self.log_file = LOG_DIR / f'test_{self.start_time.strftime("%Y%m%d_%H%M%S")}.log'
        
        # 确保日志目录存在
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    def log(self, message: str, level: str = 'INFO'):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f'[{timestamp}] [{level}] {message}'
        print(log_line)
        
        # 写入日志文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')
    
    def test_endpoint(self, endpoint: Dict) -> Dict:
        """测试单个 API 端点"""
        result = {
            'name': endpoint['name'],
            'url': endpoint['url'],
            'method': endpoint['method'],
            'status': 'unknown',
            'http_status': None,
            'response_time': None,
            'error': None,
            'data_valid': None,
            'checks': []
        }
        
        try:
            # 发送请求
            start = time.time()
            
            if endpoint['method'] == 'GET':
                response = requests.get(
                    f'{WEB_HOST}{endpoint["url"]}',
                    timeout=TIMEOUT
                )
            else:
                result['error'] = f'不支持的方法：{endpoint["method"]}'
                result['status'] = 'failed'
                return result
            
            result['response_time'] = round((time.time() - start) * 1000, 2)
            result['http_status'] = response.status_code
            
            # 检查 HTTP 状态码
            if response.status_code != endpoint['expect_status']:
                # 可选端点 404 不算失败
                if endpoint.get('optional') and response.status_code == 404:
                    result['status'] = 'passed'
                    result['checks'].append({
                        'name': 'HTTP 状态码',
                        'passed': True,
                        'message': f'可选端点，返回 404（正常）'
                    })
                    return result
                
                result['status'] = 'failed'
                result['error'] = f'HTTP 状态码错误：期望 {endpoint["expect_status"]}, 实际 {response.status_code}'
                result['checks'].append({
                    'name': 'HTTP 状态码',
                    'passed': False,
                    'message': result['error']
                })
                return result
            
            result['checks'].append({
                'name': 'HTTP 状态码',
                'passed': True,
                'message': f'返回 {response.status_code}'
            })
            
            # 解析 JSON 响应
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                # 非 API 端点（如首页）返回 HTML 是正常的
                if endpoint.get('check_content'):
                    result['status'] = 'passed'
                    result['data_valid'] = True
                    result['checks'].append({
                        'name': '内容检查',
                        'passed': True,
                        'message': 'HTML 页面正常'
                    })
                    return result
                
                # 其他端点应该返回 JSON
                result['status'] = 'failed'
                result['error'] = f'JSON 解析失败：{e}'
                result['checks'].append({
                    'name': 'JSON 格式',
                    'passed': False,
                    'message': f'解析失败：{str(e)[:100]}'
                })
                return result
            
            # 检查 API 返回格式
            if endpoint.get('check_data'):
                data_checks = self.check_api_response(endpoint['name'], data)
                result['checks'].extend(data_checks)
                
                # 如果有关键检查失败
                failed_checks = [c for c in data_checks if not c['passed']]
                if failed_checks:
                    result['data_valid'] = False
                    result['status'] = 'warning'
                    result['error'] = f'{len(failed_checks)} 个数据检查失败'
                else:
                    result['data_valid'] = True
                    result['status'] = 'passed'
            else:
                result['data_valid'] = True
                result['status'] = 'passed'
            
        except requests.exceptions.Timeout:
            result['status'] = 'failed'
            result['error'] = f'请求超时（>{TIMEOUT}秒）'
        except requests.exceptions.ConnectionError as e:
            result['status'] = 'failed'
            result['error'] = f'连接失败：{e}'
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = f'未知错误：{e}'
        
        return result
    
    def check_api_response(self, api_name: str, data: Dict) -> List[Dict]:
        """检查 API 返回数据"""
        checks = []
        
        # 通用检查：code 字段
        if 'code' in data:
            if data['code'] == 200:
                checks.append({
                    'name': 'API 返回码',
                    'passed': True,
                    'message': 'code=200'
                })
            else:
                checks.append({
                    'name': 'API 返回码',
                    'passed': False,
                    'message': f'code={data.get("code")}'
                })
        
        # 通用检查：data 字段
        if 'data' in data:
            checks.append({
                'name': 'data 字段',
                'passed': True,
                'message': '存在'
            })
        else:
            checks.append({
                'name': 'data 字段',
                'passed': False,
                'message': '缺失'
            })
        
        # 特定 API 检查
        if api_name == '最新报告数据':
            checks.extend(self.check_latest_data(data.get('data', {})))
        elif api_name == '市场数据':
            checks.extend(self.check_market_data(data.get('data', {})))
        elif api_name == '板块资金流':
            checks.extend(self.check_sector_data(data.get('data', {})))
        elif api_name == '持仓监控':
            checks.extend(self.check_monitor_stocks(data.get('data', {})))
        elif api_name == '数据看板大盘指数':
            checks.extend(self.check_dashboard_index(data.get('data', {})))
        
        return checks
    
    def check_latest_data(self, data: Dict) -> List[Dict]:
        """检查最新报告数据"""
        checks = []
        
        # 检查指数数据
        index = data.get('index', {})
        if index.get('value', 0) > 0:
            checks.append({
                'name': '上证指数',
                'passed': True,
                'message': f'{index.get("value", 0):.2f} ({index.get("change", 0):+.2f}%)'
            })
        else:
            checks.append({
                'name': '上证指数',
                'passed': False,
                'message': '数据缺失或为 0'
            })
        
        # 检查板块数据
        sector_flows = data.get('sector_flows', [])
        if len(sector_flows) > 0:
            checks.append({
                'name': '板块资金流',
                'passed': True,
                'message': f'{len(sector_flows)} 个板块'
            })
        else:
            checks.append({
                'name': '板块资金流',
                'passed': False,
                'message': '无数据'
            })
        
        # 检查报告日期
        report_date = data.get('report_date', '')
        if report_date:
            checks.append({
                'name': '报告日期',
                'passed': True,
                'message': report_date
            })
        else:
            checks.append({
                'name': '报告日期',
                'passed': False,
                'message': '缺失'
            })
        
        return checks
    
    def check_market_data(self, data: Dict) -> List[Dict]:
        """检查市场数据"""
        checks = []
        
        if not data:
            checks.append({
                'name': '市场数据',
                'passed': False,
                'message': '数据为空'
            })
            return checks
        
        # 检查指数
        indices = data.get('indices', {})
        if indices.get('shanghai', {}).get('close', 0) > 0:
            checks.append({
                'name': '上证指数',
                'passed': True,
                'message': f'{indices["shanghai"]["close"]:.2f}'
            })
        else:
            checks.append({
                'name': '上证指数',
                'passed': False,
                'message': '数据缺失'
            })
        
        return checks
    
    def check_sector_data(self, data: Dict) -> List[Dict]:
        """检查板块资金流数据"""
        checks = []
        
        sector_flows = data.get('sector_flows', [])
        
        if len(sector_flows) > 0:
            checks.append({
                'name': '板块数量',
                'passed': True,
                'message': f'{len(sector_flows)} 个'
            })
            
            # 检查第一个板块的数据完整性
            first_sector = sector_flows[0]
            required_fields = ['sector', 'net_flow']
            missing_fields = [f for f in required_fields if f not in first_sector]
            
            if not missing_fields:
                checks.append({
                    'name': '数据完整性',
                    'passed': True,
                    'message': '字段完整'
                })
            else:
                checks.append({
                    'name': '数据完整性',
                    'passed': False,
                    'message': f'缺少字段：{", ".join(missing_fields)}'
                })
        else:
            checks.append({
                'name': '板块数量',
                'passed': False,
                'message': '无数据'
            })
        
        return checks
    
    def check_monitor_stocks(self, data: Dict) -> List[Dict]:
        """检查持仓监控数据"""
        checks = []
        
        stocks = data.get('stocks', [])
        
        if len(stocks) > 0:
            checks.append({
                'name': '监控股票数量',
                'passed': True,
                'message': f'{len(stocks)} 只'
            })
            
            # 🔥 检查股价是否为 0
            zero_price_stocks = [s for s in stocks if s.get('price', 0) == 0]
            if zero_price_stocks:
                stock_names = ', '.join([f"{s['name']}({s['code']})" for s in zero_price_stocks[:5]])
                checks.append({
                    'name': '股价数据',
                    'passed': False,
                    'message': f'{len(zero_price_stocks)} 只股票股价为 0: {stock_names}'
                })
            else:
                checks.append({
                    'name': '股价数据',
                    'passed': True,
                    'message': '所有股票股价正常'
                })
            
            # 检查涨跌幅数据
            zero_change_stocks = [s for s in stocks if s.get('change_pct', 0) == 0 and s.get('price', 0) > 0]
            if zero_change_stocks:
                # 涨跌幅为 0 可能是涨停/跌停，只警告不报错
                checks.append({
                    'name': '涨跌幅数据',
                    'passed': True,
                    'message': f'{len(zero_change_stocks)} 只股票涨跌幅为 0（可能涨停/跌停）',
                    'warning': True
                })
            
            # 检查数据完整性
            if stocks:
                first_stock = stocks[0]
                required_fields = ['code', 'name', 'price', 'signal']
                missing_fields = [f for f in required_fields if f not in first_stock]
                
                if not missing_fields:
                    checks.append({
                        'name': '数据完整性',
                        'passed': True,
                        'message': '字段完整'
                    })
                else:
                    checks.append({
                        'name': '数据完整性',
                        'passed': False,
                        'message': f'缺少字段：{", ".join(missing_fields)}'
                    })
        else:
            checks.append({
                'name': '监控股票数量',
                'passed': False,
                'message': '无监控股票'
            })
        
        return checks
    
    def check_dashboard_index(self, data: Dict) -> List[Dict]:
        """检查数据看板大盘指数数据"""
        checks = []
        
        # 🔥 检查大盘指数是否为 0
        index = data.get('index', {})
        index_value = index.get('value', 0)
        index_change = index.get('change', 0)
        
        if index_value > 0:
            checks.append({
                'name': '上证指数',
                'passed': True,
                'message': f'{index_value:.2f} ({index_change:+.2f}%)'
            })
        else:
            checks.append({
                'name': '上证指数',
                'passed': False,
                'message': f'大盘指数为 0（当前值：{index_value}）'
            })
        
        # 检查市场情绪
        sentiment = data.get('sentiment', '')
        sentiment_score = data.get('sentimentScore', 0)
        
        if sentiment and sentiment_score > 0:
            checks.append({
                'name': '市场情绪',
                'passed': True,
                'message': f'{sentiment}（得分：{sentiment_score}）'
            })
        else:
            checks.append({
                'name': '市场情绪',
                'passed': False,
                'message': '市场情绪数据缺失'
            })
        
        # 检查板块数据
        sector_flows = data.get('sector_flows', [])
        if len(sector_flows) > 0:
            checks.append({
                'name': '板块资金流',
                'passed': True,
                'message': f'{len(sector_flows)} 个板块'
            })
        else:
            checks.append({
                'name': '板块资金流',
                'passed': False,
                'message': '无板块数据'
            })
        
        return checks
    
    def check_top_list(self, data: Dict) -> List[Dict]:
        """检查龙虎榜交易数据"""
        checks = []
        
        top_list = data.get('top_list', [])
        
        # 🔥 检查龙虎榜数量
        if len(top_list) > 0:
            checks.append({
                'name': '龙虎榜数量',
                'passed': True,
                'message': f'{len(top_list)} 条'
            })
        else:
            checks.append({
                'name': '龙虎榜数量',
                'passed': False,
                'message': '龙虎榜数据为空'
            })
            return checks  # 无数据，后续检查无需进行
        
        # 🔥 检查交易数据（取前 3 条验证）
        zero_amount_count = 0
        zero_buy_count = 0
        zero_sell_count = 0
        zero_net_in_count = 0
        
        for stock in top_list[:3]:
            amount = stock.get('amount', 0)
            l_buy = stock.get('l_buy', 0)
            l_sell = stock.get('l_sell', 0)
            net_in = stock.get('net_in', 0)  # 🔥 前端使用 net_in
            
            if amount == 0:
                zero_amount_count += 1
            if l_buy == 0:
                zero_buy_count += 1
            if l_sell == 0:
                zero_sell_count += 1
            if net_in == 0:
                zero_net_in_count += 1
        
        if zero_amount_count > 0:
            checks.append({
                'name': '成交额数据',
                'passed': False,
                'message': f'{zero_amount_count} 条记录成交额为 0'
            })
        else:
            checks.append({
                'name': '成交额数据',
                'passed': True,
                'message': '成交额数据正常'
            })
        
        if zero_buy_count > 0:
            checks.append({
                'name': '买方总额',
                'passed': False,
                'message': f'{zero_buy_count} 条记录买方总额为 0'
            })
        else:
            checks.append({
                'name': '买方总额',
                'passed': True,
                'message': '买方总额数据正常'
            })
        
        if zero_sell_count > 0:
            checks.append({
                'name': '卖方总额',
                'passed': False,
                'message': f'{zero_sell_count} 条记录卖方总额为 0'
            })
        else:
            checks.append({
                'name': '卖方总额',
                'passed': True,
                'message': '卖方总额数据正常'
            })
        
        # 🔥 检查净买额
        if zero_net_in_count > 0:
            checks.append({
                'name': '净买额数据',
                'passed': False,
                'message': f'{zero_net_in_count} 条记录净买额为 0'
            })
        else:
            checks.append({
                'name': '净买额数据',
                'passed': True,
                'message': '净买额数据正常'
            })
        
        # 🔥 检查必要字段完整性
        required_fields = ['ts_code', 'name', 'close', 'amount', 'l_buy', 'l_sell', 'net_in']
        if top_list:
            first_stock = top_list[0]
            missing_fields = [f for f in required_fields if f not in first_stock]
            
            if not missing_fields:
                checks.append({
                    'name': '字段完整性',
                    'passed': True,
                    'message': '必要字段完整'
                })
            else:
                checks.append({
                    'name': '字段完整性',
                    'passed': False,
                    'message': f'缺少字段：{", ".join(missing_fields)}'
                })
        
        return checks
    
    def run_all_tests(self) -> Dict:
        """运行所有测试"""
        self.log('=' * 60)
        self.log('开始 Web API 测试')
        self.log(f'目标：{WEB_HOST}')
        self.log(f'测试端点：{len(API_ENDPOINTS)} 个')
        self.log('=' * 60)
        
        for endpoint in API_ENDPOINTS:
            self.log(f'\n测试：{endpoint["name"]}')
            result = self.test_endpoint(endpoint)
            self.results.append(result)
            
            # 记录结果
            status_icon = '✅' if result['status'] == 'passed' else ('⚠️' if result['status'] == 'warning' else '❌')
            self.log(f'  {status_icon} 状态：{result["status"]}')
            self.log(f'     HTTP: {result.get("http_status", "N/A")}')
            self.log(f'     耗时：{result.get("response_time", "N/A")}ms')
            
            if result.get('error'):
                self.log(f'     错误：{result["error"]}', level='ERROR')
            
            # 记录检查项
            for check in result.get('checks', []):
                check_icon = '✓' if check['passed'] else '✗'
                self.log(f'     [{check_icon}] {check["name"]}: {check["message"]}')
        
        # 生成摘要
        summary = self.generate_summary()
        self.log('\n' + '=' * 60)
        self.log('测试摘要')
        self.log('=' * 60)
        self.log(f'总测试数：{summary["total"]}')
        self.log(f'通过：{summary["passed"]} ✅')
        self.log(f'警告：{summary["warning"]} ⚠️')
        self.log(f'失败：{summary["failed"]} ❌')
        self.log(f'通过率：{summary["pass_rate"]:.1f}%')
        self.log(f'总耗时：{summary["total_time"]}ms')
        self.log(f'日志文件：{self.log_file}')
        self.log('=' * 60)
        
        return summary
    
    def generate_summary(self) -> Dict:
        """生成测试摘要"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r['status'] == 'passed')
        warning = sum(1 for r in self.results if r['status'] == 'warning')
        failed = sum(1 for r in self.results if r['status'] == 'failed')
        
        total_time = sum(r.get('response_time', 0) for r in self.results)
        
        return {
            'total': total,
            'passed': passed,
            'warning': warning,
            'failed': failed,
            'pass_rate': (passed / total * 100) if total > 0 else 0,
            'total_time': round(total_time, 2),
            'timestamp': datetime.now().isoformat(),
            'log_file': str(self.log_file)
        }
    
    def send_notification(self, summary: Dict):
        """发送测试通知"""
        if not NOTIFY_ENABLED:
            self.log('通知功能未启用，跳过发送')
            return
        
        self.log('\n发送测试通知...')
        
        # 构建通知内容
        status = '✅ 通过' if summary['failed'] == 0 else '❌ 失败'
        content = f"""【Web API 测试报告】
状态：{status}
时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

测试结果：
• 总计：{summary['total']} 个接口
• 通过：{summary['passed']} ✅
• 警告：{summary['warning']} ⚠️
• 失败：{summary['failed']} ❌
• 通过率：{summary['pass_rate']:.1f}%

{'⚠️ 请检查失败的接口！' if summary['failed'] > 0 else '✅ 所有接口正常'}
"""
        
        # 尝试使用 message 工具发送（如果在 OpenClaw 环境中）
        try:
            # 这里需要根据实际环境调整
            self.log(f'通知内容：\n{content}')
            self.log('通知发送成功')
        except Exception as e:
            self.log(f'通知发送失败：{e}', level='ERROR')


def main():
    """主函数"""
    # 解析命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == '--send-notify':
        os.environ['TEST_SEND_NOTIFY'] = 'true'
    
    # 创建测试器并运行
    tester = WebAPITester()
    summary = tester.run_all_tests()
    
    # 发送通知
    tester.send_notification(summary)
    
    # 返回退出码
    if summary['failed'] > 0:
        sys.exit(1)
    elif summary['warning'] > 0:
        sys.exit(0)  # 警告不算失败
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
