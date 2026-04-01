"""
数据获取服务测试
"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'stock-agent' / 'services'))


class TestDataFetchers:
    """数据获取器测试类"""
    
    def test_market_data_fetcher_initialization(self):
        """测试市场数据获取器初始化"""
        from market_fetcher import MarketDataFetcher
        
        fetcher = MarketDataFetcher()
        assert fetcher is not None
        assert fetcher.data_dir.exists()
    
    def test_capital_flow_fetcher_initialization(self):
        """测试资金流获取器初始化"""
        from capital_fetcher import CapitalFlowFetcher
        
        fetcher = CapitalFlowFetcher()
        assert fetcher is not None
        assert fetcher.analyzer.tushare_pro is not None, "Tushare Pro 未连接"
    
    def test_ai_news_fetcher_initialization(self):
        """测试 AI 新闻获取器初始化"""
        from ai_news_fetcher import AINewsFetcher
        
        fetcher = AINewsFetcher()
        assert fetcher is not None
        assert fetcher.monitor is not None


class TestDataAvailability:
    """数据可用性测试"""
    
    def test_data_directory_exists(self, data_dir):
        """测试数据目录存在"""
        assert data_dir.exists(), f"数据目录不存在：{data_dir}"
    
    def test_market_data_dir_exists(self, data_dir):
        """测试市场数据目录存在"""
        market_dir = data_dir / 'market'
        assert market_dir.exists(), f"市场数据目录不存在：{market_dir}"
    
    def test_capital_data_dir_exists(self, data_dir):
        """测试资金流数据目录存在"""
        capital_dir = data_dir / 'capital'
        assert capital_dir.exists(), f"资金流数据目录不存在：{capital_dir}"
    
    def test_ai_news_data_dir_exists(self, data_dir):
        """测试 AI 新闻数据目录存在"""
        ai_news_dir = data_dir / 'ai_news'
        assert ai_news_dir.exists(), f"AI 新闻数据目录不存在：{ai_news_dir}"
    
    def test_aggregated_data_dir_exists(self, data_dir):
        """测试聚合数据目录存在"""
        agg_dir = data_dir / 'aggregated'
        assert agg_dir.exists(), f"聚合数据目录不存在：{agg_dir}"
