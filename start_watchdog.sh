#!/bin/bash
# ============================================
# Learning Agent Web 服务守护脚本
# ============================================
# 功能：
#   - 自动监控 Web 服务状态
#   - 服务异常时自动重启
#   - 防止 OOM 导致服务停止
# ============================================
# 
# 用法：
#   ./start_watchdog.sh              # 启动守护进程
#   ./start_watchdog.sh --stop       # 停止守护进程
#   ./start_watchdog.sh --status     # 查看状态
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKDIR="$SCRIPT_DIR"
VENV_PYTHON="$WORKDIR/venv/bin/python3"
LOGFILE="$WORKDIR/logs/watchdog.log"
PIDFILE="$WORKDIR/.watchdog.pid"
MAX_RESTARTS=5
RESTART_DELAY=5
CHECK_INTERVAL=30

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOGFILE"
}

show_help() {
    cat << EOF
🛡️  Learning Agent 守护进程

用法：$0 [选项]

选项:
  --stop             停止守护进程
  --status           查看状态
  --help             显示帮助

功能:
  - 每30秒检查服务状态
  - 服务异常自动重启
  - 重启频率限制（最多5次/分钟）
EOF
}

stop_watchdog() {
    echo -e "${BLUE}🛑 停止守护进程...${NC}"
    
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID 2>/dev/null || true
            rm -f "$PIDFILE"
            echo -e "${GREEN}✅ 守护进程已停止${NC}"
        else
            rm -f "$PIDFILE"
            echo -e "${YELLOW}⚠️  守护进程已停止${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  未找到PID文件${NC}"
        pkill -f "start_watchdog.sh" 2>/dev/null || true
    fi
}

check_status() {
    echo -e "${BLUE}📊 守护进程状态${NC}"
    echo ""
    
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 守护进程运行中${NC}"
            echo "   PID: $PID"
            echo "   日志: $LOGFILE"
            
            # 检查Web服务
            if curl -s http://localhost:5001/health > /dev/null 2>&1; then
                echo -e "${GREEN}   Web服务：正常${NC}"
            else
                echo -e "${YELLOW}   Web服务：异常${NC}"
            fi
            return 0
        fi
    fi
    
    echo -e "${BLUE}ℹ️  守护进程未运行${NC}"
    return 1
}

start_watchdog() {
    # 创建日志目录
    mkdir -p "$WORKDIR/logs"
    
    log "🚀 Learning Agent 守护进程启动"
    log "📂 工作目录：$WORKDIR"
    log "🐍 Python: $VENV_PYTHON"
    
    restart_count=0
    last_start_time=0
    
    while true; do
        current_time=$(date +%s)
        
        # 检查进程是否存在
        if ! pgrep -f "python3 web/app.py.*5001" > /dev/null; then
            log "⚠️  服务未运行，尝试重启..."
            
            # 检查重启频率
            if [ $((current_time - last_start_time)) -lt 60 ]; then
                restart_count=$((restart_count + 1))
                if [ $restart_count -ge $MAX_RESTARTS ]; then
                    log "❌ 重启次数过多（$MAX_RESTARTS 次），退出守护进程"
                    exit 1
                fi
                log "⚠️  重启次数：$restart_count/$MAX_RESTARTS"
            else
                restart_count=0
            fi
            
            # 启动服务
            log "🚀 启动服务..."
            cd "$WORKDIR"
            source venv/bin/activate
            nohup python3 web/app.py --host 0.0.0.0 --port 5001 > logs/web.log 2>&1 &
            PID=$!
            last_start_time=$current_time
            
            sleep 3
            
            # 验证启动
            if pgrep -f "python3 web/app.py.*5001" > /dev/null; then
                log "✅ 服务启动成功 (PID: $PID)"
            else
                log "❌ 服务启动失败"
            fi
        else
            # 服务正常运行
            restart_count=0
            sleep $CHECK_INTERVAL
        fi
    done
}

# 主函数
main() {
    ACTION="start"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --stop)
                ACTION="stop"
                shift
                ;;
            --status)
                ACTION="status"
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                echo -e "${RED}❌ 未知选项：$1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
    
    mkdir -p "$WORKDIR/logs"
    
    case $ACTION in
        stop)
            stop_watchdog
            ;;
        status)
            check_status
            ;;
        start)
            # 后台启动
            nohup bash "$0" --run > "$LOGFILE" 2>&1 &
            PID=$!
            echo $PID > "$PIDFILE"
            echo -e "${GREEN}✅ 守护进程已启动 (PID: $PID)${NC}"
            echo "   日志: $LOGFILE"
            echo ""
            echo "查看日志：tail -f $LOGFILE"
            echo "停止守护：$0 --stop"
            ;;
        run)
            start_watchdog
            ;;
    esac
}

main "$@"