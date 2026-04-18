#!/bin/bash
#
# Learning Agent public-release 分支部署脚本
# 用途：打包镜像并部署到 /opt/learning-agent
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="/opt/learning-agent"
BRANCH="public-release"

echo "=========================================="
echo "🚀 Learning Agent 公开知识展示网站部署"
echo "=========================================="
echo ""
echo "📋 部署信息:"
echo "   分支：$BRANCH"
echo "   目标目录：$DEPLOY_DIR"
echo "   容器端口：32015"
echo ""

# 1. 切换到 public-release 分支
echo "📦 步骤 1/7: 切换到 $BRANCH 分支..."
git checkout $BRANCH
git pull origin $BRANCH 2>/dev/null || echo "   ⚠️  无法拉取远程分支，使用本地代码"
echo "   ✅ 完成"
echo ""

# 2. 创建部署目录
echo "📁 步骤 2/7: 创建部署目录..."
sudo mkdir -p $DEPLOY_DIR
sudo chown $(whoami):$(whoami) $DEPLOY_DIR
echo "   ✅ 完成"
echo ""

# 3. 复制源码
echo "📦 步骤 3/7: 复制源码到部署目录..."
rsync -av --delete \
    --exclude='.git' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='.ruff_cache' \
    --exclude='logs/*' \
    --exclude='data/llm_audit_logs/*' \
    --exclude='data/workflow_results/*' \
    --exclude='.env' \
    $SCRIPT_DIR/ $DEPLOY_DIR/
echo "   ✅ 完成"
echo ""

# 4. 复制生成的知识数据
echo "💾 步骤 4/7: 复制知识数据..."
if [ -d "$SCRIPT_DIR/data/workflow_results" ]; then
    mkdir -p $DEPLOY_DIR/data/workflow_results
    cp -r $SCRIPT_DIR/data/workflow_results/* $DEPLOY_DIR/data/workflow_results/ 2>/dev/null || true
    echo "   ✅ 工作流结果已复制"
fi

if [ -d "$SCRIPT_DIR/data/llm_audit_logs" ]; then
    mkdir -p $DEPLOY_DIR/data/llm_audit_logs
    cp -r $SCRIPT_DIR/data/llm_audit_logs/* $DEPLOY_DIR/data/llm_audit_logs/ 2>/dev/null || true
    echo "   ✅ 审计日志已复制"
fi

if [ -d "$SCRIPT_DIR/config" ]; then
    mkdir -p $DEPLOY_DIR/config
    cp -r $SCRIPT_DIR/config/* $DEPLOY_DIR/config/ 2>/dev/null || true
    echo "   ✅ 配置文件已复制"
fi
echo ""

# 5. 复制环境变量
echo "🔐 步骤 5/7: 配置环境变量..."
if [ -f "$SCRIPT_DIR/.env" ]; then
    # 复制 .env 并追加公开模式配置
    cp $SCRIPT_DIR/.env $DEPLOY_DIR/.env
    cat >> $DEPLOY_DIR/.env << EOF

# 公开模式配置（强制）
PUBLIC_MODE=true
HIDE_WORKFLOW_EXECUTION=true
HIDE_CONFIG_PAGE=true
EOF
    echo "   ✅ .env 已配置"
else
    # 创建最小 .env 文件
    cat > $DEPLOY_DIR/.env << EOF
# Learning Agent 公开知识展示网站
# 自动生成时间：$(date -Iseconds)

# 公开模式配置
PUBLIC_MODE=true
HIDE_WORKFLOW_EXECUTION=true
HIDE_CONFIG_PAGE=true

# 时区
TZ=Asia/Shanghai

# API Key（从原配置复制）
DASHSCOPE_API_KEY=
EOF
    echo "   ✅ .env 已创建（请手动配置 API Key）"
fi
echo ""

# 6. 构建 Docker 镜像
echo "🐳 步骤 6/7: 构建 Docker 镜像..."
cd $DEPLOY_DIR
docker build -f Dockerfile.public -t learning-agent:public-release .
echo "   ✅ 镜像构建完成"
echo ""

# 7. 启动容器
echo "🚀 步骤 7/7: 启动容器..."
docker compose -f docker-compose.public.yml down 2>/dev/null || true
docker compose -f docker-compose.public.yml up -d
echo ""

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 健康检查
echo ""
echo "🔍 健康检查..."
for i in {1..10}; do
    if curl -s http://localhost:32015/health > /dev/null 2>&1; then
        echo "   ✅ 服务健康检查通过"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "   ⚠️  服务启动中，请稍后检查"
    else
        echo "   等待中... ($i/10)"
        sleep 2
    fi
done

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo ""
echo "📊 服务信息:"
echo "   访问地址：http://localhost:32015/"
echo "   容器名称：learning-agent-public"
echo "   镜像版本：learning-agent:public-release"
echo ""
echo "📋 管理命令:"
echo "   查看日志：docker logs -f learning-agent-public"
echo "   停止服务：docker compose -f docker-compose.public.yml down"
echo "   重启服务：docker compose -f docker-compose.public.yml restart"
echo "   查看状态：docker ps | grep learning-agent-public"
echo ""
echo "📁 数据目录:"
echo "   知识数据：$DEPLOY_DIR/data/workflow_results"
echo "   审计日志：$DEPLOY_DIR/data/llm_audit_logs"
echo "   应用日志：$DEPLOY_DIR/logs"
echo ""
echo "🔒 安全提示:"
echo "   - 公开模式已启用"
echo "   - 工作流执行已隐藏"
echo "   - 配置管理已隐藏"
echo "   - 聊天功能已隐藏"
echo ""
