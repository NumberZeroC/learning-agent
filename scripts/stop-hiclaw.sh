#!/bin/bash
# HiClaw 一键停止脚本

set -e

log() { echo -e "\033[36m[HiClaw]\033[0m $1"; }
success() { echo -e "\033[32m[HiClaw SUCCESS]\033[0m $1"; }

echo ""
echo "========================================"
echo "🦞 HiClaw 停止服务"
echo "========================================"
echo ""

log "停止 hiclaw-manager..."
docker stop hiclaw-manager 2>/dev/null && success "hiclaw-manager 已停止" || log "hiclaw-manager 未运行"

log "停止 hiclaw-docker-proxy..."
docker stop hiclaw-docker-proxy 2>/dev/null && success "hiclaw-docker-proxy 已停止" || log "hiclaw-docker-proxy 未运行"

echo ""
success "HiClaw 服务已停止"
echo ""
echo "📋 重启服务：bash /home/admin/.openclaw/workspace/scripts/restart-hiclaw.sh"
echo "========================================"
