#!/bin/bash
# Learning Agent Web 服务停止脚本

PIDFILE="$(cd "$(dirname "$0")" && pwd)/../web.pid"

echo "🛑 停止 Web 服务..."

if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        rm "$PIDFILE"
        echo "✅ 服务已停止 (PID: $PID)"
    else
        rm "$PIDFILE"
        echo "⚠️  服务未运行（PID 文件存在但进程不存在）"
    fi
else
    echo "⚠️  PID 文件不存在，服务可能未运行"
fi

echo ""
