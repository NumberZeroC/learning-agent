# 🔍 Stock-Agent Web 服务监控失效诊断报告

**日期：** 2026-04-01  
**问题：** 服务停止后 watchdog 未自动重启，测试任务未告警

---

## 📊 问题总结

| 问题 | 状态 | 原因 |
|------|------|------|
| **Web 服务** | ❌ 已停止 | 端口 5000 被占用（2026-03-24） |
| **Watchdog** | ❌ 未运行 | **未配置到 crontab** |
| **定时测试** | ⚠️ 部分失效 | 测试失败但未发送通知 |
| **数据刷新** | ❌ 未更新 | 服务停止导致 |

---

## 🔍 根本原因分析

### 1. Watchdog 未配置到 Crontab ❌

**检查结果：**
```bash
$ crontab -l | grep watchdog
# 无输出 - watchdog 未配置
```

**影响：**
- watchdog.sh 脚本虽然存在，但**没有定时执行**
- 服务停止后**无人监管**
- 最后一次 watchdog 日志：`2026-03-30 23:08:01`

**证据：**
```
watchdog.log 最后记录：
[2026-03-30 23:08:01] === 看门狗检查开始 ===
[2026-03-30 23:08:01] ✅ 服务运行中 (PID: 302649)
[2026-03-30 23:08:01] === 看门狗检查结束 ===
# 之后无任何记录
```

---

### 2. 测试任务告警未启用 ⚠️

**检查结果：**
```bash
$ crontab -l | grep scheduled_test
0 19 * * * /home/admin/.openclaw/workspace/stock-notification-web/scheduled_test.sh
```

**测试日志（2026-04-01 19:00）：**
```
总测试数：10
通过：8 ✅
警告：1 ⚠️
失败：1 ❌
通过率：80.0%

通知功能未启用，跳过发送
```

**问题：**
- `TEST_SEND_NOTIFY=false`（默认值）
- 测试失败后**未发送告警**
- 即使服务挂了也**无人知晓**

---

### 3. 服务停止原因

**历史日志（2026-03-24）：**
```
OSError: [Errno 98] Address already in use
```

**原因：** 端口 5000 被其他程序占用，导致 Flask 启动失败

**为什么 watchdog 没发现？**
- watchdog 最后一次运行：2026-03-30 23:08
- 服务可能在 2026-03-30 23:08 之后停止
- 或者 watchdog 的 cron 任务被删除了

---

## 📋 当前状态（2026-04-01 22:27）

| 检查项 | 状态 | 详情 |
|--------|------|------|
| **Web 服务** | ✅ 已启动 | PID: 426388 |
| **端口 5000** | ✅ 监听中 | http://localhost:5000 |
| **Watchdog** | ❌ 未配置 | 需要添加到 crontab |
| **定时测试** | ⚠️ 已配置 | 但告警未启用 |
| **数据刷新** | ❌ 待验证 | 需要检查大盘数据 |

---

## 🔧 修复方案

### 方案 1：配置 Watchdog 到 Crontab（推荐）

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每分钟检查一次）
* * * * * /home/admin/.openclaw/workspace/stock-notification-web/watchdog.sh >> /home/admin/.openclaw/workspace/stock-notification-web/logs/watchdog.log 2>&1
```

**优点：**
- ✅ 自动监控，每分钟检查
- ✅ 服务异常自动重启
- ✅ 日志完整记录

---

### 方案 2：启用测试告警

```bash
# 编辑 scheduled_test.sh
export TEST_SEND_NOTIFY=true

# 或者在 crontab 中设置环境变量
0 19 * * * TEST_SEND_NOTIFY=true /home/admin/.openclaw/workspace/stock-notification-web/scheduled_test.sh
```

**添加告警逻辑（scheduled_test.sh）：**
```bash
# 如果测试失败且启用了通知，发送告警
if [ $EXIT_CODE -ne 0 ] && [ "$TEST_SEND_NOTIFY" = "true" ]; then
    echo "发送失败通知..."
    
    # 方式 1：发送邮件
    echo "Stock-Agent Web 测试失败" | mail -s "告警：Web 服务异常" admin@example.com
    
    # 方式 2：调用通知 API（如钉钉、企业微信）
    curl -X POST "https://api.example.com/notify" \
      -H "Content-Type: application/json" \
      -d "{\"text\":\"Stock-Agent Web 测试失败，请检查\"}"
