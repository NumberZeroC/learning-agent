#!/bin/bash
#
# 发送报告完成通知到 QQ（实时发送，不依赖 Heartbeat）
# 用法：./send_notify.sh "消息内容"
#       echo "消息" | ./send_notify.sh --stdin
#

# 支持从 stdin 读取或参数传入
if [ "$1" = "--stdin" ] || [ -z "$1" ]; then
    # 从 stdin 读取
    MESSAGE=$(cat)
else
    MESSAGE="$1"
fi

if [ -z "$MESSAGE" ]; then
    echo "❌ 用法：$0 \"消息内容\" 或 echo \"消息\" | $0 --stdin"
    exit 1
fi

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 使用 Python 脚本直接发送 QQ 消息
echo "📬 正在发送 QQ 通知..."
echo "$MESSAGE" | "$SCRIPT_DIR/send_qq_notify.py" --stdin

if [ $? -eq 0 ]; then
    echo "✅ 通知已实时发送到 QQ"
    exit 0
else
    echo "⚠️ 发送失败，降级为写入通知文件（等待 Heartbeat 发送）"
    
    # 降级方案：写入通知文件，等待 Heartbeat 检查
    NOTIFY_DIR="$SCRIPT_DIR/data/notifications"
    mkdir -p "$NOTIFY_DIR"
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    NOTIFY_FILE="$NOTIFY_DIR/notify_${TIMESTAMP}.txt"
    echo "$MESSAGE" > "$NOTIFY_FILE"
    
    echo "   通知已写入：$NOTIFY_FILE"
    exit 1
fi
