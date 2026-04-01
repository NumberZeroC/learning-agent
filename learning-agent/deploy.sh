#!/bin/bash
# Learning Agent 快速部署脚本

set -e

echo "========================================"
echo "🚀 Learning Agent 部署脚本"
echo "========================================"
echo ""

WORKDIR="$(cd "$(dirname "$0")" && pwd)"
cd "$WORKDIR"

# 1. 检查 Python 环境
echo "📦 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi
echo "✅ Python3: $(python3 --version)"
echo ""

# 2. 安装依赖
echo "📦 安装依赖..."
pip3 install -r requirements.txt
echo "✅ 依赖安装完成"
echo ""

# 3. 检查配置文件
echo "📄 检查配置文件..."
if [ ! -f "config/agent_config.yaml" ]; then
    echo "❌ 配置文件不存在：config/agent_config.yaml"
    exit 1
fi
echo "✅ 配置文件检查通过"
echo ""

# 4. 检查环境变量
echo "🔐 检查环境变量..."
if [ ! -f ".env" ]; then
    echo "⚠️  .env 文件不存在，从 .env.example 复制..."
    cp .env.example .env
    echo "请编辑 .env 文件，填入 DASHSCOPE_API_KEY"
    echo ""
    read -p "按回车继续..."
fi

# 加载环境变量
export $(grep -v '^#' .env | xargs)

if [ -z "$DASHSCOPE_API_KEY" ]; then
    echo "❌ DASHSCOPE_API_KEY 未配置"
    exit 1
fi
echo "✅ 环境变量检查通过"
echo ""

# 5. 创建必要目录
echo "📁 创建必要目录..."
mkdir -p data/workflow_results
mkdir -p data/knowledge
mkdir -p logs
echo "✅ 目录创建完成"
echo ""

# 6. 启动服务（可选）
echo "========================================"
echo "✅ 部署完成！"
echo "========================================"
echo ""
echo "📂 工作目录：$WORKDIR"
echo ""
echo "下一步："
echo "  1. 编辑 .env 文件，填入你的 DASHSCOPE_API_KEY"
echo "  2. 运行工作流：python3 run_workflow.py"
echo "  3. 启动 Web 服务：cd web && python3 app.py"
echo ""
echo "或者使用一键启动："
echo "  ./start_workflow.sh    # 后台运行工作流"
echo "  cd web && ./start_web.sh  # 启动 Web 服务"
echo ""
