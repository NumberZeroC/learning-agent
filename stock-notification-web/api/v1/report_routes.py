"""
报告 API
"""
import os
import json
from flask import jsonify, current_app, request
from api.v1 import api_v1_blueprint
from datetime import datetime, timedelta


def scan_monitor_dir(monitor_dir, report_type=None, days_limit=7):
    """扫描 monitor 子目录中的报告（只返回 7 天内）"""
    reports = []
    if not os.path.isdir(monitor_dir):
        return reports
    
    cutoff_date = datetime.now() - timedelta(days=days_limit)
    
    for filename in os.listdir(monitor_dir):
        filepath = os.path.join(monitor_dir, filename)
        if not os.path.isfile(filepath):
            continue
        
        if not filename.endswith('.md'):
            continue
        
        # 类型筛选
        if report_type and report_type != 'all' and report_type != 'monitor':
            continue
        
        stat = os.stat(filepath)
        mtime = datetime.fromtimestamp(stat.st_mtime)
        
        # 只返回 7 天内的报告
        if mtime < cutoff_date:
            continue
        
        report_info = {
            'filename': filename,
            'type': 'monitor',
            'title': '持仓监控报告',
            'created_at': mtime.isoformat(),
            'size': stat.st_size,
            'path': f'/data/reports/monitor/{filename}',
            'icon': 'bi-eye text-info',
            'description': '持仓股票的技术分析和买卖建议...'
        }
        reports.append(report_info)
    
    return reports


@api_v1_blueprint.route('/reports', methods=['GET'])
def get_reports():
    """获取报告列表"""
    try:
        reports_dir = current_app.config.get('REPORTS_DIR', '/home/admin/.openclaw/workspace/stock-agent/data/reports')
        report_type = current_app.config.get('REPORT_TYPE', request.args.get('type', 'all'))
        
        if not os.path.exists(reports_dir):
            return jsonify({
                'code': 404,
                'message': '报告目录不存在',
                'data': []
            }), 404
        
        reports = []
        cutoff_date = datetime.now() - timedelta(days=7)  # 7 天限制
        
        # 扫描主目录
        for filename in os.listdir(reports_dir):
            filepath = os.path.join(reports_dir, filename)
            
            # 处理 monitor 子目录
            if filename == 'monitor' and os.path.isdir(filepath):
                monitor_reports = scan_monitor_dir(filepath, report_type, days_limit=7)
                reports.extend(monitor_reports)
                continue
            
            # 跳过非文件
            if not os.path.isfile(filepath):
                continue
            
            # 获取文件信息
            stat = os.stat(filepath)
            mtime = datetime.fromtimestamp(stat.st_mtime)
            
            # 根据类型筛选
            if report_type and report_type != 'all':
                if report_type == 'morning':
                    if 'morning' not in filename.lower():
                        continue
                elif report_type == 'evening':
                    if 'evening' not in filename.lower():
                        continue
                elif report_type == 'monitor':
                    # monitor 类型只返回包含 monitor 或 analysis 的文件，且 7 天内
                    if 'monitor' not in filename.lower() and 'analysis' not in filename.lower():
                        continue
                    if mtime < cutoff_date:
                        continue
            
            # 只处理 markdown 报告（不展示 JSON）
            if not filename.endswith('.md'):
                continue
            
            # 尝试解析报告类型
            report_info = {
                'filename': filename,
                'type': 'unknown',
                'title': filename,
                'created_at': mtime.isoformat(),
                'size': stat.st_size,
                'path': f'/data/reports/{filename}'
            }
            
            # 根据文件名判断类型
            if 'morning' in filename.lower():
                report_info['type'] = 'morning'
                report_info['icon'] = 'bi-sunrise text-warning'
                report_info['title'] = '早盘分析推荐'
                report_info['description'] = '基于隔夜分析和早间新闻的选股推荐...'
            elif 'evening' in filename.lower():
                report_info['type'] = 'evening'
                report_info['icon'] = 'bi-moon-stars text-primary'
                report_info['title'] = '晚间新闻综合分析'
                report_info['description'] = '分析全天新闻，识别利好板块和受益个股...'
            elif 'analysis' in filename.lower() or 'monitor' in filename.lower():
                report_info['type'] = 'monitor'
                report_info['icon'] = 'bi-eye text-info'
                report_info['title'] = '持仓监控报告'
                report_info['description'] = '持仓股票的技术分析和买卖建议...'
                # monitor 类型只返回 7 天内的
                if mtime < cutoff_date:
                    continue
            elif 'data' in filename.lower():
                report_info['type'] = 'data'
                report_info['icon'] = 'bi-database text-secondary'
                report_info['title'] = '市场数据快照'
                report_info['description'] = '实时市场数据记录...'
            
            reports.append(report_info)
        
        # 按修改时间排序，最新的在前
        reports.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': reports,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': []
        }), 500


