"""
监控功能 API
"""
from flask import jsonify, request, current_app
from api.v1 import api_v1_blueprint
from services.monitor_service import MonitorService
from datetime import datetime


@api_v1_blueprint.route('/monitor/stocks', methods=['GET'])
def get_monitor_stocks():
    """
    获取持仓监控列表
    
    Query Params:
        date: 日期
        signal: 筛选信号 (BUY/HOLD/SELL)
    """
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    signal = request.args.get('signal', None)
    
    try:
        service = MonitorService(current_app.config)
        result = service.get_monitor_stocks(date, signal)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': None
        }), 500


@api_v1_blueprint.route('/monitor/stocks/<code>', methods=['GET'])
def get_monitor_stock_detail(code):
    """
    获取单只股票监控详情
    
    Path Params:
        code: 股票代码
    """
    try:
        service = MonitorService(current_app.config)
        result = service.get_stock_detail(code)
        
        if not result:
            return jsonify({
                'code': 404,
                'message': '股票不存在或未监控',
                'data': None
            }), 404
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': None
        }), 500


@api_v1_blueprint.route('/monitor/report', methods=['GET'])
def get_monitor_report():
    """
    获取监控报告
    
    Query Params:
        date: 日期
    """
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    try:
        service = MonitorService(current_app.config)
        result = service.get_monitor_report(date)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': None
        }), 500


@api_v1_blueprint.route('/monitor/history', methods=['GET'])
def get_monitor_history():
    """
    获取历史监控记录
    
    Query Params:
        code: 股票代码 (必填)
        start_date: 开始日期
        end_date: 结束日期
        limit: 返回数量，默认 30
    """
    code = request.args.get('code')
    if not code:
        return jsonify({
            'code': 400,
            'message': '缺少参数：code',
            'data': None
        }), 400
    
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    limit = request.args.get('limit', 30, type=int)
    
    try:
        service = MonitorService(current_app.config)
        result = service.get_history(code, start_date, end_date, limit)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': None
        }), 500
