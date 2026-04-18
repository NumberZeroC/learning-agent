# Learning Agent 快捷命令

# 添加到 ~/.bashrc 或 ~/.bash_profile

# ============================================
# 工作目录快捷方式
# ============================================

# 进入 Learning Agent 工作目录
alias la='cd /home/admin/.openclaw/workspace/learning-agent'

# 进入 OpenClaw 工作目录
alias oc='cd /home/admin/.openclaw/workspace'

# ============================================
# Docker 管理命令
# ============================================

# 查看 Learning Agent 容器状态
alias la-status='docker ps | grep learning-agent'

# 查看 Learning Agent 日志
alias la-logs='docker logs -f learning-agent-public'

# 重启 Learning Agent 容器
alias la-restart='cd /opt/learning-agent && docker compose -f docker-compose.public.yml restart'

# 停止 Learning Agent 容器
alias la-stop='cd /opt/learning-agent && docker compose -f docker-compose.public.yml down'

# ============================================
# 数据同步命令
# ============================================

# 同步 Web 数据到部署目录
alias la-sync='cd /home/admin/.openclaw/workspace/learning-agent && ./sync_web_data.sh'

# ============================================
# 快速启动命令
# ============================================

# 进入工作目录并查看状态
la-status() {
    cd /home/admin/.openclaw/workspace/learning-agent
    echo "=== Learning Agent 状态 ==="
    echo ""
    echo "📁 当前目录：$(pwd)"
    echo ""
    echo "🐳 Docker 容器:"
    docker ps --filter "name=learning-agent" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "   未找到容器"
    echo ""
    echo "📊 部署目录:"
    ls -lh /opt/learning-agent/data/workflow_results/layer_*.json 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}' || echo "   未找到文件"
    echo ""
}

# 帮助信息
la-help() {
    echo "=========================================="
    echo "Learning Agent 快捷命令"
    echo "=========================================="
    echo ""
    echo "📁 目录切换:"
    echo "   la          - 进入 Learning Agent 目录"
    echo "   oc          - 进入 OpenClaw 工作目录"
    echo ""
    echo "🐳 Docker 管理:"
    echo "   la-status   - 查看容器状态"
    echo "   la-logs     - 查看容器日志"
    echo "   la-restart  - 重启容器"
    echo "   la-stop     - 停止容器"
    echo ""
    echo "📦 数据同步:"
    echo "   la-sync     - 同步 Web 数据到部署目录"
    echo ""
    echo "❓ 帮助:"
    echo "   la-help     - 显示帮助信息"
    echo ""
}

# 加载配置
echo "✅ Learning Agent 快捷命令已加载"
echo "💡 输入 'la-help' 查看可用命令"
