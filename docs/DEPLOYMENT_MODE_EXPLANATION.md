# 📦 部署方式说明

**当前状态：** 混合模式（systemd 运行 + Docker 可用）

---

## 🔍 当前运行方式

### ✅ 当前：systemd 服务运行

**进程信息：**
```bash
PID: 771222
命令：/home/admin/.openclaw/workspace/learning-agent/venv/bin/python3 web/app.py --host 0.0.0.0 --port 5001
服务名：learning-agent.service
状态：active (running)
内存：22.8MB
```

**服务文件：**
```ini
[Unit]
Description=Learning Agent Web Service
After=network.target

[Service]
Type=simple
User=admin
WorkingDirectory=/home/admin/.openclaw/workspace/learning-agent
EnvironmentFile=/home/admin/.openclaw/workspace/learning-agent/.env
ExecStart=/home/admin/.openclaw/workspace/learning-agent/venv/bin/python3 web/app.py --host 0.0.0.0 --port 5001
Restart=always

[Install]
WantedBy=multi-user.target
```

**优点：**
- ✅ 直接运行，性能好
- ✅ 调试方便
- ✅ 日志易查看（`journalctl -u learning-agent`）
- ✅ 资源占用低（无容器开销）

**缺点：**
- ⚠️ 依赖系统 Python 环境
- ⚠️ 迁移需要手动配置
- ⚠️ 环境隔离性差

---

## 🐳 Docker 容器化（可用但未使用）

### Docker 文件已准备

**文件清单：**
```
Dockerfile           # Docker 镜像构建文件
docker-compose.yml   # Docker Compose 配置
.dockerignore        # Docker 构建排除文件
DOCKER.md            # Docker 部署文档
```

### Dockerfile 内容

```dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p logs data data/llm_audit_logs data/workflow_results config/backups

EXPOSE 5001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

CMD ["python3", "web/app.py", "--host", "0.0.0.0", "--port", "5001"]
```

### docker-compose.yml 内容

```yaml
version: '3.8'

services:
  learning-agent:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: learning-agent
    restart: unless-stopped
    ports:
      - "5001:5001"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
      - ./.env:/app/.env:ro
    environment:
      - FLASK_ENV=production
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY:-}
      - DASHSCOPE_BASE_URL=${DASHSCOPE_BASE_URL:-}
    networks:
      - learning-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Docker 镜像状态

```bash
# 镜像已构建
REPOSITORY: learning-agent
TAG: latest
IMAGE ID: 4d019229add6
CREATED: 3 days ago
SIZE: 133MB
```

### 当前无运行容器

```bash
# 没有运行中的 Docker 容器
docker ps -a | grep learning-agent
# (无输出)
```

---

## 📊 对比分析

| 特性 | systemd 运行 | Docker 容器化 |
|------|-------------|--------------|
| **当前状态** | ✅ 正在使用 | ⚠️ 可用但未使用 |
| **性能** | ✅ 原生性能 | ⚠️ 轻微容器开销 |
| **环境隔离** | ⚠️ 依赖系统环境 | ✅ 完全隔离 |
| **迁移性** | ⚠️ 需手动配置 | ✅ 一键部署 |
| **调试** | ✅ 方便 | ⚠️ 需进入容器 |
| **资源占用** | ✅ 低（22.8MB） | ⚠️ 略高（+10-20MB） |
| **日志管理** | ✅ journalctl | ⚠️ docker logs |
| **自动重启** | ✅ systemd | ✅ Docker restart |
| **网络访问** | ✅ 直接访问 | ✅ 端口映射 |
| **数据持久化** | ⚠️ 本地存储 | ✅ 卷挂载 |

---

## 🔄 切换到 Docker 容器化

### 方案 1：完全切换到 Docker

**步骤：**

```bash
# 1. 停止 systemd 服务
sudo systemctl stop learning-agent
sudo systemctl disable learning-agent

# 2. 停止并删除现有容器（如果有）
docker stop learning-agent 2>/dev/null || true
docker rm learning-agent 2>/dev/null || true

# 3. 重新构建镜像（可选）
cd /home/admin/.openclaw/workspace/learning-agent
docker build -t learning-agent:latest .

# 4. 启动容器
docker run -d \
  --name learning-agent \
  --restart unless-stopped \
  -p 5001:5001 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/.env:/app/.env:ro \
  -e LEARNING_AGENT_MASTER_KEY=$(grep LEARNING_AGENT_MASTER_KEY .env | cut -d= -f2) \
  learning-agent:latest

# 5. 验证
docker ps | grep learning-agent
docker logs learning-agent
```

**优点：**
- ✅ 完全容器化
- ✅ 环境隔离
- ✅ 易于迁移

**缺点：**
- ⚠️ 需要手动管理容器
- ⚠️ systemd 监控失效

---

### 方案 2：使用 Docker Compose（推荐）

**步骤：**

```bash
# 1. 停止 systemd 服务
sudo systemctl stop learning-agent
sudo systemctl disable learning-agent

# 2. 停止旧容器
docker-compose down

# 3. 启动容器
cd /home/admin/.openclaw/workspace/learning-agent
docker-compose up -d

# 4. 验证
docker-compose ps
docker-compose logs -f
```

**优点：**
- ✅ 配置管理简单
- ✅ 支持多服务编排
- ✅ 易于扩展

**缺点：**
- ⚠️ 需要安装 docker-compose

---

### 方案 3：混合模式（当前）

**说明：**
- ✅ systemd 管理主服务
- ✅ Docker 镜像用于测试/备份
- ✅ 可随时切换

**优点：**
- ✅ 灵活性高
- ✅ 兼容性好
- ✅ 风险低

**缺点：**
- ⚠️ 维护两套配置
- ⚠️ 可能混淆

---

## 🎯 建议

### 推荐方案：保持当前 systemd 运行

**理由：**
1. ✅ 性能最优（无容器开销）
2. ✅ 调试方便（直接访问日志）
3. ✅ 资源占用低
4. ✅ 单机部署足够
5. ✅ 已有完善监控（systemd）

**适用场景：**
- 单机部署
- 开发测试环境
- 资源受限环境

---

### 何时切换到 Docker？

**建议切换的场景：**
1. 需要多机部署
2. 需要环境完全隔离
3. 需要频繁迁移
4. 需要 Kubernetes 编排
5. 需要 CI/CD 集成

**切换时机：**
- 生产环境部署
- 多环境（开发/测试/生产）
- 微服务架构

---

## 📝 总结

**当前状态：**
```
✅ systemd 服务运行（主用）
🐳 Docker 镜像可用（备用）
❌ 无运行中的 Docker 容器
```

**建议：**
- 继续使用 systemd（适合当前场景）
- 保留 Docker 配置（用于未来扩展）
- 需要时随时切换

**切换命令：**
```bash
# 查看当前状态
sudo systemctl status learning-agent

# 切换到 Docker
sudo systemctl stop learning-agent
docker-compose up -d

# 切换回 systemd
docker-compose down
sudo systemctl start learning-agent
```

---

_文档更新时间：2026-04-06 11:48_  
_版本：v1.0_
