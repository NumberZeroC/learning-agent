# HEARTBEAT.md

# Keep this file empty (or with only comments) to skip heartbeat API calls.

# Add tasks below when you want the agent to check something periodically.

---

## 📬 Stock-Agent 报告通知检查

检查股票分析报告完成通知，如有新通知则通过 QQ 推送给用户。

**检查命令：**
```bash
/home/admin/.openclaw/workspace/stock-agent/check_notifications.py
```

**如果有通知：**
1. 读取通知内容
2. 使用 `message` 工具发送到 QQ（channel=qqbot, to=qqbot:c2c:6BD7A1BCF3F92369D0580647287C0D52）
3. 标记通知为已发送（删除或移动文件）

**检查频率：** 每 30-60 分钟（交易时间可更频繁）

**通知类型：**
- 🌙 晚间总结（20:00 后）
- 📈 早盘推荐（9:30 后）
- 🎯 持仓监控（有强信号时）
