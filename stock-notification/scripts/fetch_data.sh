#!/bin/bash
# 数据获取总控脚本
# 功能：获取所有数据并存储

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/../logs"
mkdir -p "$LOG_DIR"

DATE=${1:-$(date +%Y%m%d)}
LOG_FILE="$LOG_DIR/data_fetch_${DATE}.log"

echo "🚀 [$(date '+%Y-%m-%d %H:%M:%S')] 开始数据获取" | tee -a "$LOG_FILE"
echo "📅 交易日期：$DATE" | tee -a "$LOG_FILE"

cd "$SCRIPT_DIR/.."

# 使用数据聚合服务一次性获取所有数据
./venv311/bin/python3 services/data_aggregator.py --date "$DATE" 2>&1 | tee -a "$LOG_FILE"

echo "✅ [$(date '+%Y-%m-%d %H:%M:%S')] 数据获取完成" | tee -a "$LOG_FILE"
