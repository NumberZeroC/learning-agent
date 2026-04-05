#!/bin/bash
# Learning Agent Web 服务守护脚本
# 功能：自动重启服务，防止因 OOM 导致服务停止

set -e

WORKDIR="/home/admin/.openclaw/workspace/learning-agent"
VENV_PYTHON="$WORKDIR/venv/bin/python3"
LOGFILE="/tmp/learning-agent-watchdog.log"
MAX_RESTARTS=5
RESTART_DELAY=5

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOGFILE"
}

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
        
        # 检查重启频率（避免频繁重启循环）
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
        nohup python3 web/app.py --host 0.0.0.0 --port 5001 > /tmp/learning-agent.log 2>&1 &
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
        # 服务正常运行，重置重启计数
        restart_count=0
        
        # 每 30 秒检查一次
        sleep 30
    fi
done
