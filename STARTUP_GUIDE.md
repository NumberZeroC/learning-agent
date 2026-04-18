# 🚀 Learning Agent 启动指南

## 📋 快速启动

### 方式一：使用启动脚本（推荐）

```bash
cd /home/admin/.openclaw/workspace/learning-agent

# 前台启动
./start.sh

# 后台启动
./start.sh -d

# 查看状态
./start.sh -s

# 停止服务
./start.sh -k

# 重启服务
./start.sh -r
```

### 方式二：手动启动

```bash
cd /home/admin/.openclaw/workspace/learning-agent

# 1. 激活虚拟环境
source venv/bin/activate

# 2. 启动服务
python3 web/app.py --host 0.0.0.0 --port 5001
```

### 方式三：Docker 运行

```bash
cd /opt/learning-agent

# 启动
docker compose up -d

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f

# 停止
docker compose down
```

---

## 🔧 start.sh 脚本选项

| 选项 | 说明 | 示例 |
|------|------|------|
| `-d, --daemon` | 后台运行 | `./start.sh -d` |
| `-f, --foreground` | 前台运行（默认） | `./start.sh -f` |
| `-p, --port PORT` | 指定端口 | `./start.sh -p 8080` |
| `-h, --host HOST` | 指定主机 | `./start.sh -h 127.0.0.1` |
| `-c, --check` | 只检查环境 | `./start.sh -c` |
| `-s, --status` | 查看运行状态 | `./start.sh -s` |
| `-k, --kill` | 停止服务 | `./start.sh -k` |
| `-r, --restart` | 重启服务 | `./start.sh -r` |
| `--help` | 显示帮助 | `./start.sh --help` |

---

## 📝 使用示例

### 1. 检查环境

```bash
./start.sh -c
```

输出：
```
[INFO] 检查运行环境...
[SUCCESS] Python3: Python 3.6.8
[SUCCESS] 虚拟环境：venv/
[SUCCESS] 依赖检查通过
[SUCCESS] API Key: 已配置
[SUCCESS] 环境检查完成
```

### 2. 后台启动

```bash
./start.sh -d
```

输出：
```
[SUCCESS] 服务已启动 (后台模式)

PID: 12345
端口：5001
日志：logs/web.log

访问地址:
  - 本地：http://localhost:5001
  - 远程：http://172.25.10.209:5001

查看日志：tail -f logs/web.log
停止服务：./start.sh -k
```

### 3. 自定义端口

```bash
./start.sh -p 8080
```

### 4. 查看状态

```bash
./start.sh -s
```

输出：
```
[INFO] 检查服务状态...
[SUCCESS] 服务运行中 (PID: 12345, 端口：5001)

访问地址:
  - 本地：http://localhost:5001
  - 远程：http://172.25.10.209:5001

日志文件：logs/web.log
停止服务：./start.sh -k
```

### 5. 重启服务

```bash
./start.sh -r
```

---

## 🌐 访问地址

启动后可以通过以下地址访问：

- **本地访问**: http://localhost:5001
- **远程访问**: http://<服务器IP>:5001
- **Docker 网络**: http://learning-agent:5001

---

## 📁 目录结构

```
learning-agent/
├── start.sh              # 启动脚本
├── web/
│   └── app.py           # Web 应用入口
├── venv/                # Python 虚拟环境
├── logs/                # 日志目录
│   └── web.log         # Web 日志
├── data/                # 数据目录
├── config/              # 配置目录
└── .pid                # PID 文件（后台运行时）
```

---

## 🔍 故障排除

### 端口被占用

```bash
# 查看占用端口的进程
lsof -i :5001

# 停止旧进程
./start.sh -k

# 或使用自定义端口
./start.sh -p 8080
```

### 虚拟环境问题

```bash
# 重新创建虚拟环境
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 查看日志

```bash
# 实时查看日志
tail -f logs/web.log

# 查看最近 100 行
tail -100 logs/web.log

# 搜索错误
grep -i "error" logs/web.log
```

### API Key 未配置

```bash
# 临时配置
export DASHSCOPE_API_KEY=sk-xxx
./start.sh

# 永久配置
echo "DASHSCOPE_API_KEY=sk-xxx" >> .env
./start.sh
```

---

## 📊 运行模式对比

| 模式 | 命令 | 适用场景 |
|------|------|---------|
| **前台** | `./start.sh` | 开发调试 |
| **后台** | `./start.sh -d` | 生产部署 |
| **Docker** | `docker compose up -d` | 容器化部署 |

---

## 🎯 完整工作流程

```bash
# 1. 检查环境
./start.sh -c

# 2. 启动服务
./start.sh -d

# 3. 查看状态
./start.sh -s

# 4. 访问服务
curl http://localhost:5001/health

# 5. 查看日志
tail -f logs/web.log

# 6. 停止服务（需要时）
./start.sh -k
```

---

## 📞 支持

遇到问题请查看：
- 日志文件：`logs/web.log`
- 项目文档：`README.md`
- 配置文件：`config/agent_config.yaml`
