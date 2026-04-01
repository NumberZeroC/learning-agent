"""
Web API 测试
"""
import pytest
import requests


class TestWebAPI:
    """Web API 测试类"""
    
    def test_api_root(self, web_api_base):
        """测试 API 根路径"""
        response = requests.get(f'{web_api_base}/data/overview', timeout=10)
        assert response.status_code == 200
    
    def test_data_overview_api(self, web_api_base):
        """测试首页概览 API"""
        response = requests.get(f'{web_api_base}/data/overview', timeout=10)
        
        assert response.status_code == 200
        data = response.json()['data']
        
        assert 'market' in data, "缺少市场数据"
        assert 'capital' in data, "缺少资金流数据"
        assert 'ai_news' in data, "缺少 AI 新闻数据"
        
        # 检查市场数据
        assert 'shanghai' in data['market']
        assert 'close' in data['market']['shanghai']
        assert 'change_pct' in data['market']['shanghai']
    
    def test_sector_flows_api(self, web_api_base):
        """测试板块资金流 API"""
        response = requests.get(f'{web_api_base}/data/capital/sectors', timeout=10)
        
        assert response.status_code == 200
        data = response.json()['data']['sector_flows']
        
        assert len(data) > 0, "板块资金流数据为空"
        assert 'sector' in data[0], "缺少板块名称"
        assert 'net_flow' in data[0], "缺少净流入数据"
    
    def test_ai_news_api(self, web_api_base):
        """测试 AI 新闻 API"""
        response = requests.get(f'{web_api_base}/data/ai-news', timeout=10)
        
        assert response.status_code == 200
        data = response.json()['data']
        
        assert 'news' in data, "缺少新闻数据"
        assert 'sentiment' in data, "缺少情感分析数据"
        
        if len(data['news']) > 0:
            assert 'title' in data['news'][0], "缺少新闻标题"
    
    def test_reports_api(self, web_api_base):
        """测试报告 API"""
        response = requests.get(f'{web_api_base}/reports', timeout=10)
        
        assert response.status_code == 200
        data = response.json()['data']
        
        assert isinstance(data, list), "报告列表应该是数组"
    
    def test_latest_data_api(self, web_api_base):
        """测试最新数据 API"""
        response = requests.get(f'{web_api_base}/data/latest', timeout=10)
        
        # 404 表示没有数据，200 表示有数据
        assert response.status_code in [200, 404]
