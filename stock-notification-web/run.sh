#!/bin/bash
# Stock-Agent Web 后台启动脚本

cd /home/admin/.openclaw/workspace/stock-agent-web

# 停止旧进程
pkill -f "python3 app.py" 2>/dev/null
sleep 2

# 创建日志目录
mkdir -p logs

# 后台启动
nohup python3 app.py > logs/web.log 2>&1 &
PID=$!

# 等待启动
sleep 5

# 检查状态
echo "=========================================="
echo "Stock-Agent Web 启动状态"
echo "=========================================="
echo ""
echo "进程 ID: $PID"
echo ""
echo "进程状态:"
ps aux | grep "python3 app.py" | grep -v grep || echo "未找到进程"
echo ""
echo "端口状态:"
netstat -tuln 2>/dev/null | grep 5000 || ss -tuln 2>/dev/null | grep 5000 || echo "端口未监听"
echo ""
echo "访问地址:"
echo "  内网：http://172.25.10.209:5000"
echo "  公网：http://39.97.249.78:5000"
echo ""
echo "测试访问:"
curl -s http://127.0.0.1:5000/api/v1/config 2>&1 | head -3 || echo "访问失败"
echo ""
echo "=========================================="
