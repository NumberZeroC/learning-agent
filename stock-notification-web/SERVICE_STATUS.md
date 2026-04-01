# Stock-Agent Web 服务状态

**检查时间：** 2026-03-16 23:10

---

## ✅ 当前状态

```
服务状态：✅ 运行中
进程 ID: 130395
监听端口：5000
访问地址：http://39.97.249.78:5000
API 测试：✅ 成功
自动监控：✅ 已启用（每 5 分钟检查）
```

---

## 🔍 排查结果

### 服务挂掉原因

1. **后台进程管理问题**
   - 直接使用 `&` 后台运行，进程容易被系统回收
   - 没有使用 `nohup` 或 `disown` 保护进程

2. **内存紧张**
   - 系统总内存：1.8GB
   - 已使用：1.1GB
   - 可用：753MB
   - Flask 应用占用约 320MB

3. **没有自动重启机制**
   - 进程退出后无人管理
   - 需要手动重启

---

## ✅ 解决方案

### 1. 创建守护脚本 (webctl.sh)

```bash
#!/bin/bash
# 服务管理脚本

# 启动
./webctl.sh start

# 停止
./webctl.sh stop

# 重启
./webctl.sh restart

# 查看状态
./webctl.sh status
```

### 2. 添加 Crontab 监控

```cron
*/5 * * * * /home/admin/.openclaw/workspace/stock-agent-web/webctl.sh start
```

**作用：** 每 5 分钟检查一次，如果服务挂了自动重启

### 3. 使用 nohup + PID 文件

- 使用 `nohup` 防止进程被 kill
- 记录 PID 到文件便于管理
- 启动前检查是否已在运行

---

## 📊 服务管理命令

### 启动服务
```bash
cd /home/admin/.openclaw/workspace/stock-agent-web
./webctl.sh start
```

### 查看状态
```bash
./webctl.sh status
```

### 重启服务
```bash
./webctl.sh restart
```

### 查看日志
```bash
tail -f logs/web.log
```

### 查看进程
```bash
ps aux | grep "python3 app.py" | grep -v grep
```

### 查看端口
```bash
netstat -tuln | grep 5000
```

---

## 🔧 故障排查

### 服务无法启动

```bash
# 1. 检查端口是否被占用
netstat -tuln | grep 5000

# 2. 查看错误日志
tail -50 logs/web.log

# 3. 检查 Python 依赖
python3 -c "import flask; print(flask.__version__)"

# 4. 手动启动测试
python3 app.py
```

### 服务频繁挂掉

```bash
# 1. 检查内存
free -h

# 2. 检查系统日志
dmesg | grep -i "killed process"

# 3. 查看应用日志
tail -100 logs/web.log

# 4. 检查是否有异常请求
grep "ERROR" logs/web.log
```

---

## 📈 监控指标

| 指标 | 当前值 | 阈值 | 状态 |
|------|--------|------|------|
| 内存使用 | ~320MB | <500MB | ✅ |
| CPU 使用 | ~3% | <50% | ✅ |
| 响应时间 | <100ms | <1s | ✅ |
| 正常运行时间 | 持续 | 24/7 | ✅ |

---

## 🛡️ 高可用保障

1. **自动重启** - Crontab 每 5 分钟检查
2. **PID 管理** - 防止重复启动
3. **日志记录** - 便于故障排查
4. **优雅关闭** - 使用 stop 命令

---

## 📞 快速修复

如果服务挂了，执行：

```bash
cd /home/admin/.openclaw/workspace/stock-agent-web
./webctl.sh restart
```

等待 5 分钟后 Crontab 也会自动重启服务。

---

*最后更新：2026-03-16 23:10*
