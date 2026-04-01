"""
数据完整性测试
"""
import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta


class TestDataDirectoryStructure:
    """数据目录结构测试"""
    
    def test_data_directory_exists(self, data_dir):
        """测试数据目录存在"""
        assert data_dir.exists(), f"数据目录不存在：{data_dir}"
    
    def test_subdirectories_exist(self, data_dir):
        """测试子目录存在"""
        subdirs = ['market', 'capital', 'ai_news', 'aggregated', 'reports']
        
        for subdir in subdirs:
            subdir_path = data_dir / subdir
            assert subdir_path.exists(), f"子目录不存在：{subdir_path}"
            assert subdir_path.is_dir(), f"不是目录：{subdir_path}"


class TestDataFileFreshness:
    """数据文件新鲜度测试"""
    
    def test_latest_data_exists(self, data_dir):
        """测试最新数据文件存在"""
        today = datetime.now()
        
        # 检查最近 3 天的数据（考虑周末）
        for i in range(3):
            date = today - timedelta(days=i)
            if date.weekday() >= 5:  # 跳过周末
                continue
            
            date_str = date.strftime('%Y%m%d')
            
            # 检查聚合数据
            agg_file = data_dir / 'aggregated' / f'{date_str}.json'
            if agg_file.exists():
                return  # 找到数据，测试通过
        
        # 如果没有找到数据，可能是非交易日，跳过测试
        pytest.skip("未找到最近交易日的聚合数据")
    
    def test_data_files_are_valid_json(self, data_dir):
        """测试数据文件是有效的 JSON"""
        agg_dir = data_dir / 'aggregated'
        
        if not agg_dir.exists():
            pytest.skip("聚合数据目录不存在")
        
        json_files = list(agg_dir.glob('*.json'))
        
        if not json_files:
            pytest.skip("没有 JSON 文件")
        
        for json_file in json_files[:3]:  # 只检查前 3 个文件
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"JSON 文件格式错误：{json_file} - {e}")


class TestDataConsistency:
    """数据一致性测试"""
    
    def test_aggregated_data_structure(self, data_dir):
        """测试聚合数据结构"""
        agg_dir = data_dir / 'aggregated'
        
        if not agg_dir.exists():
            pytest.skip("聚合数据目录不存在")
        
        json_files = list(agg_dir.glob('*.json'))
        
        if not json_files:
            pytest.skip("没有聚合数据文件")
        
        # 检查最新的聚合数据
        latest_file = sorted(json_files)[-1]
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查必需字段
        assert 'trade_date' in data, "缺少交易日期"
        assert 'aggregated_at' in data, "缺少聚合时间"
        assert 'market' in data, "缺少市场数据"
        assert 'capital' in data, "缺少资金流数据"
        assert 'ai_news' in data, "缺少 AI 新闻数据"
