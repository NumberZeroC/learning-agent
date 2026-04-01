"""
服务层初始化
"""
import os
import sys

# 添加 stock-agent 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'stock-agent', 'src'))


def init_services(app):
    """初始化服务"""
    # 确保数据目录存在
    os.makedirs(app.config['DATA_DIR'], exist_ok=True)
    os.makedirs(app.config['REPORTS_DIR'], exist_ok=True)
    os.makedirs(app.config['LOGS_DIR'], exist_ok=True)
    
    # 初始化 Web 数据服务
    from services.web_data_service import get_web_data_service
    data_service = get_web_data_service()
    app.data_service = data_service
    
    # 可以在这里初始化全局服务对象
    app.logger.info(f"Stock-Agent Web 启动")
    app.logger.info(f"数据目录：{app.config['DATA_DIR']}")
    app.logger.info(f"报告目录：{app.config['REPORTS_DIR']}")
    app.logger.info(f"Web 数据服务：已初始化")
