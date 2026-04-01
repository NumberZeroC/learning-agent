#!/bin/bash
#
# Stock-Agent Web 启动脚本
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Stock-Agent Web 启动"
echo "=========================================="
echo ""

# 检查 Python 环境
if [ ! -d "venv311" ]; then
    echo "⚠️  未找到虚拟环境，使用系统 Python"
    PYTHON="python3"
else
    echo "✅ 使用虚拟环境"
    PYTHON="./venv311/bin/python"
fi

# 检查依赖
echo "📦 检查依赖..."
$PYTHON -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  安装依赖..."
    $PYTHON -m pip install -r requirements.txt -q
fi

# 启动
echo ""
echo "🚀 启动 Flask 应用..."
echo "   访问地址：http://localhost:5000"
echo "   API 地址：http://localhost:5000/api/v1"
echo ""
echo "按 Ctrl+C 停止"
echo "=========================================="
echo ""

$PYTHON app.py
