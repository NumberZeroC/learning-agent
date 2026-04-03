#!/bin/bash
# CCP Web 服务器管理脚本
# 端口：5008

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/logs/web_server.pid"
LOG_FILE="$SCRIPT_DIR/logs/web_server.log"

case "$1" in
    start)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "⚠️  Web 服务器已在运行 (PID: $(cat $PID_FILE))"
            exit 0
        fi
        
        cd "$SCRIPT_DIR"
        source .venv/bin/activate
        export $(grep -v '^#' .env | xargs)
        
        mkdir -p logs
        nohup python -m src.web_server --host 0.0.0.0 --port 5008 > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        
        sleep 2
        if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "✅ CCP Web 服务器已启动"
            echo "📁 PID: $(cat $PID_FILE)"
            echo "🌐 访问地址：http://0.0.0.0:5008"
            echo "📝 日志文件：$LOG_FILE"
        else
            echo "❌ 启动失败，查看日志：$LOG_FILE"
            exit 1
        fi
        ;;
    
    stop)
        if [ -f "$PID_FILE" ]; then
            kill $(cat "$PID_FILE") 2>/dev/null
            rm -f "$PID_FILE"
            echo "✅ CCP Web 服务器已停止"
        else
            echo "⚠️  Web 服务器未运行"
        fi
        ;;
    
    restart)
        $0 stop
        sleep 1
        $0 start
        ;;
    
    status)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "✅ CCP Web 服务器运行中"
            echo "📁 PID: $(cat $PID_FILE)"
            echo "🌐 端口：5008"
            netstat -tlnp 2>/dev/null | grep 5008 || ss -tlnp | grep 5008
        else
            echo "❌ CCP Web 服务器未运行"
        fi
        ;;
    
    logs)
        tail -f "$LOG_FILE"
        ;;
    
    *)
        echo "用法：$0 {start|stop|restart|status|logs}"
        echo
        echo "命令:"
        echo "  start   - 启动 Web 服务器"
        echo "  stop    - 停止 Web 服务器"
        echo "  restart - 重启 Web 服务器"
        echo "  status  - 查看运行状态"
        echo "  logs    - 查看日志 (实时)"
        exit 1
        ;;
esac
