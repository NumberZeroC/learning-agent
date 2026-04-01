#!/bin/bash
#
# Stock-Notification-Web API 定时测试脚本
# 功能：每天 19:00 自动执行 Web API 测试
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 设置环境变量
export WEB_HOST="${WEB_HOST:-http://localhost:5000}"
export TEST_TIMEOUT="${TEST_TIMEOUT:-10}"
export TEST_SEND_NOTIFY="${TEST_SEND_NOTIFY:-false}"

# Python 环境
PYTHON="./venv311/bin/python3"

# 日志目录
LOG_DIR="./logs"
mkdir -p "$LOG_DIR"

# 日志文件
LOG_FILE="$LOG_DIR/test_$(date +%Y%m%d).log"

echo "=========================================="
echo "🧪 Web API 定时测试"
echo "=========================================="
echo "执行时间：$(date '+%Y-%m-%d %H:%M:%S')"
echo "Web 地址：$WEB_HOST"
echo "日志文件：$LOG_FILE"
echo "=========================================="
echo ""

# 检查 Web 服务是否运行
if ! curl -s --connect-timeout 5 "$WEB_HOST" > /dev/null; then
    echo "❌ Web 服务无法访问：$WEB_HOST" | tee -a "$LOG_FILE"
    echo "请检查 Web 服务是否正常运行" | tee -a "$LOG_FILE"
    exit 1
fi

echo "✅ Web 服务可访问" | tee -a "$LOG_FILE"
echo ""

# 执行测试
if [ -f "$PYTHON" ]; then
    "$PYTHON" test_web_api.py 2>&1 | tee -a "$LOG_FILE"
else
    # 回退到系统 Python
    python3 test_web_api.py 2>&1 | tee -a "$LOG_FILE"
fi

EXIT_CODE=${PIPESTATUS[0]}

echo ""
echo "=========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ 测试通过"
else
    echo "❌ 测试失败，请检查日志"
fi
echo "=========================================="

# 如果测试失败且启用了通知，发送告警
if [ $EXIT_CODE -ne 0 ] && [ "$TEST_SEND_NOTIFY" = "true" ]; then
    echo "发送失败通知..."
    # 这里可以添加通知发送逻辑
fi

exit $EXIT_CODE
