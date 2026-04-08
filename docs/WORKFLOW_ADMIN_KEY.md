# 工作流启动密钥配置指南

> 📅 创建时间：2026-04-08  
> 🔐 功能版本：v1.0.1+

---

## 🎯 功能说明

从 **v1.0.1** 开始，Learning Agent 支持为**知识生成工作流**设置启动密钥，防止未授权用户消耗 API 额度。

**适用场景：**
- ✅ Web 页面对外公开时
- ✅ 多人共享环境时
- ✅ 防止恶意调用时

---

## 🔧 配置步骤

### 1. 生成安全密钥

使用以下命令生成一个随机密钥：

```bash
# 方法 1：使用 openssl（推荐）
openssl rand -hex 16

# 方法 2：使用 Python
python3 -c "import secrets; print(secrets.token_hex(16))"

# 方法 3：使用 /dev/urandom
head -c 32 /dev/urandom | base64
```

**示例输出：**
```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

---

### 2. 配置环境变量

编辑 `.env` 文件：

```bash
cd /home/admin/.openclaw/workspace/learning-agent
nano .env
```

添加或修改以下配置：

```bash
# 工作流启动密钥（对外公开时保护知识生成功能）
WEB_ADMIN_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

> ⚠️ **重要提示：**
> - 密钥长度建议至少 32 字符（16 字节 hex）
> - 不要使用示例密钥，务必生成自己的随机密钥
> - 密钥丢失后无法恢复，需要重新配置

---

### 3. 重启 Web 服务

```bash
# 如果使用 systemd 服务
sudo systemctl restart learning-agent

# 如果手动运行
cd web
python3 app.py --host 0.0.0.0 --port 5001
```

---

## 📝 使用方法

### Web 界面

1. 访问 `http://your-server:5001`
2. 点击左侧边栏的 **"🚀 生成知识"** 按钮
3. 在弹窗中输入管理员密钥
4. 勾选确认框
5. 点击 **"确认启动"**

### API 调用

```bash
curl -X POST http://localhost:5001/api/workflow/run/start \
  -H "Content-Type: application/json" \
  -d '{
    "layers": [1, 2, 3, 4, 5],
    "regenerate": true,
    "admin_key": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
  }'
```

**成功响应：**
```json
{
  "success": true,
  "message": "工作流已启动",
  "data": {
    "pid": 12345,
    "log_file": "/path/to/logs/workflow.log",
    "estimated_time": "45-60 分钟",
    "estimated_calls": "100-150 次 API 调用"
  }
}
```

**密钥错误响应：**
```json
{
  "success": false,
  "error": "密钥验证失败",
  "detail": "管理员密钥错误，无权执行此操作"
}
```

---

## 🔒 安全特性

### 后端验证

- ✅ 使用 `hmac.compare_digest()` 进行常量时间比较，防止时序攻击
- ✅ 密钥错误返回 HTTP 403 Forbidden
- ✅ 验证失败记录日志（包含 IP 地址）

### 前端体验

- ✅ 密钥输入框实时格式验证
- ✅ 密钥长度至少 8 位
- ✅ 验证通过显示绿色提示
- ✅ 密钥错误显示红色提示

### 兼容模式

如果未配置 `WEB_ADMIN_KEY`，系统会：
- ⚠️ 记录警告日志
- ✅ 允许启动工作流（兼容旧版本）

---

## 📊 日志示例

### 密钥验证成功
```
2026-04-08 08:30:15 - [INFO] - workflow_run_routes - ✅ 密钥验证通过：IP=192.168.1.100
```

### 密钥验证失败
```
2026-04-08 08:31:22 - [WARNING] - workflow_run_routes - ❌ 密钥验证失败：IP=10.0.0.50
```

### 未配置密钥
```
2026-04-08 08:32:05 - [WARNING] - workflow_run_routes - WEB_ADMIN_KEY 未配置，跳过密钥验证
```

---

## ❓ 常见问题

### Q1: 忘记密钥怎么办？

**A:** 直接修改 `.env` 文件中的 `WEB_ADMIN_KEY`，然后重启服务即可。

```bash
nano .env
# 修改 WEB_ADMIN_KEY=新密钥
sudo systemctl restart learning-agent
```

### Q2: 可以临时禁用密钥验证吗？

**A:** 可以，注释掉 `.env` 中的 `WEB_ADMIN_KEY` 配置：

```bash
# WEB_ADMIN_KEY=old_key
```

然后重启服务。

### Q3: 密钥验证会影响其他功能吗？

**A:** 不会，只影响 **"生成知识"** 按钮对应的工作流启动功能。其他功能（聊天、查看知识等）不受影响。

### Q4: 可以设置多个密钥吗？

**A:** 当前版本只支持单个密钥。如需多用户管理，建议：
- 使用反向代理（Nginx）做 HTTP Basic Auth
- 或使用 `LEARNING_AGENT_TOKEN` 做 API 级认证

---

## 🔗 相关文件

| 文件 | 说明 |
|------|------|
| `.env.example` | 环境变量示例（包含 WEB_ADMIN_KEY 说明） |
| `web/routes/workflow_run_routes.py` | 后端验证逻辑 |
| `web/templates/workflow.html` | 前端密钥输入界面 |

---

## 📋 更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.1 | 2026-04-08 | 初始版本，添加工作流启动密钥验证 |

---

**🔐 安全第一，保护你的 API 额度！**
