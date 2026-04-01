# Stock-Agent Web 访问信息

**更新时间：** 2026-03-16 22:49

---

## 🌐 访问地址

### 公网访问
- **主页：** http://39.97.249.78:5000
- **API：** http://39.97.249.78:5000/api/v1

### 内网访问
- **主页：** http://172.25.10.209:5000
- **API：** http://172.25.10.209:5000/api/v1

---

## 📡 API 测试

```bash
# 测试首页
curl http://39.97.249.78:5000/

# 测试选股 API
curl http://39.97.249.78:5000/api/v1/stocks/recommend

# 测试监控 API
curl http://39.97.249.78:5000/api/v1/monitor/stocks

# 测试配置 API
curl http://39.97.249.78:5000/api/v1/config

# 获取持仓监控
curl http://39.97.249.78:5000/api/v1/monitor/stocks | jq
```

---

## 🔒 防火墙配置

### 检查防火墙状态
```bash
sudo firewall-cmd --list-all
```

### 开放 5000 端口
```bash
# 添加规则
sudo firewall-cmd --permanent --add-port=5000/tcp

# 重新加载
sudo firewall-cmd --reload

# 验证
sudo firewall-cmd --list-ports
```

### 或使用 iptables
```bash
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
sudo service iptables save
```

---

## 🔐 安全建议

### 当前状态
- ⚠️ Debug 模式：开启
- ⚠️ 认证：无
- ⚠️ HTTPS：未配置

### 建议配置

1. **关闭 Debug 模式**
   ```bash
   # 编辑 app.py
   app = create_app('production')
   ```

2. **添加基础认证**
   ```python
   from flask_httpauth import HTTPBasicAuth
   
   @app.before_request
   def check_auth():
       # 验证逻辑
   ```

3. **配置 Nginx 反向代理**
   ```nginx
   server {
       listen 80;
       server_name 39.97.249.78;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
       }
   }
   ```

4. **限制访问 IP（可选）**
   ```bash
   # 只允许特定 IP 访问
   sudo iptables -A INPUT -p tcp --dport 5000 -s 你的 IP -j ACCEPT
   sudo iptables -A INPUT -p tcp --dport 5000 -j DROP
   ```

---

## 📱 手机访问

在浏览器输入：`http://39.97.249.78:5000`

---

## 📊 服务状态

```bash
# 查看进程
ps aux | grep "python3 app.py"

# 查看端口
netstat -tlnp | grep 5000

# 查看日志
tail -f /home/admin/.openclaw/workspace/stock-agent-web/logs/web.log

# 重启服务
pkill -f "python3 app.py"
cd /home/admin/.openclaw/workspace/stock-agent-web
nohup python3 app.py > logs/web.log 2>&1 &
```

---

## 🛑 停止服务

```bash
# 停止
pkill -f "python3 app.py"

# 验证
ps aux | grep "python3 app.py" | grep -v grep
```

---

*最后更新：2026-03-16 22:49*
