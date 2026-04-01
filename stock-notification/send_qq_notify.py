#!/usr/bin/env python3
"""
直接发送 QQ 通知到用户

功能：调用 OpenClaw CLI 发送 QQ 消息，不依赖 Heartbeat 轮询

用法：
    python send_qq_notify.py "消息内容"
    echo "消息内容" | python send_qq_notify.py --stdin
"""
import os
import sys
import subprocess
import argparse


def send_qq_message(message: str):
    """通过 OpenClaw CLI 发送 QQ 消息"""
    
    # QQ 频道配置
    channel = "qqbot"
    target = "qqbot:c2c:6BD7A1BCF3F92369D0580647287C0D52"
    
    # 构建命令（使用完整路径，避免 cron 环境中找不到命令）
    cmd = [
        "/home/admin/.local/share/pnpm/openclaw",
        "message", "send",
        "--channel", channel,
        "--target", target,
        "--message", message
    ]
    
    try:
        # 执行命令 (Python 3.6 兼容)
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=30,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode == 0:
            print(f"✅ QQ 消息发送成功")
            if result.stdout:
                print(f"   {result.stdout.strip()}")
            return True
        else:
            print(f"❌ 发送失败：{result.stderr}")
            return False
    
    except subprocess.TimeoutExpired:
        print(f"❌ 发送超时")
        return False
    except Exception as e:
        print(f"❌ 发送异常：{e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='发送 QQ 通知')
    parser.add_argument('message', nargs='?', help='消息内容')
    parser.add_argument('--stdin', '-i', action='store_true', help='从 stdin 读取消息')
    
    args = parser.parse_args()
    
    # 获取消息内容
    if args.stdin:
        message = sys.stdin.read().strip()
    elif args.message:
        message = args.message
    else:
        print("❌ 请提供消息内容或使用 --stdin 从管道读取")
        print("用法：python send_qq_notify.py \"消息内容\"")
        print("      echo \"消息\" | python send_qq_notify.py --stdin")
        return 1
    
    if not message:
        print("❌ 消息内容为空")
        return 1
    
    print(f"📬 准备发送 QQ 消息...")
    print(f"   内容：{message[:50]}...")
    
    success = send_qq_message(message)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
