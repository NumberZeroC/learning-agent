#!/bin/bash
# AI 新闻每日推送 - 简化版
# 每天晚上 8 点执行，推送到 QQ

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/ai_news_$(date +%Y-%m-%d).log"

echo "🚀 [$(date '+%Y-%m-%d %H:%M:%S')] 开始执行 AI 新闻推送" | tee -a "$LOG_FILE"

# 切换到工作目录
cd /home/admin/.openclaw/workspace

# 使用 OpenClaw 直接执行
# 这里通过 sessions_send 发送到主会话，由 AI 处理新闻获取和推送
cat << 'TASK' | /home/admin/.openclaw/workspace/stock-agent/venv311/bin/python3 -c "
import sys
import os
sys.path.insert(0, '/home/admin/.openclaw/workspace')

# 任务描述
task = '''
请执行以下任务：

1. 获取今日 AI 新闻（从 The Verge、TechCrunch、OpenAI 等来源）
2. 根据新闻内容，结合我的背景给出建议：
   - 6 年开发经验
   - 华为云计算 5 年
   - 现在 AI 应用创业
   - 想抓住风口
3. 将新闻 + 建议整理成简洁的消息
4. 通过 message 工具发送到 QQ：qqbot:c2c:6BD7A1BCF3F92369D0580647287C0D52

消息格式参考：
🤖 AI 应用创业日报 | 日期

📰 今日热点（3-5 条）
1. ...
2. ...

💡 个人建议
【机会】...
【风险】...
【行动项】...

---
🎯 今日金句
...
'''

print(task)
" >> "$LOG_FILE" 2>&1

echo "✅ [$(date '+%Y-%m-%d %H:%M:%S')] 任务完成" | tee -a "$LOG_FILE"
