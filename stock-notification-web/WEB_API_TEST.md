# 🧪 Web API 定时测试

**创建时间：** 2026-03-29  
**执行时间：** 每天 19:00  
**状态：** ✅ 已配置

---

## 📋 功能说明

自动测试 stock-notification-web 项目的所有 API 接口：

1. **接口可用性检查** - 验证 HTTP 状态码
2. **数据格式验证** - 检查 JSON 返回格式
3. **数据内容验证** - 验证数据合理性
4. **性能监控** - 记录响应时间
5. **失败告警** - 测试失败时发送通知

---

## 📁 文件结构

```
stock-notification-web/
├── test_web_api.py          # 测试主脚本 ⭐
├── scheduled_test.sh        # 定时执行脚本
├── logs/
│   └── test_*.log          # 测试日志
└── WEB_API_TEST.md         # 本文档
```

---

## 🚀 使用方式

### 手动测试

```bash
cd /home/admin/.openclaw/workspace/stock-notification-web

# 基础测试
python3 test_web_api.py

# 发送通知
python3 test_web_api.py --send-notify

# 指定 Web 地址
export WEB_HOST=http://localhost:5000
python3 test_web_api.py
```

### 定时执行

```bash
# 安装 crontab
crontab /home/admin/.openclaw/workspace/stock-notification/crontab.txt

# 验证
crontab -l | grep "19:00"
```

---

## 📊 测试范围

### API 端点

| 序号 | 端点 | 功能 | 检查项 |
|------|------|------|--------|
| 1 | `/` | 首页 | HTTP 200, HTML 内容 |
| 2 | `/api/v1/reports/latest-data` | 最新报告 | code, data, 指数，板块 |
| 3 | `/api/v1/reports` | 报告列表 | code, data, 报告数量 |
| 4 | `/api/v1/data/market` | 市场数据 | code, data, 指数 |
| 5 | `/api/v1/data/capital/sectors` | 板块资金流 | code, data, 板块数量 |
| 6 | `/api/v1/data/ai-news` | AI 新闻 | code, data, 新闻列表 |
| 7 | `/api/v1/data/aggregated` | 聚合数据 | code, data |
| 8 | `/api/v1/monitor/stocks` | 持仓监控 | code, data, 股票列表 |

---

## ✅ 检查项

### 通用检查

- [x] HTTP 状态码 = 200
- [x] JSON 格式正确
- [x] API 返回码 = 200
- [x] data 字段存在

### 数据检查

| 检查项 | 期望值 | 说明 |
|--------|--------|------|
| **上证指数** | > 0 | 指数数据有效 |
| **板块资金流** | > 0 个 | 有板块数据 |
| **报告日期** | 非空 | 日期字段存在 |
| **数据完整性** | 字段完整 | 必要字段不缺失 |

---

## 📝 测试日志

### 日志位置

```
/home/admin/.openclaw/workspace/stock-notification-web/logs/test_YYYYMMDD_HHMMSS.log
```

### 日志格式

```
[2026-03-29 19:00:01] [INFO] ============================================================
[2026-03-29 19:00:01] [INFO] 开始 Web API 测试
[2026-03-29 19:00:01] [INFO] 目标：http://localhost:5000
[2026-03-29 19:00:01] [INFO] 测试端点：8 个
[2026-03-29 19:00:01] [INFO] ============================================================
[2026-03-29 19:00:01] [INFO] 
测试：首页
[2026-03-29 19:00:01] [INFO]   ✅ 状态：passed
[2026-03-29 19:00:01] [INFO]      HTTP: 200
[2026-03-29 19:00:01] [INFO]      耗时：50.23ms
[2026-03-29 19:00:01] [INFO]      [✓] HTTP 状态码：返回 200
...
```

---

## 🔔 通知配置

### 环境变量

```bash
# 启用通知
export TEST_SEND_NOTIFY=true

# Web 地址
export WEB_HOST=http://localhost:5000

# 超时时间（秒）
export TEST_TIMEOUT=10
```

### 通知内容

```
【Web API 测试报告】
状态：✅ 通过
时间：2026-03-29 19:00:05

测试结果：
• 总计：8 个接口
• 通过：8 ✅
• 警告：0 ⚠️
• 失败：0 ❌
• 通过率：100.0%

✅ 所有接口正常
```

---

## 📊 测试报告

### 执行摘要

每次测试完成后生成摘要：

```
============================================================
测试摘要
============================================================
总测试数：8
通过：8 ✅
警告：0 ⚠️
失败：0 ❌
通过率：100.0%
总耗时：234.56ms
日志文件：/home/admin/.openclaw/workspace/stock-notification-web/logs/test_20260329_190001.log
============================================================
```

### 退出码

| 退出码 | 含义 |
|--------|------|
| **0** | 所有测试通过 |
| **0** | 有警告但无失败 |
| **1** | 有测试失败 |

---

## 🔧 故障排查

### Web 服务无法访问

```bash
# 检查 Web 服务状态
ps aux | grep "python.*app.py"

# 检查端口监听
netstat -tlnp | grep 5000

# 重启 Web 服务
cd /home/admin/.openclaw/workspace/stock-notification-web
pkill -f "python.*app.py"
nohup python3 app.py > logs/web.log 2>&1 &
```

### 测试脚本报错

```bash
# 查看详细错误
cat logs/test_*.log | tail -50

# 手动执行测试
python3 test_web_api.py
```

### 数据验证失败

```bash
# 检查 API 返回
curl -s http://localhost:5000/api/v1/reports/latest-data | python3 -m json.tool

# 检查数据目录
ls -la /home/admin/.openclaw/workspace/data/stock-agent/reports/
```

---

## 📈 性能监控

### 响应时间标准

| 等级 | 响应时间 | 说明 |
|------|---------|------|
| **优秀** | < 100ms | 非常快 |
| **良好** | 100-500ms | 正常 |
| **一般** | 500-1000ms | 可接受 |
| **较慢** | > 1000ms | 需要优化 |

### 历史数据

测试日志会记录每次的响应时间，可用于：

- 性能趋势分析
- 问题定位
- 容量规划

---

## 🔄 定时任务配置

### Crontab 配置

```cron
# 每天 19:00 执行 Web API 测试
0 19 * * * /home/admin/.openclaw/workspace/stock-notification-web/scheduled_test.sh >> /home/admin/.openclaw/workspace/stock-notification-web/logs/cron_test.log 2>&1
```

### 验证配置

```bash
# 查看 crontab
crontab -l | grep "19:00"

# 查看定时任务日志
tail -f /home/admin/.openclaw/workspace/stock-notification-web/logs/cron_test.log
```

---

## 📞 快速命令

```bash
# 手动执行测试
cd /home/admin/.openclaw/workspace/stock-notification-web
python3 test_web_api.py

# 查看最新测试结果
ls -lt logs/test_*.log | head -1 | awk '{print $NF}' | xargs tail -50

# 查看定时任务状态
tail -f logs/cron_test.log

# 启用通知
export TEST_SEND_NOTIFY=true
python3 test_web_api.py --send-notify
```

---

## ✅ 完成清单

- [x] 创建测试脚本 `test_web_api.py`
- [x] 创建定时执行脚本 `scheduled_test.sh`
- [x] 配置 crontab（每天 19:00）
- [x] 创建文档 `WEB_API_TEST.md`
- [ ] 首次执行测试
- [ ] 验证通知功能

---

*文档创建时间：2026-03-29 15:10*
