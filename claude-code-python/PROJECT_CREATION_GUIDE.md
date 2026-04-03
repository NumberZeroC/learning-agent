# CCP 项目创建指南

使用 CCP 创建完整项目！

---

## 🚀 快速开始

### 方式 1：使用项目模板（推荐）

```bash
ccp run -i

You: 创建一个 Python CLI 项目，名字叫 my_cli
AI: [使用 project_template 工具]
    [创建完整项目结构]
    [显示下一步操作]
```

### 方式 2：自然语言描述

```bash
ccp run -i

You: 帮我创建一个 FastAPI 的 Web 项目
AI: [询问项目名称和描述]
    [选择合适的模板]
    [创建项目]
```

### 方式 3：自定义项目

```bash
ccp run -i

You: 创建一个数据分析项目，包含以下文件：
- src/data_loader.py - 数据加载模块
- src/analysis.py - 分析模块  
- src/visualization.py - 可视化模块
- tests/ - 测试目录
- requirements.txt - 依赖文件
AI: [调用 mkdir 创建目录]
    [调用 file_write_batch 创建文件]
    [显示项目结构]
```

---

## 📋 可用模板

### python_cli

**用途：** 命令行工具

**创建命令：**
```
You: 创建一个 CLI 项目，叫 weather_cli
```

**生成文件：**
```
weather_cli/
├── pyproject.toml
├── weather_cli/
│   ├── __init__.py
│   ├── cli.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── README.md
└── .gitignore
```

---

### python_package

**用途：** Python 库/包

**创建命令：**
```
You: 创建一个 Python 包，叫 data_utils
```

**生成文件：**
```
data_utils/
├── pyproject.toml
├── data_utils/
│   ├── __init__.py
│   └── core.py
├── tests/
│   └── test_core.py
└── README.md
```

---

### web_api

**用途：** FastAPI Web API

**创建命令：**
```
You: 创建一个 Web API 项目，叫 todo_api
```

**生成文件：**
```
todo_api/
├── pyproject.toml
├── todo_api/
│   ├── __init__.py
│   └── main.py
└── README.md
```

---

## 🛠️ 工具说明

### project_template

创建完整项目结构。

**参数：**
- `template` - 模板名称 (python_cli/python_package/web_api)
- `project_name` - 项目名称
- `description` - 项目描述
- `output_dir` - 输出目录（可选）

**示例：**
```python
{
    "template": "python_cli",
    "project_name": "my_project",
    "description": "My awesome CLI"
}
```

---

### file_write_batch

批量创建多个文件。

**参数：**
- `files` - 文件列表
  - `path` - 文件路径
  - `content` - 文件内容
- `overwrite` - 是否覆盖已存在文件

**示例：**
```python
{
    "files": [
        {"path": "src/main.py", "content": "print('Hello')"},
        {"path": "src/utils.py", "content": "def helper(): pass"},
        {"path": "README.md", "content": "# Project"}
    ]
}
```

---

### mkdir

创建目录。

**参数：**
- `path` - 目录路径
- `parents` - 是否创建父目录（默认 true）
- `exist_ok` - 已存在时不报错（默认 true）

**示例：**
```python
{
    "path": "src/utils/helpers"
}
```

---

## 📝 完整示例

### 创建 CLI 项目

```bash
$ ccp run -i

🤖 Claude Code Python (Interactive Mode)
Tools: bash, file_*, grep, glob, mkdir, project_template
Try: 'Create a Python CLI project called my_project'

You: 创建一个 Python CLI 项目，名字叫 todo_cli

🔧 Using tool: project_template
🎉 Project created from template: Python CLI Project
📁 Project name: todo_cli
📝 Description: A todo list CLI tool

Next steps:
  cd todo_cli
  pip install -e .
  todo_cli --help

✅ Created: todo_cli/pyproject.toml
✅ Created: todo_cli/todo_cli/__init__.py
✅ Created: todo_cli/todo_cli/cli.py
✅ Created: todo_cli/todo_cli/main.py
✅ Created: todo_cli/README.md
✅ Created: todo_cli/.gitignore
✅ Created: todo_cli/tests/__init__.py
✅ Created: todo_cli/tests/test_main.py
```

---

### 创建自定义项目

```bash
$ ccp run -i

You: 帮我创建一个数据分析项目

AI: 好的！我来帮你创建一个数据分析项目。
    请告诉我：
    1. 项目名称是什么？
    2. 主要功能是什么？

You: 叫 stock_analysis，用于股票数据分析

AI: 🔧 Using tool: mkdir
    ✅ Created directory: stock_analysis/src
    ✅ Created directory: stock_analysis/data
    ✅ Created directory: stock_analysis/notebooks
    
    🔧 Using tool: file_write_batch
    ✅ Created: stock_analysis/pyproject.toml
    ✅ Created: stock_analysis/src/__init__.py
    ✅ Created: stock_analysis/src/loader.py
    ✅ Created: stock_analysis/src/analyzer.py
    ✅ Created: stock_analysis/src/visualizer.py
    ✅ Created: stock_analysis/README.md
    ✅ Created: stock_analysis/requirements.txt
    
    📊 项目创建完成！
    
    项目结构：
    stock_analysis/
    ├── pyproject.toml
    ├── src/
    │   ├── loader.py      # 数据加载
    │   ├── analyzer.py    # 数据分析
    │   └── visualizer.py  # 数据可视化
    ├── data/              # 数据文件
    ├── notebooks/         # Jupyter notebooks
    ├── README.md
    └── requirements.txt
    
    下一步：
    cd stock_analysis
    pip install -e .
```

---

## 💡 提示技巧

### 1. 描述要具体

❌ 不好：
```
You: 创建一个项目
```

✅ 好：
```
You: 创建一个 Python CLI 项目，叫 weather_cli，用于查询天气
```

### 2. 指定文件结构

```
You: 创建项目，包含：
- src/api.py - API 客户端
- src/database.py - 数据库操作
- src/models.py - 数据模型
- tests/ - 测试
```

### 3. 要求特定功能

```
You: 创建 FastAPI 项目，需要：
- 用户认证
- 数据库连接
- RESTful API
- Swagger 文档
```

---

## 🎯 最佳实践

1. **使用模板** - 快速开始，结构标准
2. **明确需求** - 描述清楚项目类型和功能
3. **分步创建** - 复杂项目可以分多次创建
4. **及时测试** - 创建后运行测试验证
5. **版本控制** - 记得初始化 git

---

## 📚 相关文档

- `TECHNICAL_DESIGN.md` - 技术设计
- `ALIYUN_SETUP.md` - 阿里云配置
- `README.md` - 项目说明

---

*最后更新：2026-04-03*
