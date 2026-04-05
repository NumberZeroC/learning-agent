# Learning Agent - AI 知识生成系统

基于多 Agent 协作的 AI 知识体系生成工具，自动生成结构化学习内容。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 核心功能

### 1. 知识生成工作流
- 5 层知识架构（基础理论 → 技术栈 → 核心能力 → 工程实践 → 面试准备）
- 多 Agent 并发执行，自动生成知识点
- 断点续传，防止中断丢失
- 实时保存进度

### 2. Web 聊天问答
- 与 AI Agent 实时对话
- 支持多个专家角色（理论/技术/工程/面试）
- 对话历史记录

## 🚀 快速开始

### 前置要求

- **Python 3.8+**（推荐 3.11+）
- **pip3**（Python 包管理器）
- **阿里云 DashScope API Key**（用于大模型调用）

> 💡 **检查 Python 版本：** `python3 --version`  
> 如果版本低于 3.8，请使用 `python3.11` 或更高版本

### 方式一：使用 Makefile（推荐）

```bash
# 1. 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或：venv\Scripts\activate  # Windows

# 2. 安装依赖
make install

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 DASHSCOPE_API_KEY

# 4. 运行工作流（可选，生成学习数据）
make run

# 5. 启动 Web 服务
make web
```

### 方式二：手动安装

#### 安装依赖

```bash
# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip3 install -r requirements.txt
```

#### 配置环境变量

**方式 1：直接编辑 .env 文件**
```bash
cp .env.example .env
nano .env  # 或使用你喜欢的编辑器
# 修改这一行：
DASHSCOPE_API_KEY=sk-your-real-api-key
```

**方式 2：通过 Web 配置页面（推荐）**
1. 启动 Web 服务后访问 http://localhost:5001/config
2. 在"API 配置"栏填写你的 API Key
3. 点击"保存全部配置"
4. ✅ **立即生效**，无需重启服务！

> 💡 **热更新支持：** 修改 API Key 或模型配置后，下一次 API 请求将自动使用新配置，无需重启服务。
> 
> 🌐 **支持多种大模型：** 阿里云 DashScope（通义千问）、OpenAI GPT、DeepSeek（深度求索）、智谱 AI（GLM）等

#### 运行工作流

```bash
# 方式 1：直接运行
python3 run_workflow.py

# 方式 2：后台运行
./start_workflow.sh
```

#### 启动 Web 服务

```bash
cd web
python3 app.py --host 0.0.0.0 --port 5001
```

访问：http://localhost:5001

### 其他 Makefile 命令

```bash
make help    # 查看所有可用命令
make test    # 运行测试
make clean   # 清理缓存和临时文件
make lint    # 代码检查
make format  # 代码格式化
```

## 📁 项目结构

```
learning-agent/
├── config/
│   └── agent_config.yaml    # Agent 配置
├── web/
│   ├── app.py               # Flask 主应用
│   ├── routes/              # API 路由
│   └── templates/           # HTML 模板
├── services/                # 业务服务
├── tests/                   # 单元测试
├── docs/                    # 开发文档
├── data/                    # 数据目录（运行时生成）
├── logs/                    # 日志目录
├── workflow_orchestrator.py # 工作流编排器
├── run_workflow.py          # 工作流启动脚本
├── requirements.txt         # Python 依赖
├── Makefile                 # 快速命令入口
└── .env.example             # 环境变量示例
```

## 🔧 配置说明

### 环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `DASHSCOPE_API_KEY` | 阿里云 DashScope API Key | `sk-xxx` |
| `LEARNING_AGENT_TOKEN` | Web API 认证 Token（可选） | 随机 32 字符 |

### Agent 配置

编辑 `config/agent_config.yaml` 配置：
- Agent 角色和系统提示词
- 模型参数（temperature, max_tokens）
- 重试策略和超时设置

## 📊 输出文件

工作流执行后，结果保存在 `data/workflow_results/`：

```
data/workflow_results/
├── workflow_YYYYMMDD_HHMMSS.json  # 完整工作流结果
├── layer_1_workflow.json          # 第 1 层结果
├── layer_2_workflow.json          # 第 2 层结果
├── ...
└── workflow_summary.json          # 历史汇总
```

## 🛡️ 安全建议

### 生产环境部署

1. **启用 API 认证**
   ```bash
   export LEARNING_AGENT_TOKEN=你的强随机 token
   ```

2. **使用 Nginx 反向代理**
   ```nginx
   location / {
       proxy_pass http://127.0.0.1:5001;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
   }
   ```

3. **配置 HTTPS**
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

4. **限制访问来源**
   - 配置防火墙/安全组
   - 使用 IP 白名单

## 📝 API 接口

### 工作流 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/workflow/layers` | GET | 获取所有已完成层 |
| `/api/workflow/layer/<id>` | GET | 获取单层详情 |
| `/api/workflow/topic/<layer>/<index>` | GET | 获取主题详情 |
| `/api/workflow/status` | GET | 获取运行状态 |
| `/api/workflow/summary` | GET | 获取汇总统计 |

### 聊天 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/chat/send` | POST | 发送消息给 Agent |
| `/api/chat/history` | GET | 获取对话历史 |

## 🤝 开发

### 添加新的知识层

编辑 `workflow_orchestrator.py` 中的 `_load_architecture()` 方法：

```python
{
    "layer": 6,
    "name": "新层级名称",
    "agent": "new_agent",
    "topics": [...]
}
```

### 自定义 Agent 角色

编辑 `config/agent_config.yaml` 中的 `agents` 部分。

## ❓ 常见问题

### 1. 安装依赖失败

**错误：** `No matching distribution found for flask>=2.3.0`

**原因：** Python 版本低于 3.8

**解决：**
```bash
# 检查版本
python3 --version

# 使用高版本 Python（如果有）
python3.11 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

### 2. API Key 未配置

**错误：** `DASHSCOPE_API_KEY 未加载`

**解决：**
```bash
# 复制示例配置
cp .env.example .env

# 编辑 .env 文件，填入真实的 API Key
nano .env  # 或使用你喜欢的编辑器

# 验证配置
grep DASHSCOPE_API_KEY .env
```

**或者通过 Web 配置页面：**
1. 访问 http://localhost:5001/config
2. 填写 API Key 并保存
3. ✅ 立即生效，无需重启服务！

### 3. Web 服务无法启动

**检查端口占用：**
```bash
# Linux/Mac
lsof -i :5001
# 或
netstat -tlnp | grep 5001

# 如果端口被占用，停止旧进程或更换端口
python3 web/app.py --port 5002
```

### 4. 工作流运行缓慢

**原因：** 需要调用大模型 API 生成 17 个主题的知识内容

**建议：**
- 预计耗时 15-30 分钟
- 可后台运行：`./start_workflow.sh`
- 随时查看进度：`ls -lh data/workflow_results/`

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 📚 相关文档

- [CHANGELOG.md](CHANGELOG.md) - 版本变更记录
- [CONTRIBUTING.md](CONTRIBUTING.md) - 贡献指南
- [docs/](docs/) - 开发文档

## 🙏 致谢

- 阿里云 DashScope 提供大模型 API
- Flask 提供 Web 框架
