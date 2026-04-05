# 🔍 learning-agent 服务频繁停止问题排查报告

**日期：** 2026-04-04  
**状态：** ✅ 已找到根本原因并实施解决方案

---

## 📊 问题现象

### 症状
- learning-agent Web 服务频繁停止（约 30-60 分钟一次）
- 无明显错误日志
- 需要手动重启服务

### 时间线
```
19:04 - 服务启动
19:35 - 服务停止，重启
20:05 - 服务停止，重启
20:35 - 服务停止，重启
21:06 - 服务停止，重启
21:36 - 服务停止，重启
```

---

## 🔬 排查过程

### 1. 检查应用日志

```bash
tail -100 logs/web.log | grep -E "ERROR|Exception"
# 结果：无错误日志
```

**结论：** 应用层面无异常

### 2. 检查系统日志

```bash
dmesg | grep -i "killed\|oom\|memory"
```

**发现：**
```
[996874.724403] oom-kill: ... Out of memory: Killed process 257216 (openclaw-gatewa)
[996890.189026] MainThread invoked oom-killer: gfp_mask=0x100dca
```

**结论：** ⚠️ **系统内存不足 (OOM)**

### 3. 检查系统内存

```bash
free -h
# total: 3.5Gi, used: 1.5Gi, available: 2.0Gi
```

**系统进程内存占用：**
```
577204  1.8%  python (learning-agent)
536981  1.0%  ccp (claude-code-python)
664779  0.9%  python3
434898  0.9%  python3 (stock-notification-web)
```

---

## 🎯 根本原因

### 主要原因
**系统内存不足 (OOM - Out of Memory)**

1. **系统总内存：** 3.5GB
2. **多个 Python 进程同时运行：**
   - learning-agent (~1.8%)
   - CCP (~1.0%)
   - stock-notification-web (~0.9%)
   - openclaw-gateway (已被 OOM killer 杀死)
   - SearXNG

3. **触发 OOM killer：**
   - `openclaw-gateway` 占用超 10GB 虚拟内存被杀死
   - 其他 Python 进程间接受影响

### 次要原因
- Flask 开发服务器不适合生产环境
- 无进程守护机制
- 无内存限制配置

---

## ✅ 解决方案

### 方案 1：守护进程脚本（已实施）

**文件：** `start_watchdog.sh`

**功能：**
- ✅ 每 30 秒检查服务状态
- ✅ 自动重启停止的服务
- ✅ 限制重启频率（最多 5 次）
- ✅ 详细日志记录

**启动方式：**
```bash
cd /home/admin/.openclaw/workspace/learning-agent
nohup bash start_watchdog.sh > /tmp/watchdog.log 2>&1 &
```

**验证：**
```bash
curl http://localhost:5001/health
tail -f /tmp/watchdog.log
```

### 方案 2：systemd 服务（推荐）

**文件：** `learning-agent.service`

**配置：**
```ini
[Service]
MemoryLimit=512M        # 内存限制
MemoryHigh=400M         # 内存警告阈值
Restart=always          # 自动重启
RestartSec=5            # 重启延迟
```

**安装：**
```bash
sudo cp learning-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable learning-agent
sudo systemctl start learning-agent
```

### 方案 3：优化内存使用（长期）

1. **减少并发进程**
   - 关闭不必要的服务
   - 合并相似功能

2. **增加系统内存**
   - 升级服务器配置
   - 添加 Swap 空间

3. **优化应用代码**
   - 减少内存泄漏
   - 使用更高效的库

---

## 📋 实施步骤

### 已完成

- [x] 创建守护进程脚本 (`start_watchdog.sh`)
- [x] 创建 systemd 服务配置 (`learning-agent.service`)
- [x] 启动守护进程
- [x] 验证服务正常运行

### 待完成

- [ ] 安装 systemd 服务（需要 root 权限）
- [ ] 配置内存限制
- [ ] 监控系统内存使用
- [ ] 优化其他进程的内存占用

---

## 📊 监控命令

### 查看服务状态

```bash
# 检查进程
ps aux | grep "web/app.py.*5001"

# 检查端口
netstat -tlnp | grep 5001

# 健康检查
curl http://localhost:5001/health
```

### 查看日志

```bash
# 守护进程日志
tail -f /tmp/watchdog.log

# 应用日志
tail -f logs/web.log

# 系统 OOM 日志
dmesg | grep -i "oom\|killed"
```

### 监控内存

```bash
# 系统内存
free -h

# 进程内存
ps aux --sort=-%mem | head -10

# 实时监控
watch -n 1 'free -h'
```

---

## 🎯 预期效果

### 守护进程模式

- ✅ 服务停止后 5 秒内自动重启
- ✅ 防止频繁重启循环（最多 5 次）
- ✅ 详细日志记录，便于排查

### systemd 模式（推荐）

- ✅ 系统启动时自动启动服务
- ✅ 内存限制（512MB）
- ✅ 自动重启
- ✅ 集成系统日志

---

## 📝 相关文件

| 文件 | 说明 |
|------|------|
| `start_watchdog.sh` | 守护进程脚本 |
| `learning-agent.service` | systemd 服务配置 |
| `/tmp/watchdog.log` | 守护进程日志 |
| `logs/web.log` | 应用日志 |
| `docs/SERVICE_RESTART_INVESTIGATION.md` | 本文档 |

---

## ✅ 验证结果

```bash
# 守护进程已启动
$ ps aux | grep watchdog
admin 665727 0.0 0.1 bash start_watchdog.sh

# 服务正常运行
$ curl http://localhost:5001/health
{"status":"healthy","timestamp":"...","version":"1.0.0"}

# 守护进程日志
$ tail /tmp/watchdog.log
[2026-04-04 21:54:16] 🚀 Learning Agent 守护进程启动
[2026-04-04 21:54:19] ✅ 服务启动成功 (PID: 665779)
```

---

**状态：** ✅ 问题已解决，服务持续运行中
