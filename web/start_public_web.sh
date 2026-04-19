#!/bin/bash
#
# Learning Agent 公开知识展示网站 - 生产环境启动脚本
#
# 用途：对外公开发布，只读展示知识内容
# 已禁用：聊天、配置、工作流执行
#
# 使用方法：
#   ./start_public_web.sh              # 默认 80 端口
#   ./start_public_web.sh --port 8080  # 自定义端口
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

LOG_DIR="./logs"
mkdir -p "$LOG_DIR"

# 解析参数
PORT=80
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
            echo "用法：$0 [--port PORT] [--debug]"
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "🌐 Learning Agent 公开知识展示网站"
echo "=========================================="
echo ""
echo "📍 监听端口：$PORT"
echo "🔒 运行模式：只读展示（PUBLIC_MODE=true）"
echo "✅ 已禁用：聊天、配置、工作流执行"
echo "📄 日志文件：$LOG_DIR/web_public.log"
echo ""

# 设置公开模式环境变量
export PUBLIC_MODE=true
export HIDE_WORKFLOW_EXECUTION=true
export HIDE_CONFIG_PAGE=true

# 启动服务
if [ "$DEBUG" = true ]; then
    echo "⚠️  调试模式已启用（生产环境请禁用）"
    echo ""
    python3 web/app.py --host 0.0.0.0 --port $PORT --debug
else
    nohup python3 web/app.py --host 0.0.0.0 --port $PORT > "$LOG_DIR/web_public.log" 2>&1 &
    PID=$!
    echo "✅ Web 服务已启动 (PID: $PID)"
    echo ""
    echo "访问地址：http://localhost:$PORT"
    echo ""
    echo "停止服务：./web/stop_web.sh"
    echo "查看日志：tail -f $LOG_DIR/web_public.log"
fi
