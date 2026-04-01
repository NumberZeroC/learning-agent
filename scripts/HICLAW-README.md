# 🦞 HiClaw 配置和启动说明

**配置时间：** 2026-03-31  
**公网 IP：** 39.97.249.78

---

## 📁 文件位置

| 文件 | 路径 | 说明 |
|------|------|------|
| **启动脚本** | `/home/admin/start-hiclaw.sh` | 一键启动 HiClaw |
| **停止脚本** | `/home/admin/stop-hiclaw.sh` | 一键停止 HiClaw |
| **重启脚本** | `/home/admin/restart-hiclaw.sh` | 一键重启 HiClaw |
| **配置文件** | `/home/admin/hiclaw-manager.env` | HiClaw 配置 |
| **工作空间** | `/home/admin/hiclaw-manager/` | Manager Agent 工作区 |
| **数据卷** | `hiclaw-data` | Docker 数据卷 |

---

## 🚀 一键启动

```bash
# 启动 HiClaw
bash /home/admin/start-hiclaw.sh

# 或使用完整路径
bash /home/admin/.openclaw/workspace/scripts/start-hiclaw.sh
```

---

## 🛑 停止服务

```bash
bash /home/admin/stop-hiclaw.sh
```

---

## 🔄 重启服务

```bash
bash /home/admin/restart-hiclaw.sh
```

---

## 🌐 访问地址

### Element Web（浏览器）

```
URL: http://39.97.249.78:5097/#/login

用户名：admin
密码：HiClaw2026!
```

### 其他控制台

| 服务 | URL | 端口 |
|------|-----|------|
| **Element Web** | http://39.97.249.78:5097 | 5097 |
| **Higress 控制台** | http://39.97.249.78:5098 | 5098 |
| **OpenClaw 控制台** | http://39.97.249.78:5096 | 5096 |
| **Higress AI Gateway** | http://39.97.249.78:5099 | 5099 |

### 移动端访问

```
1. 下载 FluffyChat 或 Element
2. 设置 homeserver: http://39.97.249.78:5099
3. 登录:
   用户名：admin
   密码：HiClaw2026!
```

---

## 📋 端口配置

| 服务 | 容器端口 | 主机端口 |
|------|----------|----------|
| Higress AI Gateway | 8080 | 5099 |
| Higress 控制台 | 8001 | 5098 |
| Element Web | 8088 | 5097 |
| OpenClaw 控制台 | 18888 | 5096 |

---

## 🔧 配置文件

**文件：** `/home/admin/hiclaw-manager.env`

### 关键配置项

```bash
# 访问模式
HICLAW_LOCAL_ONLY=0  # 0=允许外部访问，1=仅本机

# 端口配置
HICLAW_PORT_GATEWAY=5099
HICLAW_PORT_CONSOLE=5098
HICLAW_PORT_ELEMENT_WEB=5097
HICLAW_PORT_OPENCLAW_CONSOLE=5096

# LLM 配置
HICLAW_LLM_PROVIDER=qwen
HICLAW_DEFAULT_MODEL=qwen3.5-plus
HICLAW_LLM_API_KEY=sk-sp-1103f012953e45d984ab8fbd486e6e16

# 管理员凭据
HICLAW_ADMIN_USER=admin
HICLAW_ADMIN_PASSWORD=HiClaw2026!

# Matrix 域名
HICLAW_MATRIX_DOMAIN=matrix-local.hiclaw.io:5099
```

---

## 🐳 Docker 容器

```bash
# 查看运行状态
docker ps | grep hiclaw

# 查看日志
docker logs hiclaw-manager -f

# 查看实时日志（最后 100 行）
docker logs hiclaw-manager --tail 100 -f

# 重启容器
docker restart hiclaw-manager

# 停止容器
docker stop hiclaw-manager

# 删除容器（不删除数据）
docker rm hiclaw-manager
```

---

## 📊 网络配置

```bash
# 查看 Docker 网络
docker network inspect hiclaw-net

# 查看端口绑定
docker port hiclaw-manager
```

---

## 🔐 安全配置

### 防火墙设置（如需要）

```bash
# 开放端口（如果使用防火墙）
sudo ufw allow 5096:5099/tcp

# 或者使用 iptables
sudo iptables -A INPUT -p tcp --dport 5096:5099 -j ACCEPT
```

### 安全建议

1. ✅ 使用强密码（当前：HiClaw2026!）
2. ✅ 定期更新密码
3. ✅ 监控访问日志
4. ✅ 定期备份数据卷

---

## 💾 数据备份

```bash
# 备份数据卷
docker run --rm -v hiclaw-data:/data -v /home/admin/hiclaw-backup:/backup ubuntu tar czf /backup/hiclaw-data-$(date +%Y%m%d).tar.gz -C /data .

# 恢复数据卷
docker run --rm -v hiclaw-data:/data -v /home/admin/hiclaw-backup:/backup ubuntu tar xzf /backup/hiclaw-data-20260331.tar.gz -C /data
```

---

## 🛠️ 故障排查

### 容器无法启动

```bash
# 查看日志
docker logs hiclaw-manager --tail 100

# 检查端口占用
netstat -tlnp | grep 5099

# 检查配置文件
cat /home/admin/hiclaw-manager.env
```

### 无法访问 Web 界面

```bash
# 检查容器状态
docker ps | grep hiclaw-manager

# 检查端口绑定
docker port hiclaw-manager

# 检查防火墙
sudo ufw status
```

### Matrix 服务不可用

```bash
# 重启容器
docker restart hiclaw-manager

# 等待服务就绪
sleep 60

# 测试连接
curl http://localhost:5099/_matrix/client/versions
```

---

## 📝 更新升级

```bash
# 拉取最新镜像
docker pull higress-registry.cn-hangzhou.cr.aliyuncs.com/higress/hiclaw-manager:latest

# 停止当前容器
bash /home/admin/stop-hiclaw.sh

# 启动新版本
bash /home/admin/start-hiclaw.sh
```

---

## 🎯 快速参考

```bash
# 启动
bash /home/admin/start-hiclaw.sh

# 停止
bash /home/admin/stop-hiclaw.sh

# 重启
bash /home/admin/restart-hiclaw.sh

# 查看状态
docker ps | grep hiclaw

# 查看日志
docker logs hiclaw-manager -f

# 访问地址
http://39.97.249.78:5097
```

---

## 📞 支持

- **文档：** https://github.com/higress-group/hiclaw
- **问题反馈：** GitHub Issues
- **社区：** Discord

---

*最后更新：2026-03-31*
