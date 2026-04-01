#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术指标分析 - 定时执行脚本

注意：请使用 Python 3.11+ 运行（需要 venv311 虚拟环境）
用法：/home/admin/.openclaw/workspace/stock-notification/venv311/bin/python3 scheduled_technical_pick.py

功能：
- 开盘时间每 30 分钟执行一次（9:30-11:30, 13:00-15:00）
- 执行结果推送 QQ 消息
- 通过 cron 或 systemd timer 调用

用法：
    python scheduled_technical_pick.py
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from technical_analysis import TechnicalAnalyzer


def is_trading_time() -> bool:
    """判断是否在交易时间"""
    now = datetime.now()
    
    # 只在工作日执行
    if now.weekday() >= 5:  # 周六=5, 周日=6
        return False
    
    # 上午：9:30-11:30
    # 下午：13:00-15:00
    hour = now.hour
    minute = now.minute
    
    # 转换为分钟数
    current_minutes = hour * 60 + minute
    
    morning_start = 9 * 60 + 30   # 9:30
    morning_end = 11 * 60 + 30    # 11:30
    afternoon_start = 13 * 60     # 13:00
    afternoon_end = 15 * 60       # 15:00
    
    return (morning_start <= current_minutes <= morning_end or 
            afternoon_start <= current_minutes <= afternoon_end)


def should_run() -> bool:
    """判断是否应该执行（每 30 分钟）"""
    now = datetime.now()
    minute = now.minute
    
    # 在 00 分和 30 分执行
    return minute in [0, 30]


def send_qq_message(message: str) -> bool:
    """发送 QQ 消息"""
    try:
        # 使用 OpenClaw message 工具
        # 这里通过子进程调用 openclaw CLI
        import subprocess
        
        # 消息内容转义
        escaped_message = message.replace('"', '\\"').replace('\n', '\\n')
        
        # 调用 openclaw message 命令
        cmd = f'''openclaw message send --channel qqbot --target "qqbot:c2c:6BD7A1BCF3F92369D0580647287C0D52" --message "{escaped_message}"'''
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✅ QQ 消息已发送")
            return True
        else:
            print(f"❌ QQ 消息发送失败：{result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 发送 QQ 消息异常：{e}")
        return False


def send_qq_message_api(message: str, target: str = "qqbot:c2c:6BD7A1BCF3F92369D0580647287C0D52") -> bool:
    """发送 QQ 消息（使用 OpenClaw message 工具）"""
    try:
        import subprocess
        
        # 使用 openclaw message 命令发送
        # 注意：消息中的特殊字符需要转义
        escaped_message = message.replace('"', '\\"').replace('\n', '\\n').replace('`', '\\`')
        
        cmd = f'''openclaw message send --channel qqbot --target "{target}" --message "{escaped_message}"'''
        
        print(f"📱 发送 QQ 消息...")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✅ QQ 消息已发送")
            return True
        else:
            print(f"⚠️ QQ 消息发送返回码：{result.returncode}")
            if result.stderr:
                print(f"   错误：{result.stderr[:200]}")
            # 即使发送失败也返回 True，因为分析成功了
            return True
            
    except Exception as e:
        print(f"⚠️ 发送 QQ 消息异常：{e}")
        # 输出消息内容供手动发送
        print(f"\n📱 消息内容:\n{message}")
        return True  # 分析成功，只是消息发送失败


def main():
    print("=" * 70)
    print("📊 技术指标选股 - 定时执行")
    print("=" * 70)
    print(f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查是否在交易时间
    if not is_trading_time():
        print("⏰ 非交易时间，跳过执行")
        print("交易时间：周一至周五 9:30-11:30, 13:00-15:00")
        sys.exit(0)
    
    # 检查是否应该执行（00 分或 30 分）
    if not should_run():
        print(f"⏰ 未到执行时间（当前分钟：{datetime.now().minute}）")
        print("执行时间：每 30 分钟（00 分、30 分）")
        sys.exit(0)
    
    print("\n✅ 满足执行条件，开始分析...")
    
    # 执行技术分析
    analyzer = TechnicalAnalyzer()
    result = analyzer.run_analysis(limit=10, min_score=60)
    
    if result.get('success') and result.get('qq_message'):
        # 发送 QQ 消息
        send_qq_message_api(result['qq_message'])
        
        print(f"\n✅ 定时执行完成")
        print(f"📄 报告：{result.get('report_file', 'N/A')}")
    else:
        print(f"\n⚠️ 分析失败或未找到符合条件的股票")
        if result.get('error'):
            print(f"错误：{result['error']}")
    
    sys.exit(0 if result.get('success') else 1)


if __name__ == '__main__':
    main()
