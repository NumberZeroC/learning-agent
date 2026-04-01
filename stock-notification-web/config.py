"""
Stock-Agent Web 配置文件
"""
import os
from datetime import timedelta

class Config:
    """基础配置"""
    # 基础路径
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    STOCK_AGENT_DIR = os.path.join(os.path.dirname(BASE_DIR), 'stock-agent')
    WORKSPACE_DIR = os.path.dirname(BASE_DIR)  # workspace 根目录
    
    # 数据目录 - 使用公共数据目录（绝对路径）
    DATA_DIR = '/home/admin/.openclaw/workspace/data/stock-agent'
    REPORTS_DIR = os.path.join(DATA_DIR, 'reports')
    LOGS_DIR = os.path.join(STOCK_AGENT_DIR, 'logs')
    
    # 配置文件
    CONFIG_FILE = os.path.join(STOCK_AGENT_DIR, 'config.yaml')
    
    # Flask 配置
    SECRET_KEY = os.environ.get('SECRET_KEY', 'stock-agent-secret-key-2026')
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # API 配置
    API_VERSION = 'v1'
    API_PREFIX = f'/api/{API_VERSION}'
    
    # 缓存配置
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 分钟
    
    # 跨域配置
    CORS_ORIGINS = ['*']
    
    # 分页配置
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = os.path.join(LOGS_DIR, 'web.log')


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LOG_LEVEL = 'INFO'


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
