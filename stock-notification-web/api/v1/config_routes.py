"""
配置功能 API
"""
import os
import yaml
from flask import jsonify, request, current_app
from api.v1 import api_v1_blueprint
from services.config_service import ConfigService
from datetime import datetime


@api_v1_blueprint.route('/config', methods=['GET'])
def get_config():
    """获取配置"""
    try:
        service = ConfigService(current_app.config)
        result = service.get_config()
        
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


@api_v1_blueprint.route('/config', methods=['PUT'])
def update_config():
    """更新配置"""
    try:
        service = ConfigService(current_app.config)
        data = request.get_json()
        
        updated_fields = service.update_config(data)
        
        return jsonify({
            'code': 200,
            'message': '配置已更新',
            'data': {
                'updated_fields': updated_fields
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': None
        }), 500


@api_v1_blueprint.route('/config/monitor-stocks', methods=['POST'])
def add_monitor_stock():
    """添加监控股票"""
    try:
        data = request.get_json()
        code = data.get('code')
        name = data.get('name', '')
        
        if not code:
            return jsonify({
                'code': 400,
                'message': '缺少参数：code',
                'data': None
            }), 400
        
        service = ConfigService(current_app.config)
        service.add_monitor_stock(code, name)
        
        return jsonify({
            'code': 200,
            'message': '已添加监控股票',
            'data': {
                'code': code,
                'name': name,
                'added_at': datetime.now().isoformat()
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': None
        }), 500


@api_v1_blueprint.route('/config/monitor-stocks/<code>', methods=['DELETE'])
def remove_monitor_stock(code):
    """删除监控股票"""
    try:
        service = ConfigService(current_app.config)
        service.remove_monitor_stock(code)
        
        return jsonify({
            'code': 200,
            'message': '已删除监控股票',
            'data': {
                'code': code,
                'removed_at': datetime.now().isoformat()
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': None
        }), 500


@api_v1_blueprint.route('/config/schedule/status', methods=['GET'])
def get_schedule_status():
    """获取定时任务状态"""
    try:
        service = ConfigService(current_app.config)
        result = service.get_schedule_status()
        
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
