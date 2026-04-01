#!/bin/bash
# Stock-Agent Web 守护进程脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/logs/web.log"
PID_FILE="$SCRIPT_DIR/web.pid"

# 确保日志目录存在
mkdir -p "$SCRIPT_DIR/logs"

# 函数：检查服务状态
check_status() {
    # 优先检查新 PID 文件路径
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0  # 运行中
        fi
    fi
    
    # 兼容旧 PID 文件路径
    if [ -f "$SCRIPT_DIR/logs/web.pid" ]; then
        PID=$(cat "$SCRIPT_DIR/logs/web.pid")
        if ps -p "$PID" > /dev/null 2>&1; then
            # 迁移到新路径
            mv "$SCRIPT_DIR/logs/web.pid" "$PID_FILE"
            return 0  # 运行中
        fi
    fi
    
    # 检查端口是否监听（兜底检查）
    if command -v netstat > /dev/null 2>&1; then
        if netstat -tlnp 2>/dev/null | grep -q ":5000"; then
            # 尝试从 netstat 获取 PID
            PID=$(netstat -tlnp 2>/dev/null | grep ":5000" | awk '{print $7}' | cut -d'/' -f1)
            if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
                echo "$PID" > "$PID_FILE"
                return 0  # 运行中
            fi
        fi
    fi
    
    return 1  # 未运行
}

# 函数：启动服务
start() {
    if check_status; then
        echo "✅ 服务已在运行 (PID: $(cat $PID_FILE))"
        return 0
    fi
    
    echo "🚀 启动 Stock-Agent Web..."
    cd "$SCRIPT_DIR"
    
    # 后台启动
    nohup python3 app.py > "$LOG_FILE" 2>&1 &
    PID=$!
    
    # 记录 PID
    echo "$PID" > "$PID_FILE"
    
    # 等待启动
    sleep 3
    
    # 检查是否启动成功
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ 服务已启动 (PID: $PID)"
        echo "🌐 访问地址：http://39.97.249.78:5000"
        return 0
    else
        echo "❌ 服务启动失败，查看日志：$LOG_FILE"
        return 1
    fi
}

# 函数：停止服务
stop() {
    if check_status; then
        PID=$(cat "$PID_FILE")
        echo "🛑 停止服务 (PID: $PID)..."
        kill "$PID" 2>/dev/null
        sleep 2
        rm -f "$PID_FILE"
        echo "✅ 服务已停止"
    else
        echo "ℹ️  服务未运行"
    fi
}

# 函数：重启服务
restart() {
    stop
    sleep 2
    start
}

# 函数：查看状态
status() {
    if check_status; then
        PID=$(cat "$PID_FILE")
        echo "✅ 服务运行中"
        echo "   PID: $PID"
        echo "   端口：5000"
        echo "   访问：http://39.97.249.78:5000"
        echo ""
        echo "📊 进程信息:"
        ps aux | grep "$PID" | grep -v grep
        echo ""
        echo "📁 日志（最后 10 行）:"
        tail -10 "$LOG_FILE"
    else
        echo "❌ 服务未运行"
    fi
}

# 主逻辑
case "${1:-status}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    *)
        echo "用法：$0 {start|stop|restart|status}"
        exit 1
        ;;
esac
