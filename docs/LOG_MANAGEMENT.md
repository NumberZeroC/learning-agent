# 📝 日志管理策略

**更新日期：** 2026-04-04  
**状态：** ✅ 已启用（使用 Python logging 轮转）

---

## 📋 策略说明

### 日志轮转配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| **保留文件数** | 10 个 | 最多保留 10 个日志文件 |
| **单文件大小** | 10MB | 每个日志文件最大 10MB |
| **总空间占用** | ~100MB | 所有日志文件最大总大小 |
| **清理方式** | 自动轮转 | 使用 Python logging 框架自动管理 |

### 工作原理

```
当日志文件达到 10MB 时：
1. 当前日志文件重命名为 xxx.log.1
2. 之前的 xxx.log.1 重命名为 xxx.log.2
3. 依此类推...
4. 当超过 10 个文件时，最旧的文件（xxx.log.10）被删除
5. 创建新的 xxx.log 继续写入
```

---

## 🛠️ 技术实现

### 使用的组件

- **Python logging 模块** - 标准日志框架
- **RotatingFileHandler** - 日志轮转处理器
- **统一配置模块** - `utils/logger.py`

### 核心代码

```python
from logging.handlers import RotatingFileHandler

# 配置日志轮转
log_file = "logs/web.log"
handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=10,  # 保留 10 个备份文件
    encoding='utf-8'
)
```

---

## 📊 日志文件

### Web 服务日志

| 文件 | 说明 |
|------|------|
| `logs/web.log` | 当前日志 |
| `logs/web.log.1` | 最近的备份 |
| `logs/web.log.2` ~ `logs/web.log.10` | 历史备份 |

### 工作流日志

| 文件 | 说明 |
|------|------|
| `logs/workflow.log` | 当前日志 |
| `logs/workflow.log.1` ~ `logs/workflow.log.10` | 历史备份 |

### 服务日志

| 文件 | 说明 |
|------|------|
| `logs/ask_service.log` | Ask 服务日志 |
| `logs/ask_service.log.1` ~ `logs/ask_service.log.10` | 历史备份 |

---

## 🔧 配置位置

### 统一配置模块

**文件：** `utils/logger.py`

**修改配置：**

```python
class LogConfig:
    MAX_BYTES = 10 * 1024 * 1024  # 修改单文件大小
    BACKUP_COUNT = 10  # 修改保留文件数
```

### 各组件配置

| 组件 | 文件 | 说明 |
|------|------|------|
| Web 服务 | `web/app.py` | 已配置 RotatingFileHandler |
| 工作流 | `workflow_orchestrator.py` | 已配置 RotatingFileHandler |
| Ask 服务 | `services/ask_service.py` | 已配置 RotatingFileHandler |

---

## 📋 使用方法

### 查看日志

```bash
# 查看当前日志
tail -f logs/web.log

# 查看工作流日志
tail -f logs/workflow.log

# 查看所有日志文件
ls -lh logs/
```

### 查看日志文件列表

```bash
# 查看日志文件数量和大小
du -sh logs/*

# 查看最旧的日志文件
ls -lt logs/*.log.* | tail -5
```

### 手动清理（可选）

```bash
# 删除所有备份日志
rm logs/*.log.*

# 只保留当前日志
find logs/ -name "*.log.*" -delete
```

---

## 🎯 配置选项

### 修改保留文件数

编辑 `utils/logger.py`：

```python
class LogConfig:
    BACKUP_COUNT = 20  # 改为保留 20 个文件
```

### 修改单文件大小

```python
class LogConfig:
    MAX_BYTES = 50 * 1024 * 1024  # 改为 50MB
```

### 修改日志级别

```python
class LogConfig:
    LOG_LEVEL = logging.DEBUG  # 改为 DEBUG 级别
```

---

## 📈 日志管理最佳实践

### 1. 自动轮转

- ✅ 使用 RotatingFileHandler 自动管理
- ✅ 无需手动清理脚本
- ✅ 无需 cron 定时任务

### 2. 日志分类

```
logs/
├── web.log*              # Web 服务日志
├── workflow.log*         # 工作流日志
├── ask_service.log*      # Ask 服务日志
└── .gitkeep              # 目录占位文件
```

### 3. 监控建议

```bash
# 定期检查日志大小
du -sh logs/

# 查看日志文件数量
ls logs/*.log* | wc -l

# 检查磁盘空间
df -h
```

---

## 🔍 故障排查

### Q: 日志文件超过 10 个

**检查：**
```bash
ls -lh logs/*.log.* | wc -l
```

**原因：**
- 可能是多个进程同时写入
- 或者配置未生效

**解决：**
```bash
# 检查配置
grep BACKUP_COUNT utils/logger.py

# 重启服务
pkill -f "python3 web/app.py"
python3 web/app.py
```

### Q: 日志文件过大

**检查：**
```bash
du -sh logs/*
```

**解决：**
```bash
# 临时清理旧日志
find logs/ -name "*.log.*" -mtime +7 -delete

# 或调整 MAX_BYTES 配置
```

### Q: 日志不输出

**检查：**
```bash
# 查看 logger 配置
grep -A5 "get_logger" utils/logger.py

# 查看 handler
ps aux | grep python3
```

**解决：**
```bash
# 重启服务
pkill -f "python3 web/app.py"
python3 web/app.py
```

---

## 📝 相关文件

| 文件 | 说明 |
|------|------|
| `utils/logger.py` | 统一日志配置模块 |
| `web/app.py` | Web 服务（已配置日志） |
| `workflow_orchestrator.py` | 工作流（已配置日志） |
| `services/ask_service.py` | Ask 服务（已配置日志） |
| `docs/LOG_MANAGEMENT.md` | 本文档 |

---

## ✅ 验证清单

- [x] 统一日志模块已创建
- [x] Web 服务已配置 RotatingFileHandler
- [x] 工作流已配置 RotatingFileHandler
- [x] Ask 服务已配置 RotatingFileHandler
- [x] 清理脚本已删除
- [x] cron 任务已移除
- [x] 文档已更新

---

## 🚀 优势对比

### 旧方案（已废弃）

```
❌ 单独的清理脚本（cleanup_logs.sh）
❌ cron 定时任务（每月执行）
❌ 基于时间清理（30 天）
❌ 需要手动维护
```

### 新方案（当前）

```
✅ Python logging 框架内置支持
✅ 自动轮转（无需定时任务）
✅ 基于文件大小清理（10MB）
✅ 统一配置管理
✅ 最多保留 10 个文件
```

---

**状态：** ✅ 生产环境可用
