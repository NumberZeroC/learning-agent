#!/bin/bash
#
# Learning Agent 快捷命令安装脚本
# 用途：将快捷命令添加到 ~/.bashrc
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ALIASES_FILE="$SCRIPT_DIR/.bash_aliases"
BASHRC="$HOME/.bashrc"

echo "=========================================="
echo "🔧 Learning Agent 快捷命令安装"
echo "=========================================="
echo ""

# 检查别名文件
if [ ! -f "$ALIASES_FILE" ]; then
    echo "❌ 错误：别名文件不存在"
    echo "   $ALIASES_FILE"
    exit 1
fi

# 检查是否已安装
if grep -q "Learning Agent 快捷命令" "$BASHRC" 2>/dev/null; then
    echo "⚠️  快捷命令已安装，跳过..."
    echo ""
else
    # 添加到 .bashrc
    echo "" >> "$BASHRC"
    echo "# ============================================" >> "$BASHRC"
    echo "# Learning Agent 快捷命令"
    echo "# 安装时间：$(date -Iseconds)" >> "$BASHRC"
    echo "# ============================================" >> "$BASHRC"
    echo "" >> "$BASHRC"
    echo "# 进入 Learning Agent 工作目录" >> "$BASHRC"
    echo "alias la='cd /home/admin/.openclaw/workspace/learning-agent'" >> "$BASHRC"
    echo "" >> "$BASHRC"
    echo "# 进入 OpenClaw 工作目录" >> "$BASHRC"
    echo "alias oc='cd /home/admin/.openclaw/workspace'" >> "$BASHRC"
    echo "" >> "$BASHRC"
    echo "# 同步 Web 数据" >> "$BASHRC"
    echo "alias la-sync='cd /home/admin/.openclaw/workspace/learning-agent && ./sync_web_data.sh'" >> "$BASHRC"
    echo "" >> "$BASHRC"
    echo "# Docker 管理" >> "$BASHRC"
    echo "alias la-status='docker ps | grep learning-agent'" >> "$BASHRC"
    echo "alias la-logs='docker logs -f learning-agent-public'" >> "$BASHRC"
    echo "alias la-restart='cd /opt/learning-agent && docker compose -f docker-compose.public.yml restart'" >> "$BASHRC"
    echo "" >> "$BASHRC"
    
    echo "✅ 快捷命令已添加到 ~/.bashrc"
    echo ""
fi

# 立即生效
if command -v source > /dev/null 2>&1; then
    source "$BASHRC"
    echo "✅ 配置已生效"
    echo ""
fi

# 显示使用说明
echo "=========================================="
echo "📚 使用说明"
echo "=========================================="
echo ""
echo "快捷命令:"
echo "   la          - 进入 Learning Agent 目录"
echo "   oc          - 进入 OpenClaw 工作目录"
echo "   la-sync     - 同步 Web 数据到部署目录"
echo "   la-status   - 查看容器状态"
echo "   la-logs     - 查看容器日志"
echo "   la-restart  - 重启容器"
echo ""
echo "示例:"
echo "   la          # 进入工作目录"
echo "   la-sync     # 同步数据"
echo "   la-status   # 查看状态"
echo ""
echo "💡 如果命令未生效，请执行：source ~/.bashrc"
echo ""
