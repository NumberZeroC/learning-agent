# CCP 能力说明

Claude Code Python (CCP) - 完整的 AI 编程助手

---

## 🎯 核心能力

### 1. 项目创建 ✅

**可以创建完整的项目！**

```bash
ccp run -i

You: 创建一个 Python CLI 项目，叫 my_cli
AI: [创建完整项目结构]
    [生成所有必要文件]
    [显示下一步操作]
```

**支持：**
- ✅ Python CLI 项目
- ✅ Python 包/库
- ✅ FastAPI Web API
- ✅ 自定义项目结构

---

### 2. 代码生成 ✅

**可以生成可运行的代码！**

```bash
You: 帮我写一个斐波那契函数
AI: [生成 Python 代码]
    [解释代码逻辑]
    [提供使用示例]
```

**支持：**
- ✅ 函数/类生成
- ✅ 模块/包生成
- ✅ 完整项目代码
- ✅ 代码解释

---

### 3. 文件操作 ✅

**可以操作文件系统！**

```bash
You: 读取 src/main.py 的内容
AI: [调用 file_read 工具]
    [返回文件内容]

You: 帮我创建一个新文件 test.py
AI: [调用 file_write 工具]
    [创建文件]

You: 修改 main.py 的第 10 行
AI: [调用 file_edit 工具]
    [精确修改]
```

**支持：**
- ✅ 读取文件
- ✅ 创建文件
- ✅ 编辑文件
- ✅ 批量创建
- ✅ 创建目录

---

### 4. 命令执行 ✅

**可以执行 shell 命令！**

```bash
You: 列出当前目录的文件
AI: [调用 bash 执行 ls -la]
    [返回结果]

You: 运行测试
AI: [调用 bash 执行 pytest]
    [显示测试结果]
```

**支持：**
- ✅ 文件操作命令
- ✅ Git 命令
- ✅ 测试运行
- ✅ 构建命令
- ✅ 系统命令

---

### 5. 代码搜索 ✅

**可以搜索代码！**

```bash
You: 查找所有包含"def main"的文件
AI: [调用 grep 工具]
    [返回匹配结果]

You: 找出所有 Python 文件
AI: [调用 glob 工具 **/*.py]
    [返回文件列表]
```

**支持：**
- ✅ 文本搜索 (grep)
- ✅ 文件匹配 (glob)
- ✅ 正则搜索
- ✅ 递归搜索

---

### 6. Git 操作 ✅

**可以操作 Git！**

```bash
You: 检查 git 状态
AI: [调用 git status]
    [返回状态]

You: 提交当前更改
AI: [调用 git add, git commit]
    [完成提交]
```

**支持：**
- ✅ git status
- ✅ git add
- ✅ git commit
- ✅ git push/pull
- ✅ git branch

---

### 7. 项目分析 ✅

**可以分析项目架构！**

```bash
You: 分析一下这个项目的架构
AI: [调用工具收集信息]
    [查看目录结构]
    [查找配置文件]
    [输出完整分析报告]
```

**输出包括：**
- ✅ 项目类型识别
- ✅ 目录结构分析
- ✅ 技术栈识别
- ✅ 架构分层
- ✅ 改进建议

---

### 8. 问题排查 ✅

**可以帮助调试！**

```bash
You: 为什么测试失败了？
AI: [运行测试查看错误]
    [查看错误日志]
    [分析原因]
    [给出解决方案]
```

**支持：**
- ✅ 错误分析
- ✅ 日志查看
- ✅ 问题定位
- ✅ 解决方案

---

## 📊 能力对比

| 能力 | CCP | Claude Code | 说明 |
|------|-----|-------------|------|
| 对话问答 | ✅ | ✅ | 基本对话能力 |
| 代码生成 | ✅ | ✅ | 生成可运行代码 |
| 文件操作 | ✅ | ✅ | 读/写/编辑文件 |
| 命令执行 | ✅ | ✅ | 执行 shell 命令 |
| 代码搜索 | ✅ | ✅ | grep/glob 搜索 |
| Git 操作 | ✅ | ✅ | 版本控制 |
| 项目创建 | ✅ | ✅ | 创建完整项目 |
| 项目分析 | ✅ | ✅ | 架构分析 |
| 问题排查 | ✅ | ✅ | 调试帮助 |
| 多步任务 | ✅ | ✅ | 连续调用工具 |
| 权限审批 | ✅ | ✅ | 敏感操作审批 |

---

## 🛠️ 工具列表

| 工具 | 功能 | 示例 |
|------|------|------|
| `bash` | 执行命令 | `ls -la`, `git status` |
| `file_read` | 读取文件 | 读取源代码 |
| `file_edit` | 编辑文件 | 修改代码 |
| `file_write` | 创建文件 | 新建文件 |
| `file_write_batch` | 批量创建 | 创建多个文件 |
| `mkdir` | 创建目录 | 创建目录树 |
| `grep` | 文本搜索 | 搜索代码 |
| `glob` | 文件匹配 | 查找文件 |
| `git` | Git 操作 | 提交代码 |
| `project_template` | 项目模板 | 创建项目 |

---

## 🚀 使用示例

### 创建项目

```bash
$ ccp run -i

You: 创建一个 Python CLI 项目，叫 weather_cli

AI: 🎉 Project created from template: Python CLI Project
📁 Project name: weather_cli

Next steps:
  cd weather_cli
  pip install -e .
  weather_cli --help
```

### 分析项目

```bash
$ ccp run -i

You: 分析一下当前目录的项目架构

AI: [调用工具收集信息]

## 项目架构分析

### 项目类型
Python CLI 项目

### 目录结构
src/ - 源代码
tests/ - 测试
docs/ - 文档

### 技术栈
- Python 3.11+
- Click (CLI)
- Pytest (测试)

### 架构分层
CLI → Commands → Services → Core

### 建议
1. 添加类型注解
2. 增加文档覆盖率
```

### 代码修改

```bash
$ ccp run -i

You: 给 main.py 添加一个 greet 函数

AI: [读取 main.py]
    [添加 greet 函数]
    [显示修改内容]

def greet(name: str) -> str:
    """Greet a person by name."""
    return f"Hello, {name}!"
```

---

## 💡 最佳实践

### 1. 描述要具体

❌ 不好：
```
You: 创建一个项目
```

✅ 好：
```
You: 创建一个 Python CLI 项目，叫 weather_cli，用于查询天气
```

### 2. 分步执行

复杂任务可以分步：
```
You: 先创建项目目录
You: 现在创建 main.py
You: 添加配置文件
```

### 3. 及时验证

创建后验证：
```
You: 运行测试看看有没有问题
```

### 4. 使用模板

快速创建标准项目：
```
You: 用 python_cli 模板创建项目
```

---

## 📚 相关文档

- `PROJECT_CREATION_GUIDE.md` - 项目创建指南
- `TECHNICAL_DESIGN.md` - 技术设计
- `README.md` - 使用说明

---

*最后更新：2026-04-03*
*CCP 版本：0.1.0*
