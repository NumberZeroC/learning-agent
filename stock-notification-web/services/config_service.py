"""
配置服务 - 处理配置相关逻辑
"""
import os
import yaml
import glob
from datetime import datetime


class ConfigService:
    """配置服务"""
    
    def __init__(self, config):
        self.config = config
        self.config_file = config['CONFIG_FILE']
        self.logs_dir = config['LOGS_DIR']
    
    def get_config(self):
        """获取配置"""
        if not os.path.exists(self.config_file):
            return {}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                full_config = yaml.safe_load(f)
            
            # 提取相关配置
            return {
                'monitor_stocks': full_config.get('monitor_stocks', {}),
                'recommendation': {
                    'sectors': full_config.get('sectors', []),
                    'capital_flow_threshold': full_config.get('capital_flow', {}).get('threshold_inflow', 5000),
                    'per_sector_limit': 5
                },
                'signals': full_config.get('monitor_stocks', {}).get('signals', {
                    'strong_buy': 8.0,
                    'buy': 6.5,
                    'hold': 4.5,
                    'sell': 3.0,
                    'strong_sell': 1.5
                }),
                'risk_alerts': full_config.get('monitor_stocks', {}).get('risk_alerts', {
                    'enabled': True,
                    'overbought_kdj': 80,
                    'overbought_rsi': 70
                }),
                'schedule': {
                    'morning_time': '09:30',
                    'monitor_interval': 300,
                    'evening_time': '20:00'
                }
            }
        except Exception as e:
            return {}
    
    def update_config(self, data):
        """更新配置"""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"配置文件不存在：{self.config_file}")
        
        updated_fields = []
        
        # 读取现有配置
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 更新监控股票
        if 'monitor_stocks' in data:
            if 'monitor_stocks' not in config:
                config['monitor_stocks'] = {}
            config['monitor_stocks']['stocks'] = data['monitor_stocks'].get('stocks', [])
            updated_fields.append('monitor_stocks.stocks')
        
        # 更新推荐配置
        if 'recommendation' in data:
            if 'capital_flow_threshold' in data['recommendation']:
                if 'capital_flow' not in config:
                    config['capital_flow'] = {}
                config['capital_flow']['threshold_inflow'] = data['recommendation']['capital_flow_threshold']
                updated_fields.append('recommendation.capital_flow_threshold')
        
        # 更新信号阈值
        if 'signals' in data:
            if 'monitor_stocks' not in config:
                config['monitor_stocks'] = {}
            if 'signals' not in config['monitor_stocks']:
                config['monitor_stocks']['signals'] = {}
            
            for key, value in data['signals'].items():
                config['monitor_stocks']['signals'][key] = value
                updated_fields.append(f'signals.{key}')
        
        # 保存配置
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        
        return updated_fields
    
    def add_monitor_stock(self, code, name=''):
        """添加监控股票"""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"配置文件不存在：{self.config_file}")
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if 'monitor_stocks' not in config:
            config['monitor_stocks'] = {'stocks': []}
        
        # 检查是否已存在
        stocks = config['monitor_stocks'].get('stocks', [])
        if any(s.get('code') == code for s in stocks):
            raise ValueError(f"股票 {code} 已在监控列表中")
        
        # 添加
        stocks.append({'code': code, 'name': name})
        config['monitor_stocks']['stocks'] = stocks
        
        # 保存
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    def remove_monitor_stock(self, code):
        """删除监控股票"""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"配置文件不存在：{self.config_file}")
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if 'monitor_stocks' not in config:
            return
        
        # 删除
        stocks = config['monitor_stocks'].get('stocks', [])
        config['monitor_stocks']['stocks'] = [s for s in stocks if s.get('code') != code]
        
        # 保存
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    def get_schedule_status(self):
        """获取定时任务状态"""
        # 从 crontab 读取
        tasks = []
        
        try:
            import subprocess
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                
                for line in lines:
                    if 'stock-agent' in line and not line.startswith('#'):
                        parts = line.split()
                        if len(parts) >= 6:
                            schedule = ' '.join(parts[:5])
                            command = ' '.join(parts[5:])
                            
                            # 解析任务类型
                            if 'morning' in command:
                                name = '早盘推荐'
                            elif 'monitor' in command:
                                name = '持仓监控'
                            elif 'evening' in command:
                                name = '晚间分析'
                            else:
                                name = '未知任务'
                            
                            tasks.append({
                                'name': name,
                                'schedule': schedule,
                                'command': command,
                                'last_run': self._get_last_run_time(command),
                                'last_status': 'success',
                                'next_run': '待计算'
                            })
        except:
            pass
        
        return {'tasks': tasks}
    
    def _get_last_run_time(self, command):
        """获取最后执行时间（从日志文件）"""
        # 简化实现
        return '未知'
