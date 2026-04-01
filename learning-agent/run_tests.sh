#!/bin/bash
# Learning Agent 测试运行脚本

set -e

WORKDIR="$(cd "$(dirname "$0")" && pwd)"
cd "$WORKDIR"

echo "========================================"
echo "🧪 Learning Agent 测试套件"
echo "========================================"
echo ""

# 检查 pytest 是否安装
if ! command -v pytest &> /dev/null; then
    echo "⚠️  pytest 未安装，正在安装..."
    pip3 install pytest pytest-mock pytest-cov
fi

# 设置测试环境变量
export DASHSCOPE_API_KEY="sk-test-mock-key"
export LEARNING_AGENT_TOKEN="test-token"

# 运行测试
echo "📦 运行单元测试..."
echo ""

if [ "$1" == "--coverage" ]; then
    # 带覆盖率测试
    pytest tests/ \
        --cov=. \
        --cov-report=html \
        --cov-report=term-missing \
        -v
    echo ""
    echo "📊 覆盖率报告已生成：htmlcov/index.html"
else
    # 普通测试
    pytest tests/ -v
fi

echo ""
echo "========================================"
echo "✅ 测试完成！"
echo "========================================"