@api_v1_blueprint.route('/reports/latest-data', methods=['GET'])
def get_latest_report_data():
    """获取最新报告的市场数据（用于首页概览）"""
    try:
        # 🔥 修复：使用正确的报告目录路径
        reports_dir = current_app.config.get('REPORTS_DIR', '/home/admin/.openclaw/workspace/data/stock-agent/reports')
        
        if not os.path.exists(reports_dir):
            return jsonify({
                'code': 404,
                'message': '未找到报告目录',
                'data': {}
            }), 404
        
        # 收集所有晚间报告
        evening_reports = []
        for filename in os.listdir(reports_dir):
            if (filename.startswith('evening_data_snapshot_') or filename.startswith('evening_summary_')) and filename.endswith('.json'):
                import re
                match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
                if match:
                    date_str = match.group(1)
                    evening_reports.append((date_str, os.path.join(reports_dir, filename)))
        
        # 按日期倒序排序
        evening_reports.sort(reverse=True, key=lambda x: x[0])
        
        if not evening_reports:
            return jsonify({
                'code': 404,
                'message': '未找到晚间报告',
                'data': {}
            }), 404
        
        # 🔥 修复：大盘指数和板块使用最新报告
        latest_date, latest_json = evening_reports[0]
        
        # 读取最新报告数据（用于大盘指数和板块）
        with open(latest_json, 'r', encoding='utf-8') as f:
            latest_data = json.load(f)
        
        # 🔥 修复：龙虎榜单独查找有数据的报告
        top_list = []
        for date_str, filepath in evening_reports:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 检查龙虎榜数据
                if 'data' in data and 'top_list' in data['data']:
                    top_list = data['data'].get('top_list', [])
                elif 'top_list' in data:
                    top_list = data.get('top_list', [])
                
                # 如果有龙虎榜数据，使用此报告
                if len(top_list) > 0:
                    print(f"[INFO] 龙虎榜使用 {date_str} 的数据（{len(top_list)}条）")
                    break
            except Exception as e:
                print(f"[WARN] 读取 {filepath} 失败：{e}")
                continue
        
        # 使用最新报告的大盘指数和板块数据
        # 🔥 修复：支持两种数据结构
        indices = {}
        if 'data' in latest_data and 'market_indices' in latest_data['data']:
            indices = latest_data['data'].get('market_indices', {})
        elif 'market' in latest_data:
            indices = latest_data['market'].get('indices', {})
        
        shanghai = indices.get('shanghai', {})
        
        # 计算市场情绪得分
        sentiment_score = 5.0
        change_pct = shanghai.get('change_pct', 0)
        if change_pct < -3:
            sentiment_score = 3.0
        elif change_pct < -1:
            sentiment_score = 4.0
        elif change_pct > 1:
            sentiment_score = 7.0
        elif change_pct > 3:
            sentiment_score = 8.0
        
        # 🔥 修复：支持两种数据结构的板块资金流
        sector_flows = []
        if 'data' in latest_data and 'sector_flows' in latest_data['data']:
            sector_flows = latest_data['data'].get('sector_flows', [])
        else:
            sector_flows = latest_data.get('sector_flows', [])
        
        positive_sectors = sum(1 for s in sector_flows if s.get('net_flow', 0) > 0)
        negative_sectors = sum(1 for s in sector_flows if s.get('net_flow', 0) < 0)
        total_net_flow = sum(s.get('net_flow', 0) for s in sector_flows)
        
        # 资金流情绪
        if positive_sectors > negative_sectors:
            sentiment_score += 1
        elif positive_sectors < negative_sectors:
            sentiment_score -= 1
        
        # 🔥 修复：统一龙虎榜字段名（适配前端代码），按净买额排序
        formatted_top_list = []
        for stock in top_list:  # 🔥 获取所有数据
            formatted_top_list.append({
                'ts_code': stock.get('ts_code', ''),
                'name': stock.get('name', ''),
                'close': stock.get('close', 0),
                'pct_change': stock.get('pct_change', 0),
                'amount': stock.get('amount', 0),
                'net_in': stock.get('net_amount', 0),  # 🔥 前端使用 net_in
                'l_buy': stock.get('l_buy', 0),
                'l_sell': stock.get('l_sell', 0),
                'reason': stock.get('reason', '')
            })
        
        # 🔥 按净买额从高到低排序
        formatted_top_list.sort(key=lambda x: x['net_in'], reverse=True)
        
        result = {
            'index': {
                'value': shanghai.get('close', 0),
                'change': change_pct
            },
            'sentiment': '谨慎' if change_pct < 0 else '偏暖',
            'sentimentScore': round(sentiment_score, 1),
            'sector_flows': sector_flows[:10],  # 板块资金流 TOP10
            'top_list': formatted_top_list,  # 🔥 龙虎榜全部数据（已排序）
            'market_summary': {
                'positive_sectors': positive_sectors,
                'negative_sectors': negative_sectors,
                'total_net_flow': total_net_flow
            },
            # 🔥 修复：使用最新报告的日期（大盘指数的日期）
            'report_date': latest_data.get('trade_date', latest_data.get('date', latest_date)),
            'report_time': latest_data.get('generated_at', latest_data.get('timestamp', ''))
        }
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': {}
        }), 500


@api_v1_blueprint.route('/reports/morning-detail', methods=['GET'])
def get_morning_recommend_detail():
    """获取早盘推荐详情（包含具体股票）"""
    try:
        reports_dir = current_app.config.get('REPORTS_DIR', '/home/admin/.openclaw/workspace/stock-agent/data/reports')
        
        # 查找最新的早盘推荐 JSON
        latest_json = None
        for filename in sorted(os.listdir(reports_dir), reverse=True):
            if filename.startswith('morning_recommend_') and filename.endswith('.json'):
                filepath = os.path.join(reports_dir, filename)
                if os.path.isfile(filepath):
                    latest_json = filepath
                    break
        
        if not latest_json:
            return jsonify({
                'code': 404,
                'message': '未找到早盘推荐数据',
                'data': {}
            }), 404
        
        # 读取 JSON 数据
        with open(latest_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取推荐股票详情
        recommendations = data.get('recommendations', [])
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'date': data.get('date', ''),
                'timestamp': data.get('timestamp', ''),
                'recommendations': recommendations
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': {}
        }), 500
