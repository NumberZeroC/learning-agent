#!/bin/bash
# 测试 API Key 热更新功能

set -e

echo "========================================"
echo "🔥 API Key 热更新测试"
echo "========================================"
echo ""

# 1. 检查服务是否运行
echo "📊 步骤 1: 检查服务状态"
if curl -s http://localhost:5001/health | grep -q "healthy"; then
    echo "✅ Web 服务运行正常"
else
    echo "❌ Web 服务未运行"
    exit 1
fi
echo ""

# 2. 查看当前 API Key 配置
echo "📊 步骤 2: 查看当前 API Key 配置"
API_KEY=$(grep "api_key_value:" /home/admin/.openclaw/workspace/learning-agent/config/agent_config.yaml | awk '{print $2}')
echo "   当前 API Key: ${API_KEY:0:20}..."
echo ""

# 3. 测试聊天功能
echo "📊 步骤 3: 测试聊天功能"
RESPONSE=$(curl -s -X POST http://localhost:5001/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{"message":"测试热更新功能","agent":"master_agent"}')

if echo "$RESPONSE" | grep -q '"success":true\|"success": true'; then
    echo "✅ 聊天功能正常"
else
    echo "❌ 聊天功能失败"
    echo "   响应：$RESPONSE"
    exit 1
fi
echo ""

# 4. 查看日志确认 API Key 加载
echo "📊 步骤 4: 查看日志"
tail -5 /tmp/learning-agent.log | grep -E "DASHSCOPE|API" || echo "   无相关日志"
echo ""

echo "========================================"
echo "✅ 热更新测试完成！"
echo "========================================"
echo ""
echo "💡 测试说明："
echo "   1. 在配置页面修改 API Key"
echo "   2. 点击保存"
echo "   3. 立即发送聊天消息"
echo "   4. 如果成功，说明热更新生效"
echo ""
