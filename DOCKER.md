# Learning Agent Docker 部署指南

使用 Docker 快速部署 Learning Agent。

## 🚀 快速启动

### 方式一：Docker Compose（推荐）

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DASHSCOPE_API_KEY

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 访问服务
http://localhost:5001
```

### 方式二：Docker 命令

```bash
# 1. 构建镜像
docker build -t learning-agent .

# 2. 运行容器
docker run -d \
  --name learning-agent \
  -p 5001:5001 \
  -e DASHSCOPE_API_KEY=sk-your-api-key \
  -v learning-agent-data:/app/data \
  -v learning-agent-logs:/app/logs \
  learning-agent

# 3. 查看日志
docker logs -f learning-agent
```

## 📦 环境变量

| 变量名 | 必需 | 说明 |
|--------|------|------|
| `DASHSCOPE_API_KEY` | ✅ | 阿里云 DashScope API Key |
| `LEARNING_AGENT_TOKEN` | ❌ | Web API 认证 Token（可选） |
| `FLASK_ENV` | ❌ | 运行环境（默认 production） |
| `LOG_LEVEL` | ❌ | 日志级别（默认 INFO） |

## 🔧 常用命令

```bash
# 启动
docker-compose up -d

# 停止
docker-compose down

# 重启
docker-compose restart

# 查看日志
docker-compose logs -f

# 进入容器
docker-compose exec learning-agent bash

# 重建镜像
docker-compose up -d --build
```

## 📁 数据持久化

Docker 卷自动持久化以下数据：

- `learning-agent-data` → `/app/data`（工作流结果、聊天记录）
- `learning-agent-logs` → `/app/logs`（日志文件）

## 🛡️ 安全建议

1. **不要将 `.env` 文件提交到 Git**
2. **使用强随机 Token**（如果启用认证）
3. **配置 Nginx 反向代理**（生产环境）
4. **启用 HTTPS**（使用 Let's Encrypt）

## 🐛 故障排查

### 容器无法启动

```bash
# 查看日志
docker-compose logs learning-agent

# 检查环境变量
docker-compose exec learning-agent env | grep DASHSCOPE
```

### API Key 无效

确保 `.env` 文件中配置了正确的 API Key：

```bash
DASHSCOPE_API_KEY=sk-your-real-api-key
```

### 数据丢失

检查 Docker 卷是否存在：

```bash
docker volume ls | grep learning-agent
```

---

**更多文档：** 详见 [README.md](README.md)
