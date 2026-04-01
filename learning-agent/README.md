# Learning Agent - AI 知识生成系统

基于多 Agent 协作的 AI 知识体系生成工具，自动生成结构化学习内容。

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

### 安装依赖

```bash
pip3 install -r requirements.txt
```

### 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 DASHSCOPE_API_KEY
```

### 运行工作流

```bash
# 方式 1：直接运行
python3 run_workflow.py

# 方式 2：后台运行
./start_workflow.sh
```

### 启动 Web 服务

```bash
cd web
python3 app.py --host 0.0.0.0 --port 5001
```

访问：http://localhost:5001

## 📁 项目结构

```
learning-agent/
├── config/
│   └── agent_config.yaml    # Agent 配置
├── web/
│   ├── app.py               # Flask 主应用
│   ├── routes/
│   │   ├── chat_routes.py   # 聊天 API
│   │   └── workflow_routes.py # 工作流 API
│   └── templates/
│       ├── index.html       # 主页（工作流展示）
│       └── chat.html        # 聊天页面
├── services/
│   └── ask_service.py       # 问答服务
├── workflow_orchestrator.py # 工作流编排器
├── run_workflow.py          # 工作流启动脚本
├── requirements.txt         # Python 依赖
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

## 📄 许可证

MIT License

## 🙏 致谢

- 阿里云 DashScope 提供大模型 API
- Flask 提供 Web 框架
