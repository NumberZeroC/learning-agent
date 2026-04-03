# 📂 CCP Web 服务执行目录说明

**日期：** 2026-04-03  
**状态：** ✅ 已配置

---

## 📍 执行目录位置

通过 Web 服务发送的命令，CCP 的执行目录（工作目录）是：

```
/home/admin/.openclaw/workspace/claude-code-python/workspace
```

---

## 🗂️ 目录结构

```
claude-code-python/
├── workspace/          ← Web 服务的执行目录
│   ├── 项目 1/
│   ├── 项目 2/
│   └── ...
├── src/               ← 源代码
├── tests/             ← 测试文件
└── ...
```

---

## 🎯 为什么是这个目录？

### 设计考虑

1. **隔离性** - 与源代码分离，避免误操作修改代码
2. **安全性** - 限制在 workspace 内，不能访问系统目录
3. **组织性** - 所有 Web 创建的项目都在一个地方
4. **可访问性** - 用户空间目录，有读写权限

---

## 💻 使用示例

### 示例 1: 创建项目

**用户输入：**
```
创建一个 Python 项目，叫 my_project
```

**执行结果：**
```
✅ 创建目录：/home/admin/.openclaw/workspace/claude-code-python/workspace/my_project
✅ 创建文件：workspace/my_project/main.py
✅ 创建文件：workspace/my_project/pyproject.toml
```

**访问项目：**
```bash
cd /home/admin/.openclaw/workspace/claude-code-python/workspace/my_project
```

---

### 示例 2: 文件操作

**用户输入：**
```
在当前目录创建一个 test.txt 文件
```

**执行位置：**
```
/home/admin/.openclaw/workspace/claude-code-python/workspace/test.txt
```

---

### 示例 3: 列出文件

**用户输入：**
```
列出当前目录的所有文件
```

**执行命令：**
```bash
ls -la /home/admin/.openclaw/workspace/claude-code-python/workspace/
```

---

## 🔧 修改执行目录

如果需要修改执行目录，可以编辑 `src/web_server.py`：

```python
# 在 CCPWebServer.__init__ 方法中

# 方式 1: 使用项目根目录
workspace = Path(__file__).parent.parent

# 方式 2: 使用用户主目录
workspace = Path.home() / 'ccp-workspace'

# 方式 3: 使用绝对路径
workspace = Path('/path/to/your/workspace')
```

然后重启 Web 服务器：

```bash
pkill -f web_server
.venv/bin/python -m src.web_server --port 9000
```

---

## 📊 目录权限

| 目录 | 读 | 写 | 执行 |
|------|---|---|-----|
| workspace/ | ✅ | ✅ | ✅ |
| src/ | ✅ | ❌ | ❌ |
| 系统目录 | ❌ | ❌ | ❌ |

---

## ⚠️ 安全限制

### 禁止访问的路径

以下路径被工具安全策略禁止访问：

- `/` - 根目录
- `/etc` - 系统配置
- `/usr` - 系统程序
- `/bin` - 系统二进制
- `/root` - root 用户目录
- `/home` (其他用户) - 其他用户目录

### 允许访问的路径

- `workspace/` - 工作目录（完全访问）
- `/tmp` - 临时目录（有限访问）

---

## 📝 查看当前目录

在 Web 聊天中输入：

```
当前目录在哪里？
```

或

```
pwd
```

AI 会告诉你当前的工作目录。

---

## 🔄 会话目录

每个 Web 会话都有独立的工作目录配置：

```python
Session(
    session_id="session_123",
    working_directory="/home/admin/.openclaw/workspace/claude-code-python/workspace"
)
```

所有会话共享同一个工作目录，但会话之间不会共享文件操作历史。

---

## 📈 目录使用统计

```bash
# 查看 workspace 大小
du -sh /home/admin/.openclaw/workspace/claude-code-python/workspace

# 查看创建的项目
ls -la /home/admin/.openclaw/workspace/claude-code-python/workspace

# 查看文件数量
find /home/admin/.openclaw/workspace/claude-code-python/workspace -type f | wc -l
```

---

*文档时间：2026-04-03*  
*作者：小佳 ✨*
