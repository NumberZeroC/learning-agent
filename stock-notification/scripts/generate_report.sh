#!/bin/bash
# 报告生成总控脚本
# 功能：从已获取的数据生成报告

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/../logs"
mkdir -p "$LOG_DIR"

DATE=${1:-$(date +%Y%m%d)}
LOG_FILE="$LOG_DIR/report_gen_${DATE}.log"

echo "🚀 [$(date '+%Y-%m-%d %H:%M:%S')] 开始报告生成" | tee -a "$LOG_FILE"
echo "📅 交易日期：$DATE" | tee -a "$LOG_FILE"

cd "$SCRIPT_DIR/.."

# 生成晚间报告
./venv311/bin/python3 reporters/evening_reporter.py --date "$DATE" 2>&1 | tee -a "$LOG_FILE"

echo "✅ [$(date '+%Y-%m-%d %H:%M:%S')] 报告生成完成" | tee -a "$LOG_FILE"
