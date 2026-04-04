#!/bin/bash
# 🚀 Learning Agent 工作流启动脚本

set -e

# 获取脚本所在目录的父目录作为工作目录（相对路径）
WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGDIR="$WORKDIR/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOGFILE="$LOGDIR/workflow_$TIMESTAMP.log"

# 创建日志目录
mkdir -p "$LOGDIR"

cd "$WORKDIR"

echo "========================================"
echo "🤖 Learning Agent 工作流启动"
echo "========================================"
echo ""
echo "📂 工作目录：$WORKDIR"
echo "📄 日志文件：$LOGFILE"
echo "⏰ 启动时间：$(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查配置文件
if [ ! -f "config/agent_config.yaml" ]; then
    echo "❌ 配置文件不存在：config/agent_config.yaml"
    exit 1
fi

# 启动工作流
echo "🚀 启动工作流..."
echo ""

nohup python3 run_workflow.py > "$LOGFILE" 2>&1 &
PID=$!

echo "✅ 工作流已启动！"
echo ""
echo "========================================"
echo "📊 信息"
echo "========================================"
echo "   PID:        $PID"
echo "   日志：      $LOGFILE"
echo "   状态：      运行中"
echo ""
echo "========================================"
echo "📋 常用命令"
echo "========================================"
echo "   查看日志：     tail -f $LOGFILE"
echo "   查看进度：     ls -lh $WORKDIR/data/workflow_results/layer_*_partial.json"
echo "   查看进程：     ps aux | grep $PID | grep -v grep"
echo "   停止工作流：   kill $PID"
echo ""
echo "========================================"
echo ""
echo "💡 提示：工作流预计运行 15-30 分钟"
echo "   每层完成后会自动保存，可随时中断"
echo ""
