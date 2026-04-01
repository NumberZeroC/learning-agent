# Daily Briefing 配置指南

## ✅ 已完成的配置

配置文件已更新：`~/.openclaw/openclaw.json`

### 当前配置

```json
{
  "skills": {
    "entries": {
      "daily-briefing": {
        "config": {
          "location": "Shanghai, China",
          "timezone": "Asia/Shanghai",
          "units": "C",
          "birthdays": {
            "enabled": true,
            "lookahead": 14
          },
          "calendar": {
            "enabled": true,
            "lookahead": 1
          },
          "reminders": {
            "enabled": true
          },
          "emails": {
            "enabled": false
          }
        }
      }
    }
  }
}
```

---

## 🔧 配置项说明

### 基础配置

| 配置项 | 当前值 | 说明 |
|--------|--------|------|
| `location` | Shanghai, China | 天气查询位置 |
| `timezone` | Asia/Shanghai | 时区 |
| `units` | C | 温度单位（C/F） |

### 生日提醒

| 配置项 | 当前值 | 说明 |
|--------|--------|------|
| `enabled` | true | 启用生日提醒 |
| `lookahead` | 14 | 提前多少天提醒 |
| `sources` | ["contacts"] | 来源（contacts/google） |

### 日历

| 配置项 | 当前值 | 说明 |
|--------|--------|------|
| `enabled` | true | 启用日历 |
| `lookahead` | 1 | 查看几天后的日程 |
| `sources` | ["google"] | 日历来源 |

### 提醒事项

| 配置项 | 当前值 | 说明 |
|--------|--------|------|
| `enabled` | true | 启用提醒 |
| `dueFilter` | today | 筛选条件（today/week/all） |
| `includePastDue` | true | 包含过期提醒 |

### 重要邮件

| 配置项 | 当前值 | 说明 |
|--------|--------|------|
| `enabled` | false | 启用邮件分析 |
| `limit` | 5 | 最多显示几封 |
| `unreadOnly` | true | 仅未读邮件 |

---

## 📝 自定义配置

### 修改位置

编辑配置文件：
```bash
nano ~/.openclaw/openclaw.json
```

### 示例：启用邮件功能

```json
"emails": {
  "enabled": true,
  "limit": 10,
  "sortNewest": true,
  "starredFirst": true,
  "unreadOnly": true
}
```

### 示例：修改城市

```json
"location": "Beijing, China"
```

---

## ⏰ 设置定时任务

### 方法 1：使用 crontab

```bash
crontab -e
```

添加以下内容（每天早上 8:00）：
```
0 8 * * * /home/admin/.openclaw/workspace/daily_briefing_cron.sh
```

### 方法 2：使用 QQ Bot 定时提醒

```bash
# 通过 qqbot_remind 工具设置
```

---

## 🧪 测试运行

### 手动触发

```bash
# 在 OpenClaw 中直接说：
"生成每日简报"
或
"daily-briefing"
```

### 查看生成的数据

```bash
cat /tmp/daily_briefing_data.json
```

---

## 📊 输出示例

```
Good morning - Today is Tuesday, March 24, 2026. Partly cloudy skies, around 18°C this afternoon.

📅 **Today's schedule:**
• 9:00 AM: 团队站会
• 2:00 PM: 产品评审会

✅ **Reminders:**
• 取药

📧 **Emails needing attention:**
• 亚马逊：您的订单已发货

慢慢来，一步一步完成——你能做到的。
```

---

## 🔍 故障排查

### 天气不显示

检查位置配置：
```json
"location": "Shanghai, China"
```

### 日历不显示

确保已授权 Google Calendar 访问权限。

### 邮件不显示

邮件功能默认关闭，需要启用：
```json
"emails": {
  "enabled": true
}
```

---

## 📚 相关文档

- Skill 文档：`/home/admin/.openclaw/workspace/skills/daily-briefing/SKILL.md`
- 配置文件：`~/.openclaw/openclaw.json`

---

**最后更新：** 2026-03-24
