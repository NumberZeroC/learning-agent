#!/bin/bash
#
# Stock-Agent 交易时间定时监控脚本
# 功能：交易时间每 30 分钟监控一次持仓
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 设置环境变量
export TUSHARE_TOKEN="0b8ed09db7d7e733c133a04fad31fc34ff4938afd57f7766cfc6a3f2"

PYTHON="./venv311/bin/python"
LOG_DIR="./logs"

# 确保日志目录存在
mkdir -p "$LOG_DIR"

# 日志文件
LOG_FILE="$LOG_DIR/monitor_$(date +%Y%m%d).log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "Stock-Agent 定时监控启动"
log "=========================================="

# 执行监控
log "🎯 执行持仓监控..."
$PYTHON monitor.py --once --export 2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    log "✅ 监控完成"
    
    # 查找最新报告并发送通知（只在有买入/卖出信号时发送）
    LATEST_REPORT=$(ls -t ./data/reports/stock_monitor_*.md 2>/dev/null | head -1)
    if [ -n "$LATEST_REPORT" ]; then
        # 检查是否有强信号
        LATEST_JSON=$(ls -t ./data/reports/stock_monitor_*.json 2>/dev/null | head -1)
        if [ -n "$LATEST_JSON" ]; then
            # 检查是否有 STRONG_BUY 或 STRONG_SELL 信号
            HAS_STRONG_SIGNAL=$(cat "$LATEST_JSON" | grep -E '"signal":\s*"(STRONG_BUY|STRONG_SELL)"' | head -1)
            if [ -n "$HAS_STRONG_SIGNAL" ]; then
                log "📬 发现强信号，准备发送通知..."
                # 详细输出到日志
                ./venv311/bin/python notify_report.py --type monitor --report "$LATEST_REPORT" 2>&1 | tee -a "$LOG_FILE"
                
                # 精简模式生成通知（用于发送）
                ./venv311/bin/python notify_report.py --type monitor --report "$LATEST_REPORT" --quiet 2>/dev/null | ./send_notify.sh --stdin >> "$LOG_FILE" 2>&1
            fi
        fi
    fi
else
    log "❌ 监控失败 (退出码：$EXIT_CODE)"
fi
log "=========================================="

exit $EXIT_CODE
