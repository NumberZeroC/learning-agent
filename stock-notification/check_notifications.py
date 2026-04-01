#!/usr/bin/env python3
"""
检查并返回待发送的通知

用法：
    python check_notifications.py
    
输出：
    如果有通知：输出通知内容
    如果没有通知：输出空
"""
import os
import sys
from pathlib import Path
from datetime import datetime


def check_notifications():
    """检查通知目录，返回待发送的通知"""
    
    script_dir = Path(__file__).parent
    notify_dir = script_dir / 'data' / 'notifications'
    
    if not notify_dir.exists():
        return None
    
    # 查找所有通知文件
    notify_files = sorted(notify_dir.glob('notify_*.txt'))
    
    if not notify_files:
        return None
    
    # 返回最新的通知
    latest = notify_files[-1]
    
    # 检查文件时间（只发送 1 小时内的通知）
    file_mtime = datetime.fromtimestamp(latest.stat().st_mtime)
    age = datetime.now() - file_mtime
    
    if age.total_seconds() > 3600:  # 超过 1 小时不发送
        return None
    
    # 读取通知内容
    with open(latest, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    # 返回通知内容和文件路径（用于标记已发送）
    return {
        'content': content,
        'file': str(latest),
        'time': file_mtime.strftime('%Y-%m-%d %H:%M')
    }


def main():
    result = check_notifications()
    
    if result:
        print(f"NOTIFICATION_FOUND")
        print(f"TIME: {result['time']}")
        print(f"FILE: {result['file']}")
        print(f"CONTENT_START: {result['content'][:100]}...")
        print("---CONTENT---")
        print(result['content'])
        return 0
    else:
        print("NO_NOTIFICATION")
        return 1


if __name__ == '__main__':
    sys.exit(main())
