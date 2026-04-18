#!/bin/bash
#
# Learning Agent public-release 分支 - Docker 部署脚本
# 用途：打包镜像并部署到 /opt/learning-agent
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="/opt/learning-agent"
BRANCH="public-release"
SERVICE_NAME="learning-agent-public"

echo "=========================================="
echo "🐳 Learning Agent Docker 部署"
echo "=========================================="
echo ""
echo "📋 部署信息:"
echo "   分支：$BRANCH"
echo "   目标目录：$DEPLOY_DIR"
echo "   容器端口：32015"
echo "   运行方式：Docker 容器"
echo ""

# 1. 切换到 public-release 分支
echo "📦 步骤 1/7: 切换到 $BRANCH 分支..."
git checkout $BRANCH
echo "   ✅ 完成"
echo ""

# 2. 停止旧服务
echo "🛑 步骤 2/7: 停止旧服务..."
sudo systemctl stop $SERVICE_NAME 2>/dev/null || true
sudo systemctl disable $SERVICE_NAME 2>/dev/null || true
docker stop $SERVICE_NAME 2>/dev/null || true
docker rm $SERVICE_NAME 2>/dev/null || true
echo "   ✅ 完成"
echo ""

# 3. 创建部署目录
echo "📁 步骤 3/7: 创建部署目录..."
sudo mkdir -p $DEPLOY_DIR
sudo chown $(whoami):$(whoami) $DEPLOY_DIR
echo "   ✅ 完成"
echo ""

# 4. 复制源码
echo "📦 步骤 4/7: 复制源码到部署目录..."
cd $SCRIPT_DIR
for dir in web config docs services utils scripts; do
    if [ -d "$SCRIPT_DIR/$dir" ]; then
        cp -r "$SCRIPT_DIR/$dir" $DEPLOY_DIR/
    fi
done
cp *.py $DEPLOY_DIR/ 2>/dev/null || true
cp requirements.txt $DEPLOY_DIR/
cp Dockerfile.public docker-compose.public.yml $DEPLOY_DIR/
echo "   ✅ 完成"
echo ""

# 5. 复制知识数据
echo "💾 步骤 5/7: 复制知识数据..."
mkdir -p $DEPLOY_DIR/data/{workflow_results,llm_audit_logs,logs}
cp -r $SCRIPT_DIR/data/workflow_results/* $DEPLOY_DIR/data/workflow_results/ 2>/dev/null || true
cp -r $SCRIPT_DIR/data/llm_audit_logs/* $DEPLOY_DIR/data/llm_audit_logs/ 2>/dev/null || true
echo "   ✅ 完成"
echo ""

# 6. 配置环境变量
echo "🔐 步骤 6/7: 配置环境变量..."
cat > $DEPLOY_DIR/.env << EOF
# Learning Agent 公开知识展示网站 - Docker 部署
# 部署时间：$(date -Iseconds)

# 公开模式配置（强制）
PUBLIC_MODE=true
HIDE_WORKFLOW_EXECUTION=true
HIDE_CONFIG_PAGE=true

# 时区
TZ=Asia/Shanghai

# API Key（从原配置复制）
DASHSCOPE_API_KEY=$(grep DASHSCOPE_API_KEY $SCRIPT_DIR/.env 2>/dev/null | cut -d'=' -f2 || echo "")
EOF
echo "   ✅ .env 已配置"
echo ""

# 7. 构建并启动容器
echo "🐳 步骤 7/7: 构建 Docker 镜像并启动容器..."
cd $DEPLOY_DIR

# 停止旧容器
docker compose -f docker-compose.public.yml down 2>/dev/null || true

# 构建镜像
echo "   📦 构建镜像..."
docker build -f Dockerfile.public -t learning-agent:public-release .

# 启动容器
echo "   🚀 启动容器..."
docker compose -f docker-compose.public.yml up -d

echo "   ✅ 完成"
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
echo "✅ Docker 部署完成！"
echo "=========================================="
echo ""
echo "📊 服务信息:"
echo "   访问地址：http://localhost:32015/"
echo "   容器名称：$SERVICE_NAME"
echo "   镜像版本：learning-agent:public-release"
echo "   部署目录：$DEPLOY_DIR"
echo ""
echo "📋 管理命令:"
echo "   查看状态：docker ps | grep $SERVICE_NAME"
echo "   查看日志：docker logs -f $SERVICE_NAME"
echo "   停止服务：docker compose -f docker-compose.public.yml down"
echo "   重启服务：docker compose -f docker-compose.public.yml restart"
echo "   进入容器：docker exec -it $SERVICE_NAME bash"
echo ""
echo "📁 数据目录:"
echo "   知识数据：$DEPLOY_DIR/data/workflow_results"
echo "   审计日志：$DEPLOY_DIR/data/llm_audit_logs"
echo "   应用日志：docker logs $SERVICE_NAME"
echo ""
echo "🔒 安全提示:"
echo "   - 公开模式已启用"
echo "   - 工作流/聊天/配置已隐藏"
echo "   - 容器化隔离运行"
echo ""
