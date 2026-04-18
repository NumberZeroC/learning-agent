#!/bin/bash
#
# Learning Agent 知识数据同步脚本
# 用途：将源码目录的知识数据同步到 /opt/learning-agent 部署目录
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="/opt/learning-agent"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "📦 Learning Agent 知识数据同步"
echo "=========================================="
echo ""

# 检查源目录是否存在
if [ ! -d "$SCRIPT_DIR/data/workflow_results" ]; then
    echo -e "${RED}❌ 错误：源目录不存在${NC}"
    echo "   源目录：$SCRIPT_DIR/data/workflow_results"
    exit 1
fi

# 检查部署目录是否存在
if [ ! -d "$DEPLOY_DIR" ]; then
    echo -e "${YELLOW}⚠️  部署目录不存在，正在创建...${NC}"
    sudo mkdir -p $DEPLOY_DIR
    sudo chown $(whoami):$(whoami) $DEPLOY_DIR
fi

echo "📋 同步信息:"
echo "   源目录：$SCRIPT_DIR/data"
echo "   目标目录：$DEPLOY_DIR/data"
echo ""

# 1. 同步工作流结果
echo "📊 步骤 1/3: 同步工作流结果..."
if [ -d "$SCRIPT_DIR/data/workflow_results" ]; then
    mkdir -p $DEPLOY_DIR/data/workflow_results
    cp -r $SCRIPT_DIR/data/workflow_results/* $DEPLOY_DIR/data/workflow_results/ 2>/dev/null || true
    FILE_COUNT=$(ls -1 $DEPLOY_DIR/data/workflow_results/ 2>/dev/null | wc -l)
    echo -e "   ${GREEN}✅ 已同步 $FILE_COUNT 个文件${NC}"
else
    echo -e "   ${YELLOW}⚠️  工作流结果目录不存在${NC}"
fi

# 2. 同步 LLM 审计日志
echo "📝 步骤 2/3: 同步 LLM 审计日志..."
if [ -d "$SCRIPT_DIR/data/llm_audit_logs" ]; then
    mkdir -p $DEPLOY_DIR/data/llm_audit_logs
    cp -r $SCRIPT_DIR/data/llm_audit_logs/* $DEPLOY_DIR/data/llm_audit_logs/ 2>/dev/null || true
    FILE_COUNT=$(ls -1 $DEPLOY_DIR/data/llm_audit_logs/ 2>/dev/null | wc -l)
    echo -e "   ${GREEN}✅ 已同步 $FILE_COUNT 个文件${NC}"
else
    echo -e "   ${YELLOW}⚠️  LLM 审计日志目录不存在${NC}"
fi

# 3. 同步配置文件
echo "🔧 步骤 3/3: 同步配置文件..."
if [ -d "$SCRIPT_DIR/config" ]; then
    mkdir -p $DEPLOY_DIR/config
    cp -r $SCRIPT_DIR/config/* $DEPLOY_DIR/config/ 2>/dev/null || true
    FILE_COUNT=$(ls -1 $DEPLOY_DIR/config/ 2>/dev/null | wc -l)
    echo -e "   ${GREEN}✅ 已同步 $FILE_COUNT 个文件${NC}"
else
    echo -e "   ${YELLOW}⚠️  配置文件目录不存在${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅ 同步完成！${NC}"
echo "=========================================="
echo ""

# 显示同步后的数据统计
echo "📊 数据概览:"
echo "   工作流结果：$(ls -1 $DEPLOY_DIR/data/workflow_results/ 2>/dev/null | wc -l) 个文件"
echo "   LLM 审计日志：$(ls -1 $DEPLOY_DIR/data/llm_audit_logs/ 2>/dev/null | wc -l) 个文件"
echo "   配置文件：$(ls -1 $DEPLOY_DIR/config/ 2>/dev/null | wc -l) 个文件"
echo ""

# 如果部署了 Docker 容器，提示是否需要重启
if docker ps 2>/dev/null | grep -q learning-agent-public; then
    echo "💡 提示：Docker 容器正在运行"
    echo "   数据已挂载，容器内可立即访问最新数据"
    echo "   如需重启容器：docker compose -f $DEPLOY_DIR/docker-compose.public.yml restart"
    echo ""
fi

echo "📁 部署目录：$DEPLOY_DIR"
echo "🌐 访问地址：http://localhost:32015/"
echo ""
