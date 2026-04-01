#!/bin/bash
# Stock-Agent Web 看门狗脚本
# 检查服务状态，如果进程异常则自动重启

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/logs/watchdog.log"
PID_FILE="$SCRIPT_DIR/web.pid"
WEBCTL="$SCRIPT_DIR/webctl.sh"

# 确保日志目录存在
mkdir -p "$SCRIPT_DIR/logs"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 检查服务状态
check_service() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0  # 运行中
        fi
    fi
    return 1  # 未运行
}

# 检查端口是否监听
check_port() {
    if command -v netstat > /dev/null 2>&1; then
        netstat -tlnp 2>/dev/null | grep -q ":5000"
        return $?
    elif command -v ss > /dev/null 2>&1; then
        ss -tlnp 2>/dev/null | grep -q ":5000"
        return $?
    fi
    return 1
}

# 主逻辑
log "=== 看门狗检查开始 ==="

if check_service; then
    PID=$(cat "$PID_FILE")
    log "✅ 服务运行中 (PID: $PID)"
    
    # 额外检查端口
    if ! check_port; then
        log "⚠️  进程存在但端口 5000 未监听，可能已僵死"
        log "🔄 尝试重启服务..."
        "$WEBCTL" restart >> "$LOG_FILE" 2>&1
        if [ $? -eq 0 ]; then
            log "✅ 服务重启成功"
        else
            log "❌ 服务重启失败"
        fi
    fi
else
    log "❌ 服务未运行"
    log "🔄 尝试启动服务..."
    "$WEBCTL" start >> "$LOG_FILE" 2>&1
    if [ $? -eq 0 ]; then
        NEW_PID=$(cat "$PID_FILE" 2>/dev/null)
        log "✅ 服务已启动 (PID: $NEW_PID)"
    else
        log "❌ 服务启动失败，请检查日志"
    fi
fi

log "=== 看门狗检查结束 ==="
log ""
