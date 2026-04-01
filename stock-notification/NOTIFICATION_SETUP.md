# 📬 报告推送通知配置指南

## 功能说明

当股票分析任务完成后，系统会自动通过 QQ 推送通知给你。

### 推送类型

| 报告类型 | 触发时间 | 推送条件 |
|---------|---------|---------|
| 🌙 晚间总结 | 每个交易日 20:00 | 总是推送 |
| 📈 早盘推荐 | 每个交易日 9:30 | 总是推送 |
| 🎯 持仓监控 | 交易时间每 30 分钟 | 仅当有强信号（STRONG_BUY/STRONG_SELL）时推送 |

---

## 配置步骤

### 1. 已完成的配置

以下脚本已修改并准备好推送功能：

- ✅ `notify_report.py` - 通知内容生成脚本
- ✅ `send_notify.sh` - 通知发送脚本
- ✅ `scheduled_evening.sh` - 晚间分析（已添加推送）
- ✅ `scheduled_morning.sh` - 早盘推荐（已添加推送）
- ✅ `scheduled_monitor.sh` - 持仓监控（已添加推送，仅强信号）

### 2. 启用推送（两种方式）

#### 方式一：通过 Heartbeat 检查（推荐）

在 HEARTBEAT.md 中添加以下任务：

```markdown
# 检查股票报告通知
- 运行：`/home/admin/.openclaw/workspace/stock-agent/check_notifications.py`
- 如果有新通知，通过 QQ 发送给用户
- 检查频率：每 30-60 分钟
```

然后在你的 AI 会话中，当 heartbeat 触发时，AI 会：
1. 运行 `check_notifications.py`
2. 如果有新通知，使用 `message` 工具发送到 QQ

#### 方式二：直接集成到定时任务

如果需要实时推送（不依赖 heartbeat），需要配置 OpenClaw 的主动消息功能。

---

## 通知示例

### 晚间总结通知
```
🌙 晚间市场总结 已完成

📌 上证：3052.45 (+1.23%)

要点：
• 热点板块：半导体、人工智能、新能源
• 资金流入第 1：半导体 (125.3 万)

📄 报告：/home/admin/.openclaw/workspace/stock-agent/data/reports/evening_summary_2026-03-22.md

投资有风险，决策需谨慎
```

### 早盘推荐通知
```
📈 早盘推荐 已完成

📌 今日热点：半导体、人工智能、医药生物

要点：
• 半导体 龙头：中芯国际

📄 报告：/home/admin/.openclaw/workspace/stock-agent/data/reports/morning_recommend_2026-03-22.md

投资有风险，决策需谨慎
```

### 持仓监控通知（强信号）
```
🎯 持仓监控 已完成

📌 监控 10 只：买入 2 持有 7 卖出 1

要点：
• 🔴 买入 宁德时代 (300750)
• 🟢 卖出 比亚迪 (002594)

📄 报告：/home/admin/.openclaw/workspace/stock-agent/data/reports/stock_monitor_2026-03-22.md

投资有风险，决策需谨慎
```

---

## 测试推送

手动测试推送功能：

```bash
cd /home/admin/.openclaw/workspace/stock-agent

# 测试晚间报告通知
./venv311/bin/python notify_report.py --type evening --report ./data/reports/evening_summary_2026-03-22.md

# 发送通知到队列
./send_notify.sh "测试通知内容"
```

---

## 通知文件位置

- 通知队列目录：`/home/admin/.openclaw/workspace/stock-agent/data/notifications/`
- 通知文件格式：`notify_YYYYMMDD_HHMMSS.txt`

---

## 故障排查

### 通知未发送

1. 检查通知文件是否生成：
   ```bash
   ls -la /home/admin/.openclaw/workspace/stock-agent/data/notifications/
   ```

2. 检查定时任务日志：
   ```bash
   tail -f /home/admin/.openclaw/workspace/stock-agent/logs/cron_evening.log
   tail -f /home/admin/.openclaw/workspace/stock-agent/logs/cron_morning.log
   ```

3. 检查 cron 是否运行：
   ```bash
   crontab -l
   ```

### 推送延迟

如果使用 heartbeat 方式，推送会有延迟（取决于 heartbeat 频率）。
需要实时推送请配置方式二。

---

## 自定义通知内容

编辑 `notify_report.py` 中的 `send_notification()` 函数来自定义通知格式。

---

*最后更新：2026-03-22*
