# Docker 部署指南

**文档版本：** 1.0  
**更新日期：** 2026-04-05  
**状态：** ✅ 已完成

---

## 📦 快速开始

### 1. 构建 Docker 镜像

```bash
cd /home/admin/.openclaw/workspace/learning-agent

# 方式一：使用 docker-compose（推荐）
docker-compose build

# 方式二：直接构建
docker build -t learning-agent:latest .
```

### 2. 启动服务

```bash
# 方式一：使用 docker-compose（推荐）
docker-compose up -d

# 方式二：直接运行
docker run -d \
  --name learning-agent \
  -p 5001:5001 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/config:/app/config \
  --env-file .env \
  --restart unless-stopped \
  learning-agent:latest
```

### 3. 验证运行状态

```bash
# 查看容器状态
docker ps | grep learning-agent

# 查看日志
docker logs -f learning-agent

# 测试健康检查
curl http://localhost:5001/health
```

---

## 🔧 配置说明

### 环境变量

创建或编辑 `.env` 文件：

```bash
# DashScope API 配置
DASHSCOPE_API_KEY=sk-your-api-key-here
DASHSCOPE_BASE_URL=https://coding.dashscope.aliyuncs.com/v1

# Flask 配置
FLASK_ENV=production
```

### 数据持久化

以下目录会自动挂载到宿主机：

| 容器路径 | 宿主机路径 | 用途 |
|---------|-----------|------|
| `/app/data` | `./data` | 数据库、工作流结果 |
| `/app/logs` | `./logs` | 日志文件 |
| `/app/config` | `./config` | 配置文件 |

---

## 📋 常用命令

### 容器管理

```bash
# 启动
docker-compose up -d

# 停止
docker-compose down

# 重启
docker-compose restart

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 进入容器
docker-compose exec learning-agent bash
```

### 镜像管理

```bash
# 构建镜像
docker-compose build

# 查看镜像
docker images | grep learning-agent

# 删除镜像
docker rmi learning-agent:latest
```

### 数据管理

```bash
# 备份数据库
docker exec learning-agent tar czf - /app/data/learning_agent.db > backup.tar.gz

# 恢复数据库
docker exec -i learning-agent tar xzf - /app/data/ < backup.tar.gz

# 导出日志
docker exec learning-agent tar czf - /app/logs/ > logs_backup.tar.gz
```

---

## 🔍 故障排查

### 容器无法启动

```bash
# 查看详细日志
docker-compose logs

# 检查端口占用
netstat -tlnp | grep 5001

# 检查 Docker 状态
systemctl status docker
```

### 数据库问题

```bash
# 进入容器
docker-compose exec learning-agent bash

# 检查数据库文件
ls -la /app/data/

# 测试数据库连接
sqlite3 /app/data/learning_agent.db "SELECT COUNT(*) FROM chat_histories;"
```

### 健康检查失败

```bash
# 手动测试健康检查
curl http://localhost:5001/health

# 查看容器资源使用
docker stats learning-agent

# 重启容器
docker-compose restart
```

---

## 🚀 生产环境建议

### 1. 使用 systemd 管理

创建 `/etc/systemd/system/learning-agent.service`：

```ini
[Unit]
Description=Learning Agent Web Service
Requires=docker.service
After=docker.service

[Service]
Restart=always
WorkingDirectory=/home/admin/.openclaw/workspace/learning-agent
ExecStart=/usr/bin/docker-compose up
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

启用服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable learning-agent
sudo systemctl start learning-agent
sudo systemctl status learning-agent
```

### 2. 日志轮转

Docker 已配置日志轮转（最大 10MB，保留 3 个文件）。

额外配置系统日志：

```bash
# 创建日志配置
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

# 重启 Docker
sudo systemctl restart docker
```

### 3. 监控告警

```bash
# 安装监控工具
docker run -d \
  --name=container-monitor \
  -p 9000:9000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  dockerclues/container-monitor
```

---

## 📊 资源使用

### 镜像大小

```bash
docker images learning-agent
# 预计大小：~150MB
```

### 内存使用

```bash
docker stats learning-agent
# 预计内存：~200-500MB
```

### CPU 使用

```bash
# 查看 CPU 使用
docker stats --no-stream learning-agent
# 预计 CPU：<5%
```

---

## 🔐 安全建议

### 1. API Key 保护

- ✅ 使用 `.env` 文件，不要提交到 Git
- ✅ 设置文件权限：`chmod 600 .env`
- ✅ 使用 Docker secrets（生产环境）

### 2. 网络隔离

```yaml
# docker-compose.yml
networks:
  learning-network:
    driver: bridge
    internal: false  # 需要外部访问时设为 false
```

### 3. 只读文件系统

```yaml
# docker-compose.yml
services:
  learning-agent:
    read_only: true
    tmpfs:
      - /tmp
```

---

## 📈 性能优化

### 1. 使用多阶段构建

```dockerfile
# 构建阶段
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# 运行阶段
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python3", "web/app.py"]
```

### 2. 启用缓存

```bash
# 构建时使用缓存
docker build --cache-from learning-agent:latest -t learning-agent:latest .
```

### 3. 资源限制

```yaml
# docker-compose.yml
services:
  learning-agent:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 128M
```

---

## 📚 相关文件

- `Dockerfile` - Docker 镜像定义
- `docker-compose.yml` - Docker Compose 配置
- `.dockerignore` - Docker 构建排除文件
- `.env` - 环境变量（需手动创建）
- `requirements.txt` - Python 依赖

---

## 🆘 常见问题

### Q: 容器启动后立即退出？

A: 查看日志：
```bash
docker-compose logs
```

### Q: 如何更新镜像？

A: 重新构建并重启：
```bash
docker-compose build --no-cache
docker-compose up -d --force-recreate
```

### Q: 数据会丢失吗？

A: 不会，数据目录已挂载到宿主机：
```bash
ls -la ./data/
```

### Q: 如何备份？

A: 使用以下命令：
```bash
# 备份所有数据
tar czf learning-agent-backup.tar.gz data/ config/ logs/
```

---

**文档维护者：** AI 助手  
**最后更新：** 2026-04-05 23:45
