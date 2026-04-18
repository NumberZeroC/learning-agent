# 🌐 public-release 分支 - 对外公开知识展示

**分支定位：** 对外公开发布的生产分支  
**创建日期：** 2026-04-18  
**运行模式：** 只读展示

---

## 🎯 分支用途

### 核心功能

✅ **保留功能：**
- 知识架构展示（主页）
- 层级详情浏览
- 主题详情查看
- 公开统计数据

❌ **已禁用功能：**
- 聊天问答
- 配置管理
- 工作流执行
- API Key 配置
- 后台管理

---

## 🚀 快速部署

### 方式 1：生产环境部署（推荐）

```bash
# 切换到公开分支
git checkout public-release

# 启动 Web 服务（80 端口）
./web/start_public_web.sh

# 或使用自定义端口
./web/start_public_web.sh --port 8080
```

**访问地址：** http://localhost:80 或 http://your-domain.com

---

### 方式 2：Systemd 服务部署

```bash
# 创建 systemd 服务
sudo cat > /etc/systemd/system/learning-agent-public.service << EOF
[Unit]
Description=Learning Agent Public Website
After=network.target

[Service]
Type=simple
User=admin
WorkingDirectory=/home/admin/.openclaw/workspace/learning-agent
ExecStart=/home/admin/.openclaw/workspace/learning-agent/venv/bin/python web/public_app.py --port 80
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable learning-agent-public
sudo systemctl start learning-agent-public

# 查看状态
sudo systemctl status learning-agent-public
```

---

### 方式 3：Docker 部署

```bash
# 构建镜像
docker build -t learning-agent-public .

# 运行容器
docker run -d \
  --name learning-agent-public \
  -p 80:80 \
  -v $(pwd)/data:/app/data \
  learning-agent-public
```

---

## 📁 文件结构

```
learning-agent/
├── web/
│   ├── public_app.py              # 公开版 Web 应用（只读）
│   ├── start_public_web.sh        # 启动脚本
│   └── templates/
│       ├── public_index.html      # 主页（知识架构展示）
│       ├── public_layer.html      # 层级详情页
│       └── public_topic.html      # 主题详情页
├── config/
│   └── knowledge_framework.yaml   # 知识架构配置
├── data/
│   └── workflow_results/          # 工作流生成结果
└── docs/
    └── PUBLIC_RELEASE_BRANCH.md   # 本文档
```

---

## 🔒 安全特性

### 只读模式

- ✅ 无写操作 API
- ✅ 不暴露内部配置
- ✅ 不暴露 API Key
- ✅ 简化的错误信息（不暴露堆栈）

### 安全头配置

```python
response.headers["X-Content-Type-Options"] = "nosniff"
response.headers["X-Frame-Options"] = "DENY"
response.headers["X-XSS-Protection"] = "1; mode=block"
response.headers["Cache-Control"] = "public, max-age=300"
```

### 数据过滤

API 返回数据经过过滤，只公开必要信息：

```python
# 内部数据（不公开）
- API Key
- 详细错误信息
- 系统配置
- 用户数据

# 公开数据
- 知识架构
- 主题列表
- 统计信息
- 生成内容
```

---

## 📊 页面预览

### 主页 (/)

```
┌─────────────────────────────────────────────────┐
│     🤖 AI Agent 开发知识体系                      │
│   从基础理论到面试准备的全链路学习路径            │
├─────────────────────────────────────────────────┤
│  📊 5 知识层级  │  📚 17 核心主题  │  ✅ 12 已生成  │
├─────────────────────────────────────────────────┤
│  ┌───────────┐ ┌───────────┐ ┌───────────┐     │
│  │ Layer 1   │ │ Layer 2   │ │ Layer 3   │     │
│  │ 基础理论层 │ │ 技术栈层  │ │ 核心能力层 │     │
│  │ AI 基础... │ │ Python... │ │ 任务规划..│     │
│  └───────────┘ └───────────┘ └───────────┘     │
│  ┌───────────┐ ┌───────────┐                    │
│  │ Layer 4   │ │ Layer 5   │                    │
│  │ 工程实践层 │ │ 面试准备层 │                    │
│  │ 项目经验..│ │ 算法题... │                    │
│  └───────────┘ └───────────┘                    │
└─────────────────────────────────────────────────┘
```

### 层级页 (/layer/1)

```
┌─────────────────────────────────────────────────┐
│ ← 返回首页                                       │
├─────────────────────────────────────────────────┤
│  ① 基础理论层                                    │
│  机器学习和深度学习基础理论                      │
├─────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────┐    │
│  │ AI 基础                                  │    │
│  │ 机器学习和深度学习基础概念和原理          │    │
│  │ 🔥 核心  📚 3 个子主题                    │    │
│  └─────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────┐    │
│  │ LLM 原理                                 │    │
│  │ 大语言模型核心原理和技术                 │    │
│  │ 🔥 核心  📚 3 个子主题                    │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

---

## 🌐 Nginx 反向代理配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 启用 HTTPS（推荐）
    # listen 443 ssl;
    # ssl_certificate /path/to/cert.pem;
    # ssl_certificate_key /path/to/key.pem;
}
```

---

## 📈 监控与维护

### 查看日志

```bash
# 实时日志
tail -f logs/web_public.log

# 错误日志
grep ERROR logs/web_public.log

# 访问统计
wc -l logs/web_public.log
```

### 健康检查

```bash
# 检查服务状态
curl http://localhost/health

# 检查 API
curl http://localhost/api/stats
curl http://localhost/api/layers
```

### 更新部署

```bash
# 拉取最新代码
git checkout public-release
git pull origin public-release

# 重启服务
sudo systemctl restart learning-agent-public

# 或手动重启
./web/stop_web.sh
./web/start_public_web.sh
```

---

## 🔄 与 main 分支同步

定期从 main 分支同步知识内容和 bug 修复：

```bash
# 切换到公开分支
git checkout public-release

# 合并 main 分支的变更
git merge main

# 解决冲突（如有）
# ...

# 推送更新
git push origin public-release

# 重启服务
sudo systemctl restart learning-agent-public
```

**注意：** 合并时保留 `public-release` 分支的简化 Web 应用，不要覆盖 `public_app.py`。

---

## ⚠️ 注意事项

### 生产环境部署

1. **禁用调试模式**
   ```bash
   # 不要使用 --debug 参数
   ./web/start_public_web.sh
   ```

2. **配置防火墙**
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp  # HTTPS
   ```

3. **启用 HTTPS**（强烈推荐）
   - 使用 Let's Encrypt 免费证书
   - 配置 Nginx 反向代理

4. **定期备份**
   ```bash
   # 备份生成的知识内容
   tar -czf backup_$(date +%Y%m%d).tar.gz data/workflow_results/
   ```

---

## 📞 总结

**public-release 分支特点：**

| 特性 | 说明 |
|------|------|
| **定位** | 对外公开发布的生产分支 |
| **功能** | 只读展示知识内容 |
| **安全** | 不暴露配置和 API Key |
| **部署** | 支持多种部署方式 |
| **维护** | 定期从 main 分支同步 |

**适用场景：**

- ✅ 对外展示学习成果
- ✅ 公开知识分享网站
- ✅ 生产环境部署
- ✅ 演示和展示

**不适用场景：**

- ❌ 内部开发测试
- ❌ 工作流执行
- ❌ 聊天问答
- ❌ 配置管理

---

**文档版本：** 1.0  
**最后更新：** 2026-04-18
