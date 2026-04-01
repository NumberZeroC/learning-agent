"""
选股功能 API
"""
from flask import jsonify, request, current_app
from api.v1 import api_v1_blueprint
from services.stock_service import StockService
from datetime import datetime


@api_v1_blueprint.route('/stocks/recommend', methods=['GET'])
def get_recommendations():
    """
    获取选股推荐
    
    Query Params:
        date: 日期 (YYYY-MM-DD)，默认今日
        limit: 返回板块数量，默认 5
        per_sector: 每板块推荐股票数，默认 5
    """
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    limit = request.args.get('limit', 5, type=int)
    per_sector = request.args.get('per_sector', 5, type=int)
    
    try:
        service = StockService(current_app.config)
        result = service.get_recommendations(date, limit, per_sector)
        
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


@api_v1_blueprint.route('/stocks/sentiment', methods=['GET'])
def get_market_sentiment():
    """
    获取市场情绪
    
    Query Params:
        date: 日期，默认今日
    """
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    try:
        service = StockService(current_app.config)
        result = service.get_market_sentiment(date)
        
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


@api_v1_blueprint.route('/stocks/sectors/rank', methods=['GET'])
def get_sectors_rank():
    """
    获取板块排名
    
    Query Params:
        date: 日期
        limit: 返回数量，默认 10
        sort_by: 排序字段 (score/flow/news)
    """
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    limit = request.args.get('limit', 10, type=int)
    sort_by = request.args.get('sort_by', 'score')
    
    try:
        service = StockService(current_app.config)
        result = service.get_sectors_rank(date, limit, sort_by)
        
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


@api_v1_blueprint.route('/stocks/<code>/detail', methods=['GET'])
def get_stock_detail(code):
    """
    获取个股详情
    
    Path Params:
        code: 股票代码
    """
    try:
        service = StockService(current_app.config)
        result = service.get_stock_detail(code)
        
        if not result:
            return jsonify({
                'code': 404,
                'message': '股票不存在',
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
