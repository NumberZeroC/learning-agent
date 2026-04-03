#!/bin/bash
# CCP (Claude Code Python) 启动脚本
# 自动加载 .env 配置并启动交互模式

set -e

# 保存当前工作目录（用户启动时的目录）
USER_WORKDIR="$(pwd)"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 启动 CCP (Claude Code Python)..."
echo

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✓ 虚拟环境已激活"
else
    echo "✗ 错误：虚拟环境不存在 (.venv)"
    echo "  请先运行：uv venv && uv pip install -e ."
    exit 1
fi

# 加载 .env 文件
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✓ 配置已加载 (.env)"
else
    echo "⚠ 警告：.env 文件不存在"
    echo "  请复制 .env.example 并配置 API Key"
fi

# 返回用户原来的工作目录
cd "$USER_WORKDIR"
echo "📁 工作目录：$(pwd)"
echo

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# 启动 CCP 交互模式（传递工作目录参数）
ccp run -i -w "$USER_WORKDIR"
