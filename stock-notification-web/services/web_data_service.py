#!/usr/bin/env python3
"""
Web 服务数据层
功能：从 stock-agent 数据存储层读取数据，为 Web 前端提供 API
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List


class WebDataService:
    """Web 数据服务"""
    
    def __init__(self, stock_agent_data_dir: str = None):
        if stock_agent_data_dir:
            self.data_dir = Path(stock_agent_data_dir)
        else:
            # 默认路径 - 使用公共数据目录（绝对路径）
            self.data_dir = Path('/home/admin/.openclaw/workspace/data/stock-agent')
        
        # 确保目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    # ========== 聚合数据 ==========
    
    def get_aggregated_data(self, trade_date: str = None) -> Optional[Dict]:
        """获取聚合数据"""
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        data_file = self.data_dir / 'aggregated' / f'{trade_date}.json'
        
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return None
    
    def get_latest_aggregated_data(self, days_back: int = 7) -> Optional[Dict]:
        """获取最新的聚合数据"""
        today = datetime.now()
        
        for i in range(days_back):
            date = today - timedelta(days=i)
            # 跳过周末
            if date.weekday() >= 5:
                continue
            
            trade_date = date.strftime('%Y%m%d')
            data = self.get_aggregated_data(trade_date)
            
            if data:
                return data
        
        return None
    
    # ========== 市场数据 ==========
    
    def get_market_data(self, trade_date: str = None) -> Optional[Dict]:
        """获取市场数据"""
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        data_file = self.data_dir / 'market' / f'{trade_date}.json'
        
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return None
    
    def get_indices(self, trade_date: str = None) -> Dict:
        """获取大盘指数"""
        data = self.get_market_data(trade_date)
        return data.get('indices', {}) if data else {}
    
    def get_top_list(self, trade_date: str = None) -> List:
        """获取龙虎榜"""
        data = self.get_market_data(trade_date)
        return data.get('top_list', []) if data else []
    
    # ========== 资金流数据 ==========
    
    def get_capital_data(self, trade_date: str = None) -> Optional[Dict]:
        """获取资金流数据"""
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        data_file = self.data_dir / 'capital' / f'{trade_date}.json'
        
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return None
    
    def get_sector_flows(self, trade_date: str = None, top_n: int = 10, sort_by: str = 'change_pct') -> List:
        """获取板块资金流 TOP N - 默认按涨幅排序"""
        data = self.get_capital_data(trade_date)
        sector_flows = data.get('sector_flows', []) if data else []
        
        # 🔥 修改：默认按涨幅排序（而不是按净流入）
        if sort_by == 'change_pct':
            sector_flows_sorted = sorted(sector_flows, key=lambda x: x.get('avg_change', 0), reverse=True)
        elif sort_by == 'flow':
            sector_flows_sorted = sorted(sector_flows, key=lambda x: x.get('net_flow', 0), reverse=True)
        else:
            sector_flows_sorted = sorted(sector_flows, key=lambda x: x.get('avg_change', 0), reverse=True)
        
        return sector_flows_sorted[:top_n]
    
    # ========== AI 新闻数据 ==========
    
    def get_ai_news_data(self, trade_date: str = None) -> Optional[Dict]:
        """获取 AI 新闻数据"""
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        data_file = self.data_dir / 'ai_news' / f'{trade_date}.json'
        
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return None
    
    def get_ai_news_sentiment(self, trade_date: str = None) -> Dict:
        """获取 AI 新闻情感分析"""
        data = self.get_ai_news_data(trade_date)
        return data.get('sentiment', {}) if data else {}
    
    def get_ai_news_list(self, trade_date: str = None, limit: int = 10) -> List:
        """获取 AI 新闻列表"""
        data = self.get_ai_news_data(trade_date)
        news = data.get('news', []) if data else []
        return news[:limit]
    
    # ========== 报告数据 ==========
    
    def get_report_json(self, report_type: str, trade_date: str = None) -> Optional[Dict]:
        """获取报告 JSON 数据"""
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        reports_dir = self.data_dir.parent / 'reports'
        
        if report_type == 'evening':
            filename = f'evening_summary_{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}.json'
        elif report_type == 'morning':
            filename = f'morning_recommend_{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}.json'
        elif report_type == 'monitor':
            filename = f'stock_monitor_{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}.json'
        else:
            return None
        
        filepath = reports_dir / filename
        
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return None
    
    # ========== Web 首页概览数据 ==========
    
    def get_dashboard_overview(self) -> Dict:
        """获取首页概览数据"""
        # 获取最新数据
        latest = self.get_latest_aggregated_data()
        
        if not latest:
            return {
                'status': 'no_data',
                'message': '暂无数据'
            }
        
        market = latest.get('market', {})
        capital = latest.get('capital', {})
        ai_news = latest.get('ai_news', {})
        
        # 计算市场情绪
        indices = market.get('indices', {})
        shanghai = indices.get('shanghai', {})
        change_pct = shanghai.get('change_pct', 0)
        
        if change_pct > 1:
            sentiment = '偏暖'
            sentiment_score = 7.0
        elif change_pct > 0:
            sentiment = '中性'
            sentiment_score = 5.5
        elif change_pct > -1:
            sentiment = '中性'
            sentiment_score = 4.5
        else:
            sentiment = '偏冷'
            sentiment_score = 3.0
        
        # 板块资金流
        sector_flows = capital.get('sector_flows', [])
        positive_sectors = sum(1 for s in sector_flows if s.get('net_flow', 0) > 0)
        total_net_flow = sum(s.get('net_flow', 0) for s in sector_flows)
        
        return {
            'status': 'ok',
            'trade_date': latest.get('trade_date', ''),
            'updated_at': latest.get('aggregated_at', ''),
            'market': {
                'shanghai': {
                    'close': shanghai.get('close', 0),
                    'change_pct': change_pct
                },
                'sentiment': sentiment,
                'sentiment_score': round(sentiment_score, 1)
            },
            'capital': {
                'sector_flows_top5': sector_flows[:5],
                'positive_sectors': positive_sectors,
                'total_net_flow': total_net_flow
            },
            'ai_news': {
                'count': len(ai_news.get('news', [])),
                'sentiment_score': ai_news.get('sentiment', {}).get('overall_score', 50)
            }
        }


# 单例模式
_service_instance = None

def get_web_data_service() -> WebDataService:
    """获取 Web 数据服务实例"""
    global _service_instance
    
    if _service_instance is None:
        _service_instance = WebDataService()
    
    return _service_instance
