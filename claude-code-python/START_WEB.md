# 🌐 启动 CCP Web 界面

## 🚀 快速启动

### 1. 安装依赖

```bash
cd /home/admin/.openclaw/workspace/claude-code-python
pip3 install aiohttp
```

### 2. 启动服务器

```bash
# 设置 API Key
export ANTHROPIC_API_KEY=sk-ant-your-key-here

# 启动 Web 服务器
python3 src/web_server.py --host 0.0.0.0 --port 8080
```

### 3. 访问界面

打开浏览器访问：**http://localhost:8080**

---

## 📝 功能特性

✅ **现代化 UI** - 渐变设计，响应式布局  
✅ **实时聊天** - WebSocket 双向通信  
✅ **流式响应** - 思考中状态，实时反馈  
✅ **会话管理** - 自动创建会话 ID  
✅ **错误处理** - 友好的错误提示  
✅ **降级支持** - WebSocket 不可用时自动切换 HTTP  

---

## 💻 使用示例

### 聊天界面
1. 打开浏览器访问 http://localhost:8080
2. 在输入框输入消息，如："创建一个 Python 项目"
3. 点击"发送"或按回车
4. 等待 AI 响应（会显示"正在思考..."）
5. 查看响应结果

### 支持的功能
- 创建项目
- 代码生成
- 文件操作
- 项目分析
- 问题解答

---

## 🔧 配置选项

```bash
# 自定义端口
python3 src/web_server.py --port 9000

# 指定主机（默认所有网络接口）
python3 src/web_server.py --host 127.0.0.1

# 同时指定主机和端口
python3 src/web_server.py --host 0.0.0.0 --port 8080
```

---

## 📊 技术架构

```
浏览器 (HTML/JS/CSS)
    ↓ WebSocket / HTTP
CCP Web Server (aiohttp)
    ↓
Session 管理
    ↓
Agent Loop (AI 核心)
    ↓
工具注册表
    ↓
LLM (Anthropic API)
```

---

## 🐛 故障排查

### 问题：端口被占用
```bash
# 查看占用端口的进程
lsof -i :8080

# 使用其他端口
python3 src/web_server.py --port 9000
```

### 问题：API Key 错误
```bash
# 确保设置了正确的 API Key
export ANTHROPIC_API_KEY=sk-ant-...
```

### 问题：无法访问
```bash
# 检查防火墙
# 确保服务器正在运行
# 检查浏览器控制台错误
```

---

## 📝 文件说明

- `src/web_server.py` - Web 服务器主程序
- `scripts/start_web.py` - 启动脚本
- `WEB_SERVER_GUIDE.md` - 详细使用指南

---

*创建时间：2026-04-03*
