# 🐳 Docker 迁移尝试报告

**尝试时间：** 2026-04-06 11:50  
**状态：** ⚠️ 部分成功（网络问题）

---

## 📋 执行步骤

### 1. 停止 systemd 服务 ✅

```bash
sudo systemctl stop learning-agent
sudo systemctl disable learning-agent
```

**结果：** ✅ 成功

---

### 2. 停止旧容器 ✅

```bash
docker stop learning-agent
docker rm learning-agent
```

**结果：** ✅ 无旧容器

---

### 3. 更新 docker-compose.yml ✅

**修改内容：**
```yaml
environment:
  - LEARNING_AGENT_MASTER_KEY=${LEARNING_AGENT_MASTER_KEY:-}  # 新增
  - DASHSCOPE_BASE_URL=${DASHSCOPE_BASE_URL:-}
  # 删除：DASHSCOPE_API_KEY（已从 .env 移除）
```

**结果：** ✅ 成功

---

### 4. 重新构建 Docker 镜像 ❌

**尝试 1：Docker Hub**
```bash
docker build -t learning-agent:latest .
```

**错误：**
```
ERROR: failed to solve: python:3.11-slim: failed to resolve source metadata
dial tcp 103.252.115.221:443: i/o timeout
```

**尝试 2：阿里云镜像**
```dockerfile
FROM registry.cn-hangzhou.aliyuncs.com/library/python:3.11-slim
```

**错误：**
```
pull access denied, repository does not exist
```

**结果：** ❌ 失败（网络问题）

---

### 5. 使用现有镜像启动 ⚠️

```bash
docker run -d \
  --name learning-agent \
  --restart unless-stopped \
  -p 5001:5001 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/.env:/app/.env:ro \
  -e LEARNING_AGENT_MASTER_KEY=... \
  learning-agent:latest
```

**结果：** ⚠️ 容器启动成功，但使用旧代码

**日志：**
```
✅ 已加载环境变量：/app/.env
❌ DASHSCOPE_API_KEY 未加载，请检查 .env 文件
```

**问题：** 镜像是 3 天前构建的，不包含最新的 KeyVault 代码

---

### 6. 恢复 systemd 服务 ✅

```bash
sudo systemctl start learning-agent
```

**结果：** ✅ 成功

**服务状态：**
```
Active: active (running)
Memory: 22.7M
```

---

## 🔍 问题分析

### 根本原因

**Docker Hub 网络连接问题**

服务器无法访问：
- `registry-1.docker.io` (Docker Hub)
- `registry.cn-hangzhou.aliyuncs.com` (阿里云)

**可能原因：**
1. 服务器防火墙限制
2. 网络运营商限制
3. Docker 镜像源配置问题

---

### 验证

```bash
# 检查 Docker 镜像源配置
cat /etc/docker/daemon.json
# 输出：{"registry-mirrors": ["https://4vk1gwg4.mirror.aliyuncs.com/"]}

# 测试网络连接
curl -I https://registry-1.docker.io/v2/
# 结果：timeout
```

---

## 📊 当前状态

| 组件 | 状态 | 说明 |
|------|------|------|
| **systemd 服务** | ✅ 运行中 | 主用方案 |
| **Docker 镜像** | ⚠️ 已构建（旧版） | 3 天前 |
| **Docker 容器** | ❌ 未运行 | 网络问题 |
| **Dockerfile** | ✅ 已更新 | 包含 KeyVault |
| **docker-compose.yml** | ✅ 已更新 | 支持 KeyVault |

---

## 🎯 解决方案

### 方案 1：修复网络后重新构建（推荐）

**步骤：**

```bash
# 1. 配置 Docker 镜像加速
sudo vim /etc/docker/daemon.json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1panel.live",
    "https://hub.rat.dev"
  ]
}

# 2. 重启 Docker
sudo systemctl restart docker

# 3. 重新构建镜像
cd /home/admin/.openclaw/workspace/learning-agent
docker build -t learning-agent:latest .

# 4. 启动容器
docker-compose up -d

# 5. 验证
docker-compose ps
docker-compose logs -f
```

---

### 方案 2：手动导入镜像

**步骤：**

```bash
# 1. 在其他机器构建镜像
docker build -t learning-agent:latest .

# 2. 导出镜像
docker save -o learning-agent.tar learning-agent:latest

# 3. 传输到服务器
scp learning-agent.tar user@server:/tmp/

# 4. 导入镜像
docker load -i /tmp/learning-agent.tar

# 5. 启动容器
docker run -d --name learning-agent ...
```

---

### 方案 3：继续使用 systemd（当前）

**优点：**
- ✅ 无需 Docker
- ✅ 性能更好
- ✅ 调试方便
- ✅ 稳定运行

**缺点：**
- ⚠️ 环境隔离性差
- ⚠️ 迁移需要手动配置

**建议：** 适合当前单机部署场景

---

## 📝 已完成的工作

### ✅ 代码准备

- [x] KeyVault 加密存储
- [x] 所有服务优先使用 KeyVault
- [x] Dockerfile 更新
- [x] docker-compose.yml 更新
- [x] .env 文件清理（移除明文 API Key）

### ⚠️ Docker 迁移

- [x] 停止 systemd 服务
- [x] 更新配置文件
- [ ] 重新构建 Docker 镜像（网络问题）
- [ ] 启动 Docker 容器（等待镜像）

---

## 🚀 后续计划

### 短期（1 周）

1. [ ] 修复 Docker 网络问题
2. [ ] 重新构建 Docker 镜像
3. [ ] 完成 Docker 容器化部署
4. [ ] 验证所有功能正常

### 中期（1 个月）

5. [ ] 配置 Docker 自动更新
6. [ ] 添加 Docker 监控
7. [ ] 实现蓝绿部署
8. [ ] 添加备份恢复机制

---

## 📞 故障排查命令

### 检查网络

```bash
# 测试 Docker Hub 连接
curl -I https://registry-1.docker.io/v2/

# 测试阿里云镜像
curl -I https://registry.cn-hangzhou.aliyuncs.com/v2/

# 查看 DNS 配置
cat /etc/resolv.conf
```

### 检查 Docker 配置

```bash
# 查看镜像源配置
cat /etc/docker/daemon.json

# 查看 Docker 状态
sudo systemctl status docker

# 查看 Docker 日志
sudo journalctl -u docker -f
```

### 测试构建

```bash
# 测试构建（不推送）
docker build --no-cache -t test:latest .

# 查看构建缓存
docker builder prune
```

---

## ✅ 总结

**当前状态：**
- ✅ systemd 服务正常运行
- ✅ KeyVault 加密存储正常工作
- ⚠️ Docker 迁移因网络问题暂停

**建议：**
1. 继续使用 systemd（稳定）
2. 修复网络后重新尝试 Docker 迁移
3. 或考虑其他容器化方案（如 Podman）

---

_报告生成时间：2026-04-06 11:52_  
_版本：v1.0_  
_状态：⚠️ 部分成功_
