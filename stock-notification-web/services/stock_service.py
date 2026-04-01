"""
选股服务 - 处理选股相关逻辑
"""
import os
import json
import glob
from datetime import datetime
from pathlib import Path


class StockService:
    """选股服务"""
    
    def __init__(self, config):
        self.config = config
        self.reports_dir = config['REPORTS_DIR']
    
    def get_recommendations(self, date, limit=5, per_sector=5):
        """
        获取选股推荐
        
        Args:
            date: 日期 (YYYY-MM-DD)
            limit: 返回板块数量
            per_sector: 每板块推荐股票数
        
        Returns:
            dict: 推荐数据
        """
        # 查找推荐报告
        report_file = self._find_report('recommendation', date)
        
        if report_file:
            # 从 JSON 文件读取
            json_file = report_file.replace('.md', '.json')
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data
        
        # 如果没有报告，返回空数据
        return {
            'date': date,
            'market_sentiment': {
                'score': 5.0,
                'level': '中性',
                'description': '暂无数据'
            },
            'hot_sectors': []
        }
    
    def get_market_sentiment(self, date):
        """获取市场情绪"""
        # 从晚间分析报告获取
        report_file = self._find_report('evening_analysis', date)
        
        if report_file:
            json_file = report_file.replace('.md', '.json')
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 计算市场情绪
                sectors = data.get('sector_benefits', {})
                if sectors:
                    avg_score = sum(s.get('benefit_score', 0) for s in sectors.values()) / len(sectors)
                else:
                    avg_score = 5.0
                
                level = '偏暖' if avg_score > 6 else '中性' if avg_score > 4 else '偏冷'
                
                return {
                    'date': date,
                    'overall_score': round(avg_score, 1),
                    'level': level,
                    'components': {
                        'news_sentiment': {
                            'score': round(avg_score, 1),
                            'news_count': data.get('news_count', 0)
                        }
                    },
                    'suggestion': f'市场情绪{level}，建议适度操作'
                }
        
        return {
            'date': date,
            'overall_score': 5.0,
            'level': '中性',
            'components': {},
            'suggestion': '暂无数据'
        }
    
    def get_sectors_rank(self, date, limit=10, sort_by='change_pct'):
        """获取板块排名 - 默认按涨幅排序"""
        report_file = self._find_report('evening_analysis', date)
        
        if report_file:
            json_file = report_file.replace('.md', '.json')
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 🔥 新格式：从 sector_flows 获取（已按涨幅排序）
                sector_flows = data.get('sector_flows', [])
                sector_sentiment = data.get('sector_sentiment', {})
                
                if sector_flows:
                    sector_list = []
                    for info in sector_flows:
                        sector = info.get('sector', '')
                        sentiment_info = sector_sentiment.get(sector, {})
                        
                        sector_list.append({
                            'rank': 0,
                            'sector_name': sector,
                            'change_pct': info.get('avg_change', 0),
                            'net_flow': info.get('net_flow', 0),
                            'capital_inflow': info.get('main_force_in', 0),
                            'news_count': sentiment_info.get('news_count', 0),
                            'sentiment_score': sentiment_info.get('score', 0)
                        })
                    
                    # 排序：默认按涨幅，也支持其他排序方式
                    if sort_by == 'change_pct':
                        sector_list.sort(key=lambda x: x['change_pct'], reverse=True)
                    elif sort_by == 'flow':
                        sector_list.sort(key=lambda x: x['net_flow'], reverse=True)
                    elif sort_by == 'news':
                        sector_list.sort(key=lambda x: x['news_count'], reverse=True)
                    
                    # 添加排名
                    for i, sector in enumerate(sector_list[:limit], 1):
                        sector['rank'] = i
                    
                    return {
                        'date': date,
                        'sectors': sector_list[:limit]
                    }
                
                # 旧格式兼容：从 sector_benefits 获取
                sectors = data.get('sector_benefits', {})
                if sectors:
                    sector_list = []
                    for name, info in sectors.items():
                        sector_list.append({
                            'rank': 0,
                            'sector_name': name,
                            'benefit_score': info.get('benefit_score', 0),
                            'level': self._get_benefit_level(info.get('benefit_score', 0)),
                            'news_count': info.get('news_count', 0),
                            'capital_inflow': 0,
                            'change_pct': 0
                        })
                    
                    # 排序
                    if sort_by == 'score':
                        sector_list.sort(key=lambda x: x['benefit_score'], reverse=True)
                    elif sort_by == 'news':
                        sector_list.sort(key=lambda x: x['news_count'], reverse=True)
                    
                    # 添加排名
                    for i, sector in enumerate(sector_list[:limit], 1):
                        sector['rank'] = i
                    
                    return {
                        'date': date,
                        'sectors': sector_list[:limit]
                    }
        
        return {'date': date, 'sectors': []}
    
    def get_stock_detail(self, code):
        """获取个股详情"""
        # 从监控报告或推荐报告中查找
        # 简化实现，返回基础信息
        return {
            'code': code,
            'name': '',
            'sector': '',
            'price': 0,
            'change_pct': 0,
            'recommendation': {
                'score': 5.0,
                'signal': 'HOLD',
                'reason': '暂无数据'
            }
        }
    
    def _find_report(self, prefix, date):
        """查找报告文件"""
        # 尝试不同格式
        patterns = [
            f'{prefix}_{date}.md',
            f'{prefix}_{date.replace("-", "")}*.md',
            f'{prefix}_*.md'
        ]
        
        for pattern in patterns:
            files = glob.glob(os.path.join(self.reports_dir, pattern))
            if files:
                return sorted(files)[-1]  # 返回最新的
        
        return None
    
    def _get_benefit_level(self, score):
        """获取利好程度"""
        if score > 8:
            return '重大利好'
        elif score > 5:
            return '利好'
        elif score > 3:
            return '小幅利好'
        else:
            return '中性'
