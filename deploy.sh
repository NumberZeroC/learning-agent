#!/bin/bash
# Learning Agent 部署脚本

set -e

PROJECT_DIR="/home/admin/.openclaw/workspace/learning-agent"
SERVICE_NAME="learning-agent"
SERVICE_FILE="$PROJECT_DIR/learning-agent.service"

echo "🚀 Learning Agent 部署脚本"
echo "=========================="
echo ""

# 检查是否在正确目录
if [ ! -f "$PROJECT_DIR/web/app.py" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    exit 1
fi

echo "✅ 项目目录：$PROJECT_DIR"

# 检查虚拟环境
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "❌ 错误：虚拟环境不存在"
    exit 1
fi
echo "✅ 虚拟环境：已找到"

# 检查 .env 文件
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "⚠️  警告：.env 文件不存在，请创建并配置 API Key"
    echo "   创建命令：cp .env.example .env"
    echo "   然后编辑 .env 文件设置 DASHSCOPE_API_KEY"
fi
echo "✅ 环境变量：已配置"

# 初始化数据库
echo ""
echo "📊 初始化数据库..."
cd "$PROJECT_DIR"
source venv/bin/activate
python3 -c "from models.database import initialize; initialize()"
echo "✅ 数据库初始化完成"

# 安装 systemd 服务
echo ""
echo "🔧 安装 systemd 服务..."
SERVICE_DEST="/etc/systemd/system/$SERVICE_NAME.service"

if [ -f "$SERVICE_DEST" ]; then
    echo "⚠️  服务已存在，备份旧配置..."
    sudo cp "$SERVICE_DEST" "${SERVICE_DEST}.bak"
fi

sudo cp "$SERVICE_FILE" "$SERVICE_DEST"
echo "✅ 服务文件已复制到：$SERVICE_DEST"

# 重载 systemd
echo ""
echo "🔄 重载 systemd 配置..."
sudo systemctl daemon-reload
echo "✅ systemd 配置已重载"

# 启用服务
echo ""
echo "⚙️  启用服务（开机自启）..."
sudo systemctl enable $SERVICE_NAME
echo "✅ 服务已启用"

# 启动服务
echo ""
echo "🚀 启动服务..."
sudo systemctl start $SERVICE_NAME
echo "✅ 服务已启动"

# 检查状态
echo ""
echo "📊 服务状态:"
sudo systemctl status $SERVICE_NAME --no-pager | head -15

# 验证 Web 服务
echo ""
echo "🧪 验证 Web 服务..."
sleep 3
if curl -s http://localhost:5001/health | grep -q "healthy"; then
    echo "✅ Web 服务运行正常"
else
    echo "⚠️  Web 服务可能未正常启动，请查看日志："
    echo "   sudo journalctl -u $SERVICE_NAME -f"
fi

echo ""
echo "=========================="
echo "✅ 部署完成！"
echo ""
echo "常用命令:"
echo "  查看状态：sudo systemctl status $SERVICE_NAME"
echo "  查看日志：sudo journalctl -u $SERVICE_NAME -f"
echo "  重启服务：sudo systemctl restart $SERVICE_NAME"
echo "  停止服务：sudo systemctl stop $SERVICE_NAME"
echo "  启动服务：sudo systemctl start $SERVICE_NAME"
echo ""
echo "Web 服务地址：http://localhost:5001"
echo "健康检查：http://localhost:5001/health"
echo ""
