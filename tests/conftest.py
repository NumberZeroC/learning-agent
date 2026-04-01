"""
pytest 配置文件
"""
import pytest
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'stock-agent' / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'stock-agent' / 'services'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'stock-agent-web'))


@pytest.fixture
def data_dir():
    """数据目录路径"""
    return Path('/home/admin/.openclaw/workspace/data/stock-agent')


@pytest.fixture
def today():
    """今日日期"""
    from datetime import datetime
    return datetime.now().strftime('%Y%m%d')


@pytest.fixture
def web_api_base():
    """Web API 基础 URL"""
    return 'http://localhost:5000/api/v1'
