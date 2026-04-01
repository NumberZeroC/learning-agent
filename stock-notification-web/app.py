"""
Stock-Agent Web - Flask 应用入口
"""
import os
import sys
from flask import Flask, jsonify, render_template, send_from_directory
from flask_cors import CORS

# 添加 stock-agent 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stock-agent', 'src'))

from config import config
from api.v1 import api_v1_blueprint
from api.v1 import report_routes  # 注册报告 API
from services import init_services


def create_app(config_name=None):
    """应用工厂函数"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 添加缓存控制头
    @app.after_request
    def add_cache_headers(response):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    # 初始化扩展
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # 初始化服务
    init_services(app)
    
    # 注册蓝图
    app.register_blueprint(api_v1_blueprint, url_prefix=app.config['API_PREFIX'])
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 注册路由
    register_routes(app)
    
    return app


def register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'code': 404,
            'message': '资源不存在',
            'data': None
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'code': 400,
            'message': '请求参数错误',
            'data': None
        }), 400


def register_routes(app):
    """注册页面路由"""
    
    @app.route('/')
    def index():
        """首页"""
        return render_template('index.html')
    
    @app.route('/reports')
    def reports():
        """报告列表页"""
        return render_template('reports.html')
    
    @app.route('/report/<report_type>/<filename>')
    def report_detail(report_type, filename):
        """报告详情页"""
        return render_template('report_detail.html', 
                             report_type=report_type, 
                             filename=filename)
    
    @app.route('/read/<path:filename>')
    def read_report(filename):
        """在线阅读 MD 报告"""
        reports_dir = app.config.get('REPORTS_DIR', '/home/admin/.openclaw/workspace/stock-agent/data/reports')
        filepath = os.path.join(reports_dir, filename)
        
        if not os.path.exists(filepath):
            return jsonify({
                'code': 404,
                'message': '报告文件不存在',
                'data': None
            }), 404
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return render_template('report_read.html', 
                                 filename=filename,
                                 content=content)
        except Exception as e:
            return jsonify({
                'code': 500,
                'message': str(e),
                'data': None
            }), 500
    
    @app.route('/dashboard')
    def dashboard():
        """数据看板"""
        return render_template('dashboard.html')
    
    @app.route('/monitor')
    def monitor():
        """监控页面"""
        return render_template('monitor.html')
    
    @app.route('/settings')
    def settings():
        """配置页面"""
        return render_template('settings.html')
    
    @app.route('/test-links')
    def test_links():
        """链接测试页面"""
        return render_template('test_links.html')
    
    @app.route('/data/reports/<path:filename>')
    def serve_report(filename):
        """提供报告文件"""
        return send_from_directory(app.config['REPORTS_DIR'], filename)


# 创建应用实例
app = create_app()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
