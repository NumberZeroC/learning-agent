#!/bin/bash
#
# public-release 分支部署脚本
# 基于 main 分支 Web，隐藏工作流执行和配置管理
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "🌐 Learning Agent 公开知识展示网站"
echo "=========================================="
echo ""
echo "📋 功能说明:"
echo "   ✅ 知识架构展示"
echo "   ✅ 知识点详情"
echo "   ✅ Web 聊天问答"
echo "   ❌ 工作流执行（已隐藏）"
echo "   ❌ 配置管理（已隐藏）"
echo ""

# 检查环境变量
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 设置公开模式
export PUBLIC_MODE=true

LOG_DIR="./logs"
mkdir -p "$LOG_DIR"

PORT=32015
DEBUG=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        *)
            echo "未知参数：$1"
            exit 1
            ;;
    esac
done

echo "📍 监听端口：$PORT"
echo "🔒 运行模式：公开只读"
echo "📄 日志文件：$LOG_DIR/web_public.log"
echo ""

# 启动服务
if [ "$DEBUG" = true ]; then
    echo "⚠️  调试模式已启用"
    echo ""
    ./venv/bin/python web/app.py --host 0.0.0.0 --port $PORT --debug
else
    nohup ./venv/bin/python web/app.py --host 0.0.0.0 --port $PORT > "$LOG_DIR/web_public.log" 2>&1 &
    PID=$!
    echo "✅ Web 服务已启动 (PID: $PID)"
    echo ""
    echo "访问地址：http://localhost:$PORT"
    echo ""
    echo "停止服务：./web/stop_web.sh"
    echo "查看日志：tail -f $LOG_DIR/web_public.log"
fi
