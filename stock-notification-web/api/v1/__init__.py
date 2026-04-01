"""
API v1 初始化
"""
from flask import Blueprint

api_v1_blueprint = Blueprint('api_v1', __name__)

# 导入路由（避免循环导入）
from api.v1 import stocks, monitor, config_routes, report_routes, data_routes
