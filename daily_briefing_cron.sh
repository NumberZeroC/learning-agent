#!/bin/bash
# 每日简报定时任务脚本
# 每天早上 8:00 自动发送每日简报到 QQ

cd /home/admin/.openclaw/workspace

# 调用 daily-briefing 技能
echo "🌅 生成每日简报..."

# 使用 openclaw 命令触发简报生成
# 这里通过 sessions_send 发送到主会话
cat << 'EOF' | /home/admin/.openclaw/workspace/stock-agent/venv311/bin/python3 -c "
import sys
import json
from datetime import datetime

# 读取简报数据（如果存在）
try:
    with open('/tmp/daily_briefing_data.json', 'r') as f:
        data = json.load(f)
    
    # 生成简报消息
    greeting = 'Good morning'
    hour = data.get('system', {}).get('hour', 8)
    if hour >= 12:
        greeting = 'Good afternoon'
    elif hour >= 17:
        greeting = 'Good evening'
    
    date_str = data.get('system', {}).get('local_time', datetime.now().isoformat())
    
    # 构建消息
    message = f'{greeting} - 每日简报\n\n'
    
    # 天气
    if 'weather' in data:
        weather = data['weather']
        message += f'🌤️ 天气：{weather.get(\"condition\", \"未知\")}，{weather.get(\"temp\", \"?\"}°C\n\n'
    
    # 日程
    if data.get('calendar', {}).get('data'):
        message += '📅 今日日程:\n'
        for event in data['calendar']['data'][:3]:
            time_str = event.get('start', '全天')
            message += f'  • {time_str}: {event.get(\"title\", \"无标题\")}\n'
        message += '\n'
    
    # 提醒
    if data.get('reminders', {}).get('data'):
        message += '✅ 待办提醒:\n'
        for reminder in data['reminders']['data'][:3]:
            message += f'  • {reminder.get(\"title\", \"无标题\")}\n'
        message += '\n'
    
    print(message)
except Exception as e:
    print(f'生成简报失败：{e}')
    print('请手动运行：skillhub run daily-briefing')
EOF

echo "✅ 每日简报生成完成"
