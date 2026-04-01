"""
监控服务 - 处理监控相关逻辑
"""
import os
import json
import glob
import yaml
import re
from datetime import datetime
from pathlib import Path


class MonitorService:
    """监控服务"""
    
    def __init__(self, config):
        self.config = config
        self.reports_dir = config['REPORTS_DIR']
        self.config_file = config['CONFIG_FILE']
    
    def get_monitor_stocks(self, date, signal=None):
        """获取持仓监控列表"""
        # 从配置文件获取股票列表
        stocks = self._get_monitor_stocks_from_config()
        
        # 从监控报告获取数据（优先从 monitor 子目录）
        report_file = self._find_report('stock_monitor', date)
        if not report_file:
            report_file = self._find_report('analysis', date)
        
        report_data = {}
        report_time = None
        
        if report_file:
            # 尝试读取 JSON 版本
            json_file = report_file.replace('.md', '.json')
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
            # 否则解析 MD 文件
            elif os.path.exists(report_file):
                report_data, report_time = self._parse_monitor_md(report_file)
        
        # 合并数据
        results = []
        summary = {'buy': 0, 'hold': 0, 'sell': 0}
        
        for stock in stocks:
            code = stock.get('code')
            name = stock.get('name', '')
            
            # 从报告获取数据
            stock_data = self._get_stock_from_report(report_data, code)
            
            if stock_data:
                signal_code = stock_data.get('signal', 'HOLD')
            else:
                signal_code = 'HOLD'
            
            # 筛选
            if signal and signal_code != signal:
                continue
            
            results.append({
                'code': code,
                'name': name,
                'sector': stock_data.get('sector', ''),
                'price': stock_data.get('price', 0),
                'change_pct': stock_data.get('change_pct', 0),
                'signal': signal_code,
                'score': stock_data.get('score', 5.0),
                'action': self._signal_to_action(signal_code),
                'reason': stock_data.get('reason', ''),
                'target_price': stock_data.get('target_price', 0),
                'stop_loss': stock_data.get('stop_loss', 0),
                'risk_alerts': stock_data.get('risk_alerts', [])
            })
            
            # 统计
            if signal_code in ['BUY', 'STRONG_BUY']:
                summary['buy'] += 1
            elif signal_code in ['SELL', 'STRONG_SELL']:
                summary['sell'] += 1
            else:
                summary['hold'] += 1
        
        return {
            'update_time': report_time or datetime.now().isoformat(),
            'total': len(results),
            'summary': summary,
            'stocks': results
        }
    
    def get_stock_detail(self, code):
        """获取单只股票监控详情"""
        stocks = self._get_monitor_stocks_from_config()
        stock_info = next((s for s in stocks if s.get('code') == code), None)
        
        if not stock_info:
            return None
        
        # 从最新报告获取数据
        report_file = self._find_report('analysis', datetime.now().strftime('%Y-%m-%d'))
        stock_data = {}
        
        if report_file:
            json_file = report_file.replace('.md', '.json')
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                stock_data = self._get_stock_from_report(report_data, code)
        
        return {
            'code': code,
            'name': stock_info.get('name', ''),
            'sector': stock_data.get('sector', ''),
            'monitor_time': datetime.now().isoformat(),
            'quote': {
                'price': stock_data.get('price', 0),
                'change_pct': stock_data.get('change_pct', 0),
                'volume': 0,
                'turnover': 0
            },
            'signal': {
                'action_code': stock_data.get('signal', 'HOLD'),
                'action': self._signal_to_action(stock_data.get('signal', 'HOLD')),
                'score': stock_data.get('score', 5.0),
                'confidence': '中'
            },
            'suggestion': {
                'action': self._signal_to_action(stock_data.get('signal', 'HOLD')),
                'reason': stock_data.get('reason', ''),
                'target_price': stock_data.get('target_price', 0),
                'stop_loss': stock_data.get('stop_loss', 0),
                'position': '建议持有'
            },
            'risk_alerts': stock_data.get('risk_alerts', [])
        }
    
    def get_monitor_report(self, date):
        """获取监控报告"""
        report_file = self._find_report('analysis', date)
        
        if report_file:
            return {
                'date': date,
                'report_url': f'/data/reports/{os.path.basename(report_file)}',
                'summary': {
                    'total': 7,
                    'buy': 1,
                    'hold': 5,
                    'sell': 1
                },
                'top_gainers': [],
                'top_losers': [],
                'risk_stocks': []
            }
        
        return {
            'date': date,
            'report_url': None,
            'summary': {'total': 0, 'buy': 0, 'hold': 0, 'sell': 0}
        }
    
    def get_history(self, code, start_date=None, end_date=None, limit=30):
        """获取历史监控记录"""
        # 简化实现，返回模拟数据
        return {
            'code': code,
            'name': '',
            'records': []
        }
    
    def _get_monitor_stocks_from_config(self):
        """从配置文件获取监控股票列表"""
        if not os.path.exists(self.config_file):
            return []
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            monitor_config = config.get('monitor_stocks', {})
            return monitor_config.get('stocks', [])
        except:
            return []
    
    def _get_stock_from_report(self, report_data, code):
        """从报告获取股票数据"""
        stocks = report_data.get('stocks', [])
        return next((s for s in stocks if s.get('code') == code), {})
    
    def _parse_monitor_md(self, filepath):
        """解析监控 MD 报告文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            stocks = []
            report_time = None
            
            # 提取报告时间
            time_match = re.search(r'生成时间：(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', content)
            if time_match:
                report_time = datetime.strptime(time_match.group(1), '%Y-%m-%d %H:%M:%S').isoformat()
            
            # 分割股票块
            blocks = content.split('## ')[1:]  # 跳过标题
            
            for block in blocks:
                lines = block.strip().split('\n')
                if not lines:
                    continue
                
                # 解析股票名称和代码
                header = lines[0]
                name_code_match = re.match(r'(.+?)\((\d+)\)', header)
                if not name_code_match:
                    continue
                
                name = name_code_match.group(1).strip()
                code = name_code_match.group(2)
                
                stock_data = {
                    'code': code,
                    'name': name,
                    'price': 0,
                    'change_pct': 0,
                    'signal': 'HOLD',
                    'score': 5.0,
                    'reason': '',
                    'target_price': 0,
                    'stop_loss': 0,
                    'risk_alerts': []
                }
                
                for line in lines[1:]:
                    if '当前价格' in line:
                        price_match = re.search(r'\*\*当前价格\*\*: ([\d.]+)\s*\(([\+\-][\d.]+)%\)', line)
                        if price_match:
                            stock_data['price'] = float(price_match.group(1))
                            stock_data['change_pct'] = float(price_match.group(2))
                    elif '操作建议' in line:
                        if '强烈卖出' in line or '建议卖出' in line:
                            stock_data['signal'] = 'STRONG_SELL'
                            stock_data['score'] = 1.0
                        elif '建议减仓' in line:
                            stock_data['signal'] = 'SELL'
                            stock_data['score'] = 3.0
                        elif '建议加仓' in line:
                            stock_data['signal'] = 'STRONG_BUY'
                            stock_data['score'] = 8.0
                        elif '建议买入' in line:
                            stock_data['signal'] = 'BUY'
                            stock_data['score'] = 7.0
                    elif '综合得分' in line:
                        score_match = re.search(r'\*\*综合得分\*\*: ([\d.]+)/', line)
                        if score_match:
                            stock_data['score'] = float(score_match.group(1))
                    elif '目标价' in line:
                        target_match = re.search(r'\*\*目标价\*\*: ([\d.]+)', line)
                        if target_match:
                            stock_data['target_price'] = float(target_match.group(1))
                    elif '止损价' in line:
                        stop_match = re.search(r'\*\*止损价\*\*: ([\d.]+)', line)
                        if stop_match:
                            stock_data['stop_loss'] = float(stop_match.group(1))
                    elif '⚠️' in line:
                        stock_data['risk_alerts'].append(line.replace('⚠️', '').strip())
                
                stocks.append(stock_data)
            
            return {'stocks': stocks}, report_time
        except Exception as e:
            print(f"解析 MD 报告失败：{e}")
            return {}, None
    
    def _find_report(self, prefix, date):
        """查找报告文件"""
        # 先在主目录查找
        patterns = [
            f'{prefix}_{date}.md',
            f'{prefix}_{date.replace("-", "")}*.md',
            f'{prefix}_*.md'
        ]
        
        for pattern in patterns:
            files = glob.glob(os.path.join(self.reports_dir, pattern))
            if files:
                return sorted(files)[-1]
        
        # 在 monitor 子目录查找
        monitor_dir = os.path.join(self.reports_dir, 'monitor')
        if os.path.isdir(monitor_dir):
            patterns = [
                f'stock_monitor_{date.replace("-", "")}*.md',
                f'stock_monitor_*.md'
            ]
            for pattern in patterns:
                files = glob.glob(os.path.join(monitor_dir, pattern))
                if files:
                    return sorted(files)[-1]
        
        return None
    
    def _signal_to_action(self, signal):
        """信号转换为操作建议"""
        mapping = {
            'STRONG_BUY': '建议加仓',
            'BUY': '建议买入',
            'HOLD': '继续持有',
            'SELL': '建议减仓',
            'STRONG_SELL': '建议卖出'
        }
        return mapping.get(signal, '继续持有')
