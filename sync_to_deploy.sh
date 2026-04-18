#!/bin/bash
#
# Learning Agent 知识数据同步脚本（简化版）
# 用途：将源码目录的 workflow_results 同步到 /opt/learning-agent 部署目录
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="/opt/learning-agent"
SRC_DATA="$SCRIPT_DIR/data/workflow_results"
DST_DATA="$DEPLOY_DIR/data/workflow_results"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "📦 Learning Agent 数据同步"
echo "=========================================="
echo ""

# 检查源目录
if [ ! -d "$SRC_DATA" ]; then
    echo -e "${RED}❌ 错误：源目录不存在${NC}"
    echo "   $SRC_DATA"
    exit 1
fi

# 检查目标目录
if [ ! -d "$DST_DATA" ]; then
    echo -e "${YELLOW}⚠️  目标目录不存在，尝试创建...${NC}"
    sudo mkdir -p "$DST_DATA"
    sudo chown $(whoami):$(whoami) "$DST_DATA"
fi

echo "📋 同步信息:"
echo "   源目录：$SRC_DATA"
echo "   目标目录：$DST_DATA"
echo ""

# 统计源文件
SRC_COUNT=$(ls -1 "$SRC_DATA" 2>/dev/null | wc -l)
echo "📊 源目录文件数：$SRC_COUNT"

# 同步文件（使用 rsync 或 cp）
echo ""
echo "🔄 开始同步..."

if command -v rsync &> /dev/null; then
    # 使用 rsync（更高效）
    rsync -av --delete "$SRC_DATA/" "$DST_DATA/"
else
    # 使用 cp
    sudo cp -r "$SRC_DATA"/* "$DST_DATA/" 2>/dev/null || true
fi

# 修复权限（如果需要）
if [ "$(stat -c '%U' "$DST_DATA" 2>/dev/null)" = "root" ]; then
    echo ""
    echo -e "${YELLOW}⚠️  检测到权限问题，正在修复...${NC}"
    sudo chown -R $(whoami):$(whoami) "$DST_DATA" 2>/dev/null || true
fi

# 统计目标文件
DST_COUNT=$(ls -1 "$DST_DATA" 2>/dev/null | wc -l)
echo -e "${GREEN}✅ 同步完成！${NC}"
echo ""
echo "📊 同步结果:"
echo "   目标目录文件数：$DST_COUNT"
echo ""

# 显示最新文件
echo "📁 最新文件:"
ls -lht "$DST_DATA" | head -6
echo ""

# Docker 容器提示
if docker ps 2>/dev/null | grep -q learning-agent-public; then
    echo "💡 提示：Docker 容器正在运行"
    echo "   由于使用 volume 挂载，数据已实时更新"
    echo "   容器内可立即访问最新数据"
    echo ""
else
    echo "💡 提示：Docker 容器未运行"
    echo "   启动容器后数据将自动加载"
    echo ""
fi

echo "📁 部署目录：$DEPLOY_DIR"
echo "🌐 访问地址：http://localhost:32015/"
echo ""
