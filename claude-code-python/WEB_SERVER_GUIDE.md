# 🌐 CCP Web 界面使用指南

**日期：** 2026-04-03  
**状态：** ✅ 完成

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd /home/admin/.openclaw/workspace/claude-code-python
.venv/bin/pip install aiohttp
```

### 2. 启动 Web 服务器

```bash
# 方式 1: 使用脚本
.venv/bin/python scripts/start_web.py

# 方式 2: 使用命令行工具
.venv/bin/ccp-web

# 方式 3: 直接运行模块
.venv/bin/python -m src.web_server
```

### 3. 访问 Web 界面

打开浏览器访问：
```
http://localhost:8080
```

---

## 🎨 界面功能

### 主要特性

- ✅ **现代化 UI** - 渐变设计，响应式布局
- ✅ **实时聊天** - WebSocket 双向通信
- ✅ **流式响应** - 思考中状态，实时反馈
- ✅ **会话管理** - 自动创建会话 ID
- ✅ **错误处理** - 友好的错误提示
- ✅ **降级支持** - WebSocket 不可用时自动切换 HTTP

### 界面预览

```
┌─────────────────────────────────────────┐
│  🤖 CCP - Claude Code Python            │
│  AI 编程助手 - Web 界面                  │
├─────────────────────────────────────────┤
│                                         │
│  👤 你好！我是 CCP，你的 AI 编程助手     │
│     有什么可以帮你的吗？                │
│                                         │
│  💬 创建一个 Python 项目                 │
│                                         │
│  🤖 正在思考...                         │
│                                         │
│  🤖 好的，我来创建一个 Python 项目...    │
│     [项目创建完成]                      │
│                                         │
├─────────────────────────────────────────┤
│  [输入消息...            ] [ 发送 ]     │
└─────────────────────────────────────────┘
```

---

## 💻 API 接口

### WebSocket 接口

**连接：**
```
ws://localhost:8080/ws/{session_id}
```

**消息格式：**
```javascript
// 发送
{ "message": "创建一个 Python 项目" }

// 接收
{
  "type": "user_message",
  "content": "创建一个 Python 项目"
}

{
  "type": "thinking",
  "content": "正在思考..."
}

{
  "type": "response",
  "content": "项目创建完成...",
  "timestamp": "123456.789"
}

{
  "type": "stream_end"
}
```

### HTTP 接口

**端点：** `POST /api/chat`

**请求：**
```json
{
  "message": "创建一个 Python 项目",
  "session_id": "session_123"
}
```

**响应：**
```json
{
  "session_id": "session_123",
  "response": "项目创建完成...",
  "success": true
}
```

---

## 🔧 配置选项

### 启动参数

```bash
# 指定主机和端口
.venv/bin/python scripts/start_web.py --host 0.0.0.0 --port 9000

# 默认配置
# Host: 0.0.0.0 (所有网络接口)
# Port: 8080
```

### 环境变量

```bash
# 设置 Anthropic API Key
export ANTHROPIC_API_KEY=sk-ant-...

# 配置文件位置
export CCP_CONFIG=/path/to/config.yaml
```

---

## 📊 技术架构

```
┌─────────────┐
│   Browser   │
│   (HTML/JS) │
└──────┬──────┘
       │ WebSocket / HTTP
       ▼
┌─────────────────────────────┐
│      CCP Web Server         │
│  ┌───────────────────────┐  │
│  │  WebSocket Handler    │  │
│  │  HTTP Handler         │  │
│  └───────────────────────┘  │
│            │                │
│            ▼                │
│  ┌───────────────────────┐  │
│  │      Session Mgr      │  │
│  └───────────────────────┘  │
│            │                │
│            ▼                │
│  ┌───────────────────────┐  │
│  │      Agent Loop       │  │
│  └───────────────────────┘  │
│            │                │
│            ▼                │
│  ┌───────────────────────┐  │
│  │      Tool Registry    │  │
│  └───────────────────────┘  │
└─────────────────────────────┘
```

---

## 🧪 测试示例

### 使用 curl 测试 HTTP 接口

```bash
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello",
    "session_id": "test_session"
  }'
```

### 使用 wscat 测试 WebSocket

```bash
# 安装 wscat
npm install -g wscat

# 连接
wscat -c ws://localhost:8080/ws/test_session

