#!/usr/bin/env python3
"""
报告完成通知推送脚本

功能：在报告生成完成后，通过 OpenClaw 发送 QQ 通知给用户

用法：
    python notify_report.py --type evening --report /path/to/report.md
    python notify_report.py --type morning --report /path/to/report.md
    python notify_report.py --type monitor --report /path/to/report.md
"""
import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime


def read_report_summary(report_path: str, report_type: str) -> dict:
    """读取报告摘要和内容"""
    summary = {
        'title': '',
        'highlights': [],
        'content': '',
        'file': report_path
    }
    
    try:
        # 尝试读取 JSON 数据文件
        json_path = report_path.replace('.md', '.json')
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if report_type == 'evening':
                # 晚间报告
                market = data.get('market', {}).get('indices', {})
                shanghai = market.get('shanghai', {})
                if shanghai:
                    summary['title'] = f"上证：{shanghai.get('close', 0):.2f} ({shanghai.get('change_pct', 0):+.2f}%)"
                
                hot_sectors = data.get('hot_sectors', [])
                if hot_sectors:
                    summary['highlights'].append(f"热点板块：{'、'.join(hot_sectors[:3])}")
                
                sector_flows = data.get('sector_flows', [])
                if sector_flows:
                    top_flow = sector_flows[0]
                    summary['highlights'].append(f"资金流入第 1：{top_flow.get('sector')} ({top_flow.get('net_flow', 0)/10000:.1f}万)")
                
                # 提取晚间总结要点
                summary_content = data.get('summary', {}).get('content', '')
                if summary_content:
                    summary['content'] = summary_content[:500]  # 限制长度
            
            elif report_type == 'morning':
                # 早盘报告
                hot_sectors = data.get('hot_sectors', [])
                if hot_sectors:
                    summary['title'] = f"今日热点：{'、'.join(hot_sectors[:3])}"
                
                sector_leaders = data.get('sector_leaders', {})
                if sector_leaders and hot_sectors:
                    first_sector = hot_sectors[0]
                    leaders = sector_leaders.get(first_sector, [])
                    if leaders:
                        summary['highlights'].append(f"{first_sector} 龙头：{leaders[0].get('name')}")
                
                # 提取早盘推荐要点
                recommendations = data.get('recommendations', [])
                if recommendations:
                    content_lines = ["今日推荐："]
                    for rec in recommendations[:3]:
                        content_lines.append(f"• {rec.get('name', '')} {rec.get('code', '')}")
                    summary['content'] = '\n'.join(content_lines)
            
            elif report_type == 'monitor':
                # 监控报告
                stocks = data.get('stocks', [])
                buy_count = sum(1 for s in stocks if s.get('signal') in ['BUY', 'STRONG_BUY'])
                sell_count = sum(1 for s in stocks if s.get('signal') in ['SELL', 'STRONG_SELL'])
                hold_count = len(stocks) - buy_count - sell_count
                
                summary['title'] = f"监控 {len(stocks)} 只：买入{buy_count} 持有{hold_count} 卖出{sell_count}"
                
                # 找出强信号股票
                strong_signals = [s for s in stocks if s.get('signal') in ['STRONG_BUY', 'STRONG_SELL']]
                if strong_signals:
                    content_lines = ["强信号："]
                    for s in strong_signals[:3]:
                        action = '🔴 买入' if s.get('signal') == 'STRONG_BUY' else '🟢 卖出'
                        content_lines.append(f"{action} {s.get('name')}({s.get('code')})")
                    summary['content'] = '\n'.join(content_lines)
        
        # 如果没有 JSON，尝试从 MD 文件提取
        if not summary['title'] and os.path.exists(report_path):
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取标题
            lines = content.split('\n')
            for line in lines[:10]:
                if line.startswith('# '):
                    summary['title'] = line.replace('# ', '').strip()
                    break
            
            # 提取前几段作为内容
            content_lines = []
            for line in lines[1:20]:
                if line.strip() and not line.startswith('#'):
                    content_lines.append(line)
            summary['content'] = '\n'.join(content_lines[:300])  # 限制长度
    
    except Exception as e:
        print(f"⚠️ 读取报告失败：{e}")
    
    return summary


def send_notification(report_type: str, summary: dict, verbose: bool = True):
    """发送通知（通过 OpenClaw message 工具）"""
    
    # 确定表情和标题
    icons = {
        'evening': '🌙',
        'morning': '📈',
        'monitor': '🎯'
    }
    
    titles = {
        'evening': '晚间市场总结',
        'morning': '早盘推荐',
        'monitor': '持仓监控'
    }
    
    icon = icons.get(report_type, '📊')
    title = titles.get(report_type, '报告完成')
    
    # 构建精简消息（用于实际发送）
    clean_message = f"{icon} *{title}*\n\n"
    
    if summary.get('title'):
        clean_message += f"📌 {summary['title']}\n\n"
    
    if summary.get('highlights'):
        clean_message += "要点：\n"
        for h in summary['highlights'][:3]:
            clean_message += f"• {h}\n"
        clean_message += "\n"
    
    # 如果有详细内容，直接展示
    if summary.get('content'):
        clean_message += f"{summary['content']}\n\n"
    
    clean_message += "_投资有风险，决策需谨慎_"
    
    # 如果是详细模式，输出调试信息（用于日志）
    if verbose:
        print(f"NOTIFICATION_READY")
        print(f"TYPE: {report_type}")
        print(f"TITLE: {title}")
        print(f"MESSAGE: {clean_message}")
    else:
        # 精简模式：只输出消息内容（用于直接发送）
        print(clean_message)
    
    return clean_message


def main():
    parser = argparse.ArgumentParser(description='报告完成通知推送')
    parser.add_argument('--type', '-t', required=True, 
                       choices=['evening', 'morning', 'monitor'],
                       help='报告类型')
    parser.add_argument('--report', '-r', required=True,
                       help='报告文件路径')
    parser.add_argument('--output', '-o',
                       help='输出通知文件路径（可选）')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='精简模式：只输出消息内容，不输出调试信息')
    
    args = parser.parse_args()
    
    # 精简模式：只输出消息内容，不输出调试信息
    quiet = args.quiet
    
    if not quiet:
        print(f"\n{'='*50}")
        print(f"📬 准备发送报告通知 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*50}\n")
    
    # 读取报告摘要
    summary = read_report_summary(args.report, args.type)
    
    # 发送通知
    message = send_notification(args.type, summary, verbose=not quiet)
    
    # 可选：输出到文件供外部脚本处理
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(message)
        if not quiet:
            print(f"\n📄 通知已保存到：{args.output}")
    
    if not quiet:
        print(f"\n✅ 通知准备完成")
        print(f"\n{message}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
