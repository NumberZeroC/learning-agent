#!/bin/bash
# AI 新闻每日推送 - stock-notification 集成版
# 每天晚上 8 点执行，推送到 QQ

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/ai_news_$(date +%Y-%m-%d).log"

echo "🚀 [$(date '+%Y-%m-%d %H:%M:%S')] 开始执行 AI 新闻推送" | tee -a "$LOG_FILE"

# 切换到 stock-notification 目录
cd /home/admin/.openclaw/workspace/stock-notification

# 使用 stock-notification 的 Python 环境执行，启用全文抓取
export AI_NEWS_FULL_CONTENT=true
./venv311/bin/python3 src/ai_news_monitor.py --once --full-content >> "$LOG_FILE" 2>&1

echo "✅ [$(date '+%Y-%m-%d %H:%M:%S')] 任务完成" | tee -a "$LOG_FILE"
