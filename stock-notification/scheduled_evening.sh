#!/bin/bash
#
# Stock-Agent 晚间分析定时任务
# 功能：执行晚间市场综合分析，生成总结报告
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
LOG_FILE="$LOG_DIR/evening_$(date +%Y%m%d).log"
REPORT_LOG="$LOG_DIR/cron_evening.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_to_report() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$REPORT_LOG"
}

log "=========================================="
log "晚间市场分析开始"
log "=========================================="
log_to_report "=========================================="
log_to_report "$(date '+%Y-%m-%d %H:%M:%S') 晚间分析开始"

# 执行晚间分析
log "🌙 执行晚间市场综合分析..."
$PYTHON evening_analysis.py 2>&1 | tee -a "$LOG_FILE"

# 检查结果
if [ $? -eq 0 ]; then
    log "✅ 晚间分析完成"
    log_to_report "✅ 晚间分析完成"
else
    log "❌ 晚间分析失败"
    log_to_report "❌ 晚间分析失败"
fi

# 查找最新报告并发送通知
LATEST_REPORT=$(ls -t ./data/reports/evening_summary_*.md 2>/dev/null | head -1)
if [ -n "$LATEST_REPORT" ]; then
    log "📬 准备发送通知..."
    # 详细输出到日志
    ./venv311/bin/python notify_report.py --type evening --report "$LATEST_REPORT" 2>&1 | tee -a "$LOG_FILE"
    
    # 精简模式生成通知（用于发送）
    ./venv311/bin/python notify_report.py --type evening --report "$LATEST_REPORT" --quiet 2>/dev/null | ./send_notify.sh --stdin >> "$LOG_FILE" 2>&1
fi

log "=========================================="
log "晚间分析结束"
log "=========================================="
log_to_report "=========================================="
