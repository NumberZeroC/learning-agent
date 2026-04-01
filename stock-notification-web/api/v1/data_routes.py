"""
数据 API - 从 stock-agent 数据存储层读取数据
"""

import os
import sys
from flask import jsonify, current_app, request
from api.v1 import api_v1_blueprint

# 添加服务路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))
from services.web_data_service import get_web_data_service


@api_v1_blueprint.route('/data/overview', methods=['GET'])
def get_data_overview():
    """获取首页概览数据"""
    try:
        service = get_web_data_service()
        data = service.get_dashboard_overview()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': data
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': {}
        }), 500


@api_v1_blueprint.route('/data/market', methods=['GET'])
def get_market_data():
    """获取市场数据"""
    try:
        trade_date = request.args.get('date')
        service = get_web_data_service()
        
        data = service.get_market_data(trade_date)
        
        if not data:
            return jsonify({
                'code': 404,
                'message': '未找到市场数据',
                'data': {}
            }), 404
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': data
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': {}
        }), 500


@api_v1_blueprint.route('/data/capital/sectors', methods=['GET'])
def get_sector_flows():
    """获取板块资金流"""
    try:
        trade_date = request.args.get('date')
        top_n = request.args.get('top', 10, type=int)
        
        service = get_web_data_service()
        sector_flows = service.get_sector_flows(trade_date, top_n)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'trade_date': trade_date or 'latest',
                'sector_flows': sector_flows
            }
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': []
        }), 500


@api_v1_blueprint.route('/data/ai-news', methods=['GET'])
def get_ai_news():
    """获取 AI 新闻数据"""
    try:
        trade_date = request.args.get('date')
        limit = request.args.get('limit', 10, type=int)
        
        service = get_web_data_service()
        
        news = service.get_ai_news_list(trade_date, limit)
        sentiment = service.get_ai_news_sentiment(trade_date)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'trade_date': trade_date or 'latest',
                'news': news,
                'sentiment': sentiment
            }
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': {}
        }), 500


@api_v1_blueprint.route('/data/aggregated', methods=['GET'])
def get_aggregated_data():
    """获取聚合数据"""
    try:
        trade_date = request.args.get('date')
        
        service = get_web_data_service()
        data = service.get_aggregated_data(trade_date)
        
        if not data:
            return jsonify({
                'code': 404,
                'message': '未找到聚合数据',
                'data': {}
            }), 404
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': data
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': {}
        }), 500


@api_v1_blueprint.route('/data/latest', methods=['GET'])
def get_latest_data():
    """获取最新数据"""
    try:
        service = get_web_data_service()
        data = service.get_latest_aggregated_data()
        
        if not data:
            return jsonify({
                'code': 404,
                'message': '未找到最新数据',
                'data': {}
            }), 404
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': data
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': {}
        }), 500