fi
```

---

### 方案 3：使用 systemd 管理（最可靠）

**创建 systemd 服务文件：**
```ini
# /etc/systemd/system/stock-agent-web.service
[Unit]
Description=Stock-Agent Web Service
After=network.target

[Service]
Type=simple
User=admin
WorkingDirectory=/home/admin/.openclaw/workspace/stock-notification-web
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**启用服务：**
```bash
sudo systemctl daemon-reload
sudo systemctl enable stock-agent-web
sudo systemctl start stock-agent-web
sudo systemctl status stock-agent-web
```

**优点：**
- ✅ 系统级守护进程
- ✅ 自动重启（Restart=always）
- ✅ 日志集中管理（journalctl）
- ✅ 开机自启动

---

## 📝 执行清单

### 立即执行

- [ ] **配置 watchdog 到 crontab**
  ```bash
  (crontab -l 2>/dev/null; echo "* * * * * /home/admin/.openclaw/workspace/stock-notification-web/watchdog.sh >> /home/admin/.openclaw/workspace/stock-notification-web/logs/watchdog.log 2>&1") | crontab -
  ```

- [ ] **验证 watchdog 运行**
  ```bash
  sleep 60 && tail -20 /home/admin/.openclaw/workspace/stock-notification-web/logs/watchdog.log
  ```

### 建议执行

- [ ] **启用测试告警**
  ```bash
  export TEST_SEND_NOTIFY=true
  ```

- [ ] **配置通知渠道**
  - 邮件告警
  - 钉钉/企业微信 webhook
  - QQ 推送（已有 stock-notification 项目）

- [ ] **迁移到 systemd**（可选）
  - 更可靠的服务管理
  - 系统重启自动恢复

---

## 🧪 验证步骤

### 1. 验证 Watchdog

```bash
# 1. 检查 crontab
crontab -l | grep watchdog

# 2. 手动执行一次
/home/admin/.openclaw/workspace/stock-notification-web/watchdog.sh

# 3. 等待 1 分钟检查日志
tail -20 /home/admin/.openclaw/workspace/stock-notification-web/logs/watchdog.log
```

### 2. 验证服务状态

```bash
# 检查进程
ps aux | grep "python3 app.py"

# 检查端口
curl -s http://localhost:5000/ | head -5

# 检查 API
curl -s http://localhost:5000/api/ | python3 -m json.tool
```

### 3. 模拟故障测试

```bash
# 1. 停止服务
kill $(cat /home/admin/.openclaw/workspace/stock-notification-web/logs/web.pid)

# 2. 等待 1 分钟

# 3. 检查 watchdog 日志
tail -20 /home/admin/.openclaw/workspace/stock-notification-web/logs/watchdog.log

# 4. 验证服务是否自动重启
ps aux | grep "python3 app.py"
```

---

## 📊 监控指标

### 关键指标

| 指标 | 目标值 | 当前状态 |
|------|--------|----------|
| **服务可用性** | >99.9% | ❌ 待提升 |
| **数据刷新频率** | 交易时间每 30 分钟 | ❌ 已停止 |
| **Watchdog 检查** | 每分钟 1 次 | ❌ 未配置 |
| **定时测试** | 每天 19:00 | ✅ 已配置 |
| **告警响应时间** | <5 分钟 | ❌ 未启用 |

---

## 🎯 后续优化

1. **添加健康检查端点**
   ```python
   @app.route('/health')
   def health():
       return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})
   ```

2. **集成 Prometheus 监控**
   - 导出服务指标
   - Grafana 可视化
   - Alertmanager 告警

3. **添加数据新鲜度检查**
   ```bash
   # 检查数据文件最后修改时间
   find /home/admin/.openclaw/workspace/data/stock-agent -mmin +60
   ```

4. **配置日志轮转**
   ```bash
   # 使用 logrotate 管理日志
   /home/admin/.openclaw/workspace/stock-notification-web/logs/*.log {
       daily
       rotate 7
       compress
       delaycompress
       missingok
       notifempty
   }
   ```

---

## ✅ 修复完成检查清单

- [ ] Watchdog 已配置到 crontab
- [ ] Watchdog 日志正常更新
- [ ] 服务自动重启功能验证通过
- [ ] 测试告警已启用
- [ ] 通知渠道已配置
- [ ] 大盘数据正常刷新
- [ ] 监控指标可视化（可选）

---

**报告生成时间：** 2026-04-01 22:30  
**负责人：** 系统管理员  
**优先级：** 🔴 高（立即执行）
