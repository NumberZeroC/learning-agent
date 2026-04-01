#!/bin/bash
# Learning Agent Web 服务启动脚本

set -e

WORKDIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$WORKDIR")"
LOGDIR="$PROJECT_DIR/logs"
PIDFILE="$PROJECT_DIR/web.pid"

mkdir -p "$LOGDIR"

echo "========================================"
echo "🌐 Learning Agent Web 服务"
echo "========================================"
echo ""

# 检查是否已在运行
if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "✅ 服务已在运行 (PID: $PID)"
        exit 0
    else
        rm "$PIDFILE"
    fi
fi

# 加载环境变量
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
fi

# 从项目根目录启动
cd "$PROJECT_DIR"

# 启动服务
nohup python3 -c "
import sys
sys.path.insert(0, '.')
from web.app import app
app.run(host='0.0.0.0', port=5001, debug=False)
" > "$LOGDIR/web.log" 2>&1 &

PID=$!
echo $PID > "$PIDFILE"

echo "========================================"
echo "✅ Web 服务已启动！"
echo "========================================"
echo "   PID:        $PID"
echo "   端口：      5001"
echo "   日志：      $LOGDIR/web.log"
echo "   访问地址：  http://127.0.0.1:5001"
echo ""
echo "========================================"
echo "常用命令："
echo "   查看日志：tail -f $LOGDIR/web.log"
echo "   停止服务：$WORKDIR/stop_web.sh"
echo "   重启服务：$WORKDIR/stop_web.sh && $WORKDIR/start_web.sh"
echo ""
