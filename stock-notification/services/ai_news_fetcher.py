#!/usr/bin/env python3
"""
AI 新闻数据获取服务
功能：获取 AI 行业新闻、情感分析
存储：data/ai_news/YYYY-MM-DD.json
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai_news_monitor import AINewsMonitor


class AINewsFetcher:
    """AI 新闻数据获取器"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        self.config = self._load_config(config_path)
        self.data_dir = Path('/home/admin/.openclaw/workspace/data/stock-notification') / 'ai_news'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化监控器
        akshare_config = self.config.get('akshare', {})
        self.monitor = AINewsMonitor(
            cache_dir=akshare_config.get('cache_dir'),
            cache_ttl=600
        )
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        import yaml
        config_file = Path(config_path)
        if not config_file.exists():
            config_file = Path(__file__).parent.parent / config_file
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def fetch_news(self, limit_sources: int = 8) -> list:
        """获取 AI 新闻"""
        print(f"\n🤖 获取 AI 行业新闻...")
        
        news = self.monitor.fetch_all_news(limit_sources=limit_sources)
        
        print(f"   ✅ 获取 {len(news)} 条新闻")
        
        return news
    
    def analyze_sentiment(self, news: list) -> dict:
        """分析新闻情感"""
        print(f"\n📊 分析情感...")
        
        sentiment = self.monitor.analyze_news_sentiment(news)
        
        print(f"   📊 情感得分：{sentiment['overall_score']} ({sentiment['overall_emoji']} {sentiment['overall_level']})")
        
        return sentiment
    
    def fetch_all(self, trade_date: str = None) -> dict:
        """获取所有 AI 新闻数据"""
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        print(f"\n{'='*60}")
        print(f"🤖 AI 新闻数据获取 - {trade_date}")
        print(f"{'='*60}")
        
        # 获取新闻
        news = self.fetch_news()
        
        # 分析情感
        sentiment = self.analyze_sentiment(news)
        
        data = {
            'trade_date': trade_date,
            'fetched_at': datetime.now().isoformat(),
            'news': news,
            'sentiment': sentiment
        }
        
        # 保存到文件
        self._save_data(trade_date, data)
        
        print(f"\n✅ AI 新闻数据获取完成")
        print(f"📄 已保存：{self._get_data_file(trade_date)}")
        
        return data
    
    def _get_data_file(self, trade_date: str) -> Path:
        """获取数据文件路径"""
        date_str = trade_date if len(trade_date) == 8 else trade_date.replace('-', '')
        return self.data_dir / f'{date_str}.json'
    
    def _save_data(self, trade_date: str, data: dict):
        """保存数据到文件"""
        data_file = self._get_data_file(trade_date)
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_data(self, trade_date: str = None) -> dict:
        """加载已存储的数据"""
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        data_file = self._get_data_file(trade_date)
        
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {}


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI 新闻数据获取服务')
    parser.add_argument('--date', '-d', help='交易日期 (YYYYMMDD)')
    parser.add_argument('--config', '-c', default='config.yaml', help='配置文件')
    parser.add_argument('--limit', '-l', type=int, default=8, help='新闻源数量限制')
    
    args = parser.parse_args()
    
    fetcher = AINewsFetcher(config_path=args.config)
    data = fetcher.fetch_all(args.date)
    
    print(f"\n🤖 数据摘要:")
    print(f"   新闻数量：{len(data.get('news', []))}")
    print(f"   情感得分：{data.get('sentiment', {}).get('overall_score', 0)}")
    print(f"   热点话题：{', '.join(data.get('sentiment', {}).get('hot_topics', [])[:3])}")


if __name__ == '__main__':
    main()
