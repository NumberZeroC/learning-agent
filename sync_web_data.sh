#!/bin/bash
#
# Learning Agent Web 数据同步脚本
# 用途：只同步 layer_*.json 文件到部署目录，删除冗余文件
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="/opt/learning-agent"
SRC_DIR="$SCRIPT_DIR/data/workflow_results"
DST_DIR="$DEPLOY_DIR/data/workflow_results"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "🌐 Learning Agent Web 数据同步"
echo "=========================================="
echo ""

# 检查源目录
if [ ! -d "$SRC_DIR" ]; then
    echo -e "${RED}❌ 错误：源目录不存在${NC}"
    exit 1
fi

# 检查目标目录
if [ ! -d "$DST_DIR" ]; then
    sudo mkdir -p "$DST_DIR"
    sudo chown $(whoami):$(whoami) "$DST_DIR"
fi

echo "📋 同步策略:"
echo "   ✅ 保留：layer_*.json (5 个层级的知识数据)"
echo "   ✅ 保留：*.db (SQLite 数据库，防止数据丢失)"
echo "   ❌ 删除：其他冗余文件"
echo ""

# 1. 先清理冗余文件
echo -e "${BLUE}🧹 步骤 1/3: 清理冗余文件...${NC}"
DELETED=0
cd "$DST_DIR"
for file in *; do
    if [ -f "$file" ]; then
        # 只保留 layer_*.json 文件（不包括.bak）
        if [[ ! "$file" =~ ^layer_[1-5]_workflow\.json$ ]]; then
            rm -f "$file" 2>/dev/null && echo "   ❌ 删除：$file" && ((DELETED++)) || true
        fi
    fi
done
cd - > /dev/null

if [ $DELETED -eq 0 ]; then
    echo "   ✅ 无需清理"
fi

# 2. 同步 layer 文件
echo ""
echo -e "${BLUE}📦 步骤 2/3: 同步 layer 文件...${NC}"
SYNCED=0
for i in 1 2 3 4 5; do
    src_file="$SRC_DIR/layer_${i}_workflow.json"
    dst_file="$DST_DIR/layer_${i}_workflow.json"
    if [ -f "$src_file" ]; then
        cp "$src_file" "$dst_file"
        echo "   ✅ layer_${i}_workflow.json"
        ((SYNCED++)) || true
    fi
done

# 同步数据库文件
echo ""
echo -e "${BLUE}💾 同步数据库文件...${NC}"
for db_file in learning_agent.db secrets.db; do
    src_db="$SCRIPT_DIR/data/$db_file"
    dst_db="$DEPLOY_DIR/data/$db_file"
    if [ -f "$src_db" ]; then
        cp "$src_db" "$dst_db"
        echo "   ✅ $db_file"
    fi
done

# 3. 验证结果
echo ""
echo -e "${BLUE}📊 步骤 3/3: 验证结果...${NC}"
CURRENT=$(ls -1 "$DST_DIR"/layer_*_workflow.json 2>/dev/null | wc -l)
echo "   当前文件：$CURRENT 个"

# 修复权限
sudo chown -R $(whoami):$(whoami) "$DST_DIR" 2>/dev/null || true

echo ""
echo -e "${GREEN}✅ 同步完成！${NC}"
echo ""

# 显示结果
echo "📊 统计:"
echo "   同步文件：$SYNCED 个"
echo "   删除文件：$DELETED 个"
echo "   保留文件：$CURRENT 个"
echo ""

echo "📁 部署目录:"
ls -lh "$DST_DIR" | awk 'NR<=10 {print "   " $9 " (" $5 ")"}'
echo ""

# Docker 提示
if docker ps 2>/dev/null | grep -q learning-agent-public; then
    echo -e "${GREEN}💡 Docker 容器运行中，数据已实时更新${NC}"
else
    echo -e "${YELLOW}💡 Docker 容器未运行${NC}"
fi

echo ""
echo "🌐 访问地址：http://localhost:32015/"
echo ""
