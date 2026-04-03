# CCP 快速启动指南

## 🚀 设置别名（已完成）

别名已添加到 `~/.bashrc`：

```bash
# CCP 启动脚本（交互模式）
alias ccp-start

# CCP 命令行工具
alias ccp
```

### 使别名生效

```bash
source ~/.bashrc
```

---

## 📋 使用方式

### 方式 1：交互模式（推荐）

```bash
# 在你当前的工作目录启动
cd /your/project
ccp-start

# 等价于
/home/admin/.openclaw/workspace/claude-code-python/start.sh
```

### 方式 2：批处理模式

```bash
# 一次性任务
ccp run "分析这个项目"

# 指定工作目录
ccp run -w /path/to/project "创建 README 文件"

# 交互模式
ccp run -i
ccp run -i -w /path/to/project
```

### 方式 3：直接使用别名

```bash
# 完整功能
ccp run -i -m qwen-plus "Hello"

# 查看帮助
ccp --help
```

---

## 💡 常用命令

| 命令 | 说明 |
|------|------|
| `ccp-start` | 启动交互模式（当前目录） |
| `ccp run "任务"` | 执行一次性任务 |
| `ccp run -i` | 交互模式 |
| `ccp run -w /path "任务"` | 指定工作目录 |
| `ccp --help` | 查看帮助 |
| `ccp config` | 配置向导 |
| `ccp tools` | 列出可用工具 |

---

## 📁 项目位置

```
/home/admin/.openclaw/workspace/claude-code-python/
```

### 关键文件

| 文件 | 说明 |
|------|------|
| `start.sh` | 启动脚本 |
| `.env` | 环境配置（API Key） |
| `README.md` | 项目文档 |
| `AGENT_LOOP.md` | Agent 循环说明 |

---

## ⚙️ 环境配置

API Key 已配置在 `.env` 文件：

```bash
ANTHROPIC_API_KEY=sk-sp-xxx
ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
ANTHROPIC_MODEL=qwen3.5-plus
```

---

## 🎯 示例

### 分析项目

```bash
cd /home/admin/.openclaw/workspace
ccp-start

You: 分析一下这个项目结构
```

### 创建文件

```bash
ccp run "帮我创建一个 Python 脚本，用于监控 CPU 使用率"
```

### 代码重构

```bash
cd /your/python/project
ccp-start

You: 重构 src/目录的代码，提高可读性
```

---

*最后更新：2026-04-03*
