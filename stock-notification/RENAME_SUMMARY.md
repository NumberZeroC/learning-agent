# 🔄 项目重命名：Stock-Agent → Stock-Notification

**日期：** 2026-03-27  
**原因：** 更准确反映项目核心功能（股票通知推送）

---

## ✅ 完成的更改

### 1. 目录重命名

```bash
/workspace/stock-agent/          → /workspace/stock-notification/
/workspace/stock-agent-web/      → /workspace/stock-notification-web/
/data/stock-agent/               → /data/stock-notification/
```

### 2. 路径更新

**更新的文件：**
- `technical_analysis.py`
- `scheduled_technical_pick.py`
- `services/*.py`
- `CRON_SETUP.md`
- `TECHNICAL_ANALYSIS_README.md`
- `FEATURES_SUMMARY.md`
- `test_sector_change_sort.py`

**路径变更：**
```
/home/admin/.openclaw/workspace/stock-agent
→ /home/admin/.openclaw/workspace/stock-notification
```

### 3. 数据目录

**新路径：**
```bash
/home/admin/.openclaw/workspace/data/stock-notification/
├── reports/      # 分析报告
├── capital/      # 资金流数据
├── market/       # 市场数据
├── ai_news/      # AI 新闻数据
└── technical/    # 技术分析数据
```

**软链接：**
```bash
stock-notification/data → /home/admin/.openclaw/workspace/data/stock-notification
```

---

## 📋 新项目名称

| 项目 | 新名称 |
|------|--------|
| 主程序目录 | `stock-notification` |
| Web 服务目录 | `stock-notification-web` |
| 数据目录 | `data/stock-notification` |

---

## 🔧 使用方式

### 执行脚本

```bash
# 晚间分析
/home/admin/.openclaw/workspace/stock-notification/venv311/bin/python3 evening_analysis.py

# 早盘推荐
/home/admin/.openclaw/workspace/stock-notification/venv311/bin/python3 morning_recommend.py

# 技术指标选股
/home/admin/.openclaw/workspace/stock-notification/venv311/bin/python3 technical_analysis.py --limit 10

# 定时执行
/home/admin/.openclaw/workspace/stock-notification/venv311/bin/python3 scheduled_technical_pick.py
```

### 测试脚本

```bash
/home/admin/.openclaw/workspace/stock-notification/test_technical.sh
```

### 查看文档

```bash
cat /home/admin/.openclaw/workspace/stock-notification/FEATURES_SUMMARY.md
cat /home/admin/.openclaw/workspace/stock-notification/CRON_SETUP.md
cat /home/admin/.openclaw/workspace/stock-notification/TECHNICAL_ANALYSIS_README.md
```

---

## 📅 Cron 任务更新

如需更新 cron 任务，运行：

```bash
crontab -e
```

**新的 cron 配置：**

```cron
# 晚间总结（每个交易日 20:00）
0 20 * * 1-5 cd /home/admin/.openclaw/workspace/stock-notification && /home/admin/.openclaw/workspace/stock-notification/venv311/bin/python3 evening_analysis.py >> logs/evening.log 2>&1

# 早盘推荐（每个交易日 9:00）
0 9 * * 1-5 cd /home/admin/.openclaw/workspace/stock-notification && /home/admin/.openclaw/workspace/stock-notification/venv311/bin/python3 morning_recommend.py >> logs/morning.log 2>&1

# 技术选股（交易日每 30 分钟）
*/30 9-11 * * 1-5 cd /home/admin/.openclaw/workspace/stock-notification && /home/admin/.openclaw/workspace/stock-notification/venv311/bin/python3 scheduled_technical_pick.py >> logs/technical.log 2>&1
*/30 13-14 * * 1-5 cd /home/admin/.openclaw/workspace/stock-notification && /home/admin/.openclaw/workspace/stock-notification/venv311/bin/python3 scheduled_technical_pick.py >> logs/technical.log 2>&1
```

---

## 🌐 Web 服务

### 启动

```bash
cd /home/admin/.openclaw/workspace/stock-notification-web
source venv/bin/activate  # 如果有虚拟环境
python app.py
```

### 访问

```
http://localhost:5000
```

### API 端点

```
GET /api/v1/data/overview        # 概览数据
GET /api/v1/data/market          # 市场数据
GET /api/v1/data/capital/sectors # 板块资金流
GET /api/v1/data/ai-news         # AI 新闻
GET /api/v1/sectors/rank         # 板块排名
```

---

## 📝 待办事项

### 可选更新

1. **更新 HEARTBEAT.md** - 如果使用心跳检查
2. **更新通知脚本** - 如果有其他脚本引用旧路径
3. **更新文档链接** - 内部文档中的相对链接

### 检查清单

- [x] 主目录重命名
- [x] Web 服务目录重命名
- [x] 数据目录迁移
- [x] Python 脚本路径更新
- [x] 文档路径更新
- [ ] Cron 任务更新（需要手动执行）
- [ ] 其他引用检查

---

## 🔍 验证

```bash
# 检查目录
ls -la /home/admin/.openclaw/workspace/stock-notification/

# 检查数据目录
ls -la /home/admin/.openclaw/workspace/data/stock-notification/

# 运行测试
cd /home/admin/.openclaw/workspace/stock-notification
./test_technical.sh
```

---

*重命名完成时间：2026-03-27 08:36*