# 发送消息
> {"message": "创建一个项目"}
```

---

## 🔐 安全考虑

### 当前状态

- ⚠️ **无身份验证** - 任何人都可以访问
- ⚠️ **无 CORS 限制** - 允许跨域请求
- ⚠️ **无速率限制** - 可能被滥用

### 建议改进

1. **添加身份验证**
   ```python
   # 简单的 Token 验证
   @web.middleware
   async def auth_middleware(request, handler):
       token = request.headers.get('Authorization')
       if token != 'Bearer secret-token':
           return web.HTTPUnauthorized()
       return await handler(request)
   ```

2. **启用 CORS**
   ```python
   from aiohttp_cors import setup, ResourceOptions
   
   cors = setup(app, defaults={
       "*": ResourceOptions(
           allow_credentials=True,
           expose_headers="*",
           allow_headers="*",
           allow_methods=["GET", "POST"]
       )
   })
   ```

3. **添加速率限制**
   ```python
   from aiohttp_limiter import RateLimiter
   
   limiter = RateLimiter(max_requests=100, period=60)
   app.middlewares.append(limiter.middleware)
   ```

---

## 🚀 部署建议

### 开发环境

```bash
# 本地运行
.venv/bin/python scripts/start_web.py
```

### 生产环境

**使用 Gunicorn：**

```bash
# 安装
pip install gunicorn

# 运行
gunicorn src.web_server:app \
  --bind 0.0.0.0:8080 \
  --workers 4 \
  --worker-class aiohttp.GunicornWebWorker
```

**使用 Docker：**

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -e .

EXPOSE 8080

CMD ["ccp-web", "--host", "0.0.0.0", "--port", "8080"]
```

**使用 Nginx 反向代理：**

```nginx
server {
    listen 80;
    server_name ccp.example.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## 📝 使用示例

### 示例 1: 创建项目

**用户输入：**
```
创建一个 Python CLI 项目，叫 my_cli
```

**预期响应：**
```
好的，我来创建一个 Python CLI 项目...

✅ 创建目录：my_cli
✅ 创建文件：my_cli/pyproject.toml
✅ 创建文件：my_cli/my_cli/cli.py
✅ 创建文件：my_cli/README.md

项目创建完成！

Next steps:
  cd my_cli
  pip install -e .
  my_cli --help
```

### 示例 2: 代码生成

**用户输入：**
```
写一个斐波那契函数
```

**预期响应：**
```
好的，这是一个斐波那契函数：

def fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number."""
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n-1) + fibonacci(n-2)

# 使用示例
for i in range(10):
    print(fibonacci(i))
# 输出：0, 1, 1, 2, 3, 5, 8, 13, 21, 34
```

### 示例 3: 项目分析

**用户输入：**
```
分析一下当前目录的项目架构
```

**预期响应：**
```
我来分析一下这个项目...

[调用工具：ls -la]
[调用工具：find . -name "*.py"]
[调用工具：cat pyproject.toml]

## 项目架构分析

### 项目类型
Python CLI 项目

### 目录结构
src/ - 源代码
tests/ - 测试
docs/ - 文档

### 技术栈
- Python 3.11+
- Click (CLI)
- Pytest (测试)

### 架构分层
CLI → Commands → Services → Core
```

---

## 🐛 故障排查

### 问题 1: 无法启动服务器

**错误：** `Address already in use`

**解决：**
```bash
# 查找占用端口的进程
lsof -i :8080

# 杀死进程
kill -9 <PID>

# 或使用不同端口
.venv/bin/python scripts/start_web.py --port 9000
```

### 问题 2: WebSocket 连接失败

**症状：** 浏览器显示 WebSocket 错误

**解决：**
1. 检查防火墙设置
2. 确认服务器正在运行
3. 检查浏览器控制台错误
4. 尝试使用 HTTP 降级模式

### 问题 3: API Key 错误

**错误：** `Invalid API key`

**解决：**
```bash
# 设置正确的 API Key
export ANTHROPIC_API_KEY=sk-ant-...

# 验证配置
.venv/bin/python -c "import os; print(os.environ.get('ANTHROPIC_API_KEY'))"
```

---

## 📊 性能优化

### 1. 启用压缩

```python
from aiohttp import web

app = web.Application(middlewares=[web.compress_middleware])
```

### 2. 连接池

```python
import aiohttp

connector = aiohttp.TCPConnector(limit=100, ttl_dns_cache=300)
session = aiohttp.ClientSession(connector=connector)
```

### 3. 缓存响应

```python
from aiohttp_cache import setup_cache

setup_cache(app, ttl=300)
```

---

## 🎯 下一步改进

- [ ] 添加 Markdown 渲染
- [ ] 支持代码高亮
- [ ] 添加文件上传功能
- [ ] 支持多会话管理
- [ ] 添加聊天记录导出
- [ ] 实现命令历史
- [ ] 添加快捷键支持
- [ ] 支持主题切换

---

*文档时间：2026-04-03*  
*作者：小佳 ✨*  
*状态：✅ 完成*
