# Stock-Agent Web 运维说明

## ✅ 已完成配置

### 1. 服务启动方式

使用 `webctl.sh` 脚本管理服务和看门狗：

```bash
cd /home/admin/.openclaw/workspace/stock-agent-web

# 启动服务
./webctl.sh start

# 停止服务
./webctl.sh stop

# 重启服务
./webctl.sh restart

# 查看状态
./webctl.sh status
```

### 2. 看门狗守护

**脚本位置：** `./watchdog.sh`

**功能：**
- ✅ 每分钟自动检查服务状态
- ✅ 进程异常时自动重启
- ✅ 检测端口僵死情况
- ✅ 记录详细日志

**Crontab 配置：**
```bash
* * * * * /home/admin/.openclaw/workspace/stock-agent-web/watchdog.sh
```

**日志位置：** `logs/watchdog.log`

---

## 📊 当前状态

| 项目 | 状态 |
|------|------|
| 服务 PID | 48131 |
| 端口 | 5000 |
| 访问地址 | http://39.97.249.78:5000 |
| 看门狗 | ✅ 已启用（每分钟检查） |

---

## 🔧 常用命令

### 查看服务状态
```bash
./webctl.sh status
```

### 查看看门狗日志
```bash
tail -f logs/watchdog.log
```

### 查看 Web 服务日志
```bash
tail -f logs/web.log
```

### 手动触发看门狗检查
```bash
./watchdog.sh
```

---

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `webctl.sh` | 服务管理脚本（start/stop/restart/status） |
| `watchdog.sh` | 看门狗脚本（自动监控 + 重启） |
| `logs/web.pid` | 当前服务 PID |
| `logs/web.log` | Web 服务日志 |
| `logs/watchdog.log` | 看门狗检查日志 |

---

## ⚠️ 注意事项

1. **不要手动删除 `logs/web.pid`** - 看门狗依赖此文件检测服务状态
2. **如需完全停止服务** - 使用 `./webctl.sh stop`，不要直接 kill 进程
3. **看门狗日志会持续增长** - 建议定期清理或使用 logrotate

---

*最后更新：2026-03-23 21:41*
