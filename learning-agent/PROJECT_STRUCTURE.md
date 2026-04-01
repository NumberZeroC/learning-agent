# Learning Agent 项目结构说明

## 📁 精简后的目录结构

```
learning-agent/
├── config/
│   └── agent_config.yaml        # Agent 配置（5 个专家角色）
│
├── services/
│   └── ask_service.py           # 问答服务（聊天功能核心）
│
├── web/
│   ├── app.py                   # Flask 主应用
│   ├── start_web.sh             # Web 启动脚本
│   ├── stop_web.sh              # Web 停止脚本
│   ├── routes/
│   │   ├── chat_routes.py       # 聊天 API 路由
│   │   └── workflow_routes.py   # 工作流 API 路由
│   └── templates/
│       ├── chat.html            # 聊天页面
│       ├── layer.html           # 层级详情页面
│       └── workflow.html        # 工作流展示页面（主页）
│
├── data/
│   ├── workflow_results/        # 工作流输出结果
│   └── knowledge/               # 知识库（可选）
│
├── logs/                        # 日志目录
│
├── workflow_orchestrator.py     # 工作流编排器（核心）
├── run_workflow.py              # 工作流启动脚本
├── start_workflow.sh            # 工作流后台启动脚本
├── deploy.sh                    # 一键部署脚本
│
├── requirements.txt             # Python 依赖
├── .env.example                 # 环境变量示例
├── .gitignore                   # Git 忽略配置
└── README.md                    # 项目说明
```

## 🎯 核心功能模块

### 1. 知识生成工作流

**文件：** `workflow_orchestrator.py`

**功能：**
- 5 层知识架构并发执行
- 每层独立 Agent 负责
- 断点续传，实时保存
- 输出 JSON 格式结果

**运行方式：**
```bash
python3 run_workflow.py
# 或
./start_workflow.sh  # 后台运行
```

### 2. Web 聊天问答

**文件：** `services/ask_service.py` + `web/routes/chat_routes.py`

**功能：**
- 多 Agent 角色切换
- 对话历史管理
- 实时回复生成

**运行方式：**
```bash
cd web
./start_web.sh
```

### 3. Web 成果展示

**文件：** `web/routes/workflow_routes.py` + `web/templates/workflow.html`

**功能：**
- 工作流进度展示
- 层级知识浏览
- 知识点详情查看

**访问地址：** http://localhost:5001

## 📊 删除的冗余文件

### 已删除的文件类型：

1. **AutoGen 相关**
   - `main.py` (AutoGen 版本)
   - `main_autogen_backup.py`
   - `generator.py`
   - `deep_knowledge_generator.py`
   - `knowledge_generator.py`
   - `verify_agents.py`

2. **文档和说明**
   - `AUTOGEN_ARCHITECTURE.md`
   - `AUTO_GENERATION_COMPLETE.md`
   - `CONCURRENT_DESIGN.md`
   - `MULTI_MODEL_CONFIG.md`
   - `PROJECT_COMPLETE.md`
   - `REFACTOR_COMPLETE.md`
   - `WORKFLOW_GUIDE.md`
   - 等其他冗余文档

3. **测试文件**
   - `test_qwen_api.py`
   - `test_workflow_mock.py`

4. **工具脚本**
   - `cli.py`

5. **冗余服务**
   - `services/task_service.py`
   - `services/llm_service.py`
   - `services/llm_audit_log.py`

6. **冗余路由**
   - `web/routes/config_routes.py`

7. **冗余模板**
   - `web/templates/config.html`
   - `web/templates/index.html`

8. **冗余配置**
   - `config/autogen_config.yaml`
   - `config/knowledge_schema.json`
   - `config/backups/`

## 🔧 配置说明

### 环境变量（.env）

```bash
# 必需
DASHSCOPE_API_KEY=sk-your-api-key-here

# 可选（生产环境）
LEARNING_AGENT_TOKEN=your-secret-token
```

### Agent 配置（config/agent_config.yaml）

配置 5 个专家 Agent：
- `theory_worker` - 基础理论专家
- `tech_stack_worker` - 技术栈专家
- `core_skill_worker` - 核心能力专家
- `engineering_worker` - 工程实践专家
- `interview_worker` - 面试准备专家

## 🚀 快速开始

### 1. 安装依赖

```bash
pip3 install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入 DASHSCOPE_API_KEY
```

### 3. 运行工作流

```bash
python3 run_workflow.py
```

### 4. 启动 Web 服务

```bash
cd web
./start_web.sh
```

访问：http://localhost:5001

## 📦 上传到 Git

### 1. 初始化仓库

```bash
cd /home/admin/.openclaw/workspace/learning-agent
git init
```

### 2. 添加文件

```bash
git add .
```

### 3. 提交

```bash
git commit -m "Initial commit: Learning Agent 精简版"
```

### 4. 关联远程仓库

```bash
git remote add origin https://github.com/your-username/learning-agent.git
git push -u origin main
```

## ⚠️ 注意事项

1. **数据文件不上传**
   - `data/` 目录已加入 `.gitignore`
   - 工作流结果和知识库不上传

2. **日志文件不上传**
   - `logs/` 目录已加入 `.gitignore`

3. **环境变量不上传**
   - `.env` 文件已加入 `.gitignore`
   - 使用 `.env.example` 作为模板

4. **缓存文件不上传**
   - `__pycache__/` 已忽略
   - `*.pyc` 已忽略

## 📝 下一步优化建议

1. **添加单元测试**
2. **配置 CI/CD**
3. **添加 Docker 支持**
4. **完善 API 文档**
5. **添加用户认证系统**
