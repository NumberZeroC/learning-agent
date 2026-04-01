#!/usr/bin/env python3
"""
数据聚合服务
功能：聚合所有数据源，提供统一的数据访问接口
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.market_fetcher import MarketDataFetcher
from services.capital_fetcher import CapitalFlowFetcher
from services.ai_news_fetcher import AINewsFetcher


class DataAggregator:
    """数据聚合器"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        self.config_path = config_path
        self.data_dir = Path('/home/admin/.openclaw/workspace/data/stock-notification')
        
        # 初始化获取器
        self.market_fetcher = MarketDataFetcher(config_path)
        self.capital_fetcher = CapitalFlowFetcher(config_path)
        self.ai_news_fetcher = AINewsFetcher(config_path)
    
    def fetch_all(self, trade_date: str = None) -> dict:
        """获取所有数据"""
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        print(f"\n{'='*70}")
        print(f"📊 数据聚合服务 - {trade_date}")
        print(f"{'='*70}")
        
        # 并行获取所有数据
        market_data = self.market_fetcher.fetch_all(trade_date)
        capital_data = self.capital_fetcher.fetch_all(trade_date)
        ai_news_data = self.ai_news_fetcher.fetch_all(trade_date)
        
        # 聚合数据
        aggregated = {
            'trade_date': trade_date,
            'aggregated_at': datetime.now().isoformat(),
            'market': market_data,
            'capital': capital_data,
            'ai_news': ai_news_data
        }
        
        # 保存聚合数据
        self._save_aggregated(trade_date, aggregated)
        
        print(f"\n✅ 数据聚合完成")
        print(f"📄 已保存：{self._get_aggregated_file(trade_date)}")
        
        return aggregated
    
    def load_all(self, trade_date: str = None) -> dict:
        """加载所有数据"""
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        # 尝试加载聚合数据
        aggregated_file = self._get_aggregated_file(trade_date)
        
        if aggregated_file.exists():
            with open(aggregated_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 如果聚合数据不存在，分别从各服务加载
        return {
            'trade_date': trade_date,
            'market': self.market_fetcher.load_data(trade_date),
            'capital': self.capital_fetcher.load_data(trade_date),
            'ai_news': self.ai_news_fetcher.load_data(trade_date)
        }
    
    def _get_aggregated_file(self, trade_date: str) -> Path:
        """获取聚合数据文件路径"""
        date_str = trade_date if len(trade_date) == 8 else trade_date.replace('-', '')
        return self.data_dir / 'aggregated' / f'{date_str}.json'
    
    def _save_aggregated(self, trade_date: str, data: dict):
        """保存聚合数据"""
        aggregated_dir = self.data_dir / 'aggregated'
        aggregated_dir.mkdir(parents=True, exist_ok=True)
        
        data_file = self._get_aggregated_file(trade_date)
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据聚合服务')
    parser.add_argument('--date', '-d', help='交易日期 (YYYYMMDD)')
    parser.add_argument('--config', '-c', default='config.yaml', help='配置文件')
    
    args = parser.parse_args()
    
    aggregator = DataAggregator(config_path=args.config)
    data = aggregator.fetch_all(args.date)
    
    print(f"\n📊 数据摘要:")
    print(f"   市场数据：{len(data.get('market', {}).get('indices', {}))} 个指数")
    print(f"   资金流：{len(data.get('capital', {}).get('sector_flows', []))} 个板块")
    print(f"   AI 新闻：{len(data.get('ai_news', {}).get('news', []))} 条")


if __name__ == '__main__':
    main()
