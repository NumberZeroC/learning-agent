#!/bin/bash
# HiClaw 一键启动脚本
# 公网 IP: 39.97.249.78
# 创建时间：2026-03-31

set -e

PUBLIC_IP="39.97.249.78"
ENV_FILE="${HOME}/hiclaw-manager.env"
MANAGER_IMAGE="higress-registry.cn-hangzhou.cr.aliyuncs.com/higress/hiclaw-manager:v1.0.8"
DOCKER_PROXY_IMAGE="higress-registry.cn-hangzhou.cr.aliyuncs.com/higress/hiclaw-docker-proxy:v1.0.8"

# 颜色输出
log() { echo -e "\033[36m[HiClaw]\033[0m $1"; }
error() { echo -e "\033[31m[HiClaw ERROR]\033[0m $1" >&2; exit 1; }
success() { echo -e "\033[32m[HiClaw SUCCESS]\033[0m $1"; }

echo ""
echo "========================================"
echo "🦞 HiClaw 一键启动"
echo "========================================"
echo "公网 IP: ${PUBLIC_IP}"
echo "启动时间：$(date)"
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    error "Docker 未安装"
fi

# 检查配置文件
if [ ! -f "${ENV_FILE}" ]; then
    error "配置文件不存在：${ENV_FILE}"
fi

log "配置文件：${ENV_FILE}"

# 创建 hiclaw-net 网络
log "创建 Docker 网络..."
docker network inspect hiclaw-net >/dev/null 2>&1 || docker network create hiclaw-net
success "hiclaw-net 网络已准备"

# 启动 Docker API Proxy
log "启动 Docker API Proxy..."
docker ps --format '{{.Names}}' | grep -q "^hiclaw-docker-proxy$" && {
    log "hiclaw-docker-proxy 已运行，跳过"
} || {
    docker run -d \
        --name hiclaw-docker-proxy \
        --network hiclaw-net \
        -v /var/run/docker.sock:/var/run/docker.sock \
        --security-opt label=disable \
        --restart unless-stopped \
        "${DOCKER_PROXY_IMAGE}"
    success "hiclaw-docker-proxy 已启动"
}

# 停止并删除旧容器
log "清理旧容器..."
docker stop hiclaw-manager 2>/dev/null && docker rm hiclaw-manager 2>/dev/null || true

# 启动 Manager 容器
log "启动 HiClaw Manager..."
docker run -d \
  --name hiclaw-manager \
  --env-file "${ENV_FILE}" \
  -e HOME=/root/manager-workspace \
  -w /root/manager-workspace \
  -e HOST_ORIGINAL_HOME=/home/admin \
  --network hiclaw-net \
  --network-alias matrix-local.hiclaw.io \
  --network-alias aigw-local.hiclaw.io \
  --network-alias fs-local.hiclaw.io \
  -e HICLAW_CONTAINER_API=http://hiclaw-docker-proxy:2375 \
  -p 0.0.0.0:5099:8080 \
  -p 0.0.0.0:5098:8001 \
  -p 0.0.0.0:5097:8088 \
  -p 0.0.0.0:5096:18888 \
  -v hiclaw-data:/root/hiclaw-fs \
  -v /home/admin/hiclaw-manager:/root/manager-workspace \
  -v /home/admin:/host-share \
  --restart unless-stopped \
  "${MANAGER_IMAGE}"

success "hiclaw-manager 已启动"

# 等待服务就绪
log "等待服务就绪..."
sleep 30

# 检查容器状态
if docker ps --format '{{.Names}}' | grep -q "^hiclaw-manager$"; then
    success "HiClaw Manager 运行正常"
else
    error "HiClaw Manager 启动失败"
fi

echo ""
echo "========================================"
echo "✅ HiClaw 启动成功！"
echo "========================================"
echo ""
echo "🌐 访问地址:"
echo "   Element Web:  http://${PUBLIC_IP}:5097/#/login"
echo "   Higress 控制台：http://${PUBLIC_IP}:5098"
echo "   OpenClaw 控制台：http://${PUBLIC_IP}:5096"
echo ""
echo "📱 移动端访问:"
echo "   Homeserver: http://${PUBLIC_IP}:5099"
echo ""
echo "🔐 登录信息:"
echo "   用户名：admin"
echo "   密码：HiClaw2026!"
echo ""
echo "📋 常用命令:"
echo "   查看日志：docker logs hiclaw-manager -f"
echo "   停止服务：bash ${HOME}/stop-hiclaw.sh"
echo "   重启服务：bash ${HOME}/restart-hiclaw.sh"
echo ""
echo "========================================"
