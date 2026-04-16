#!/bin/bash
#
# Learning Agent 工作流后台运行脚本
# 功能：在后台启动完整工作流，支持日志查看和进度监控
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

LOG_DIR="./logs"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/workflow_full_${TIMESTAMP}.log"
PID_FILE="$LOG_DIR/workflow_${TIMESTAMP}.pid"

echo "=========================================="
echo "🚀 Learning Agent 工作流启动"
echo "=========================================="
echo ""
echo "📋 任务：生成 5 层知识体系（17 个主题）"
echo "⚙️  并发：3 任务/层"
echo "🔄 轮次：两轮生成（结构 + 详情）"
echo "⏱️  预计：25-35 分钟"
echo ""
echo "📄 日志文件：$LOG_FILE"
echo "🆔 进程 ID:  $PID_FILE"
echo ""
echo "监控命令："
echo "  查看实时日志：tail -f $LOG_FILE"
echo "  检查进程状态：ps aux | grep workflow_orchestrator"
echo "  查看进度：grep '✅ 完成' $LOG_FILE | wc -l"
echo ""
echo "=========================================="
echo ""

# 激活虚拟环境并启动工作流
nohup ./venv/bin/python -u run_workflow.py > "$LOG_FILE" 2>&1 &
PID=$!

echo $PID > "$PID_FILE"
echo "✅ 工作流已启动 (PID: $PID)"
echo ""

# 等待 5 秒后显示初始日志
sleep 5
echo "📋 初始日志："
tail -20 "$LOG_FILE"
echo ""
echo "💡 使用 'tail -f $LOG_FILE' 持续监控进度"
