# 🔐 Web 前端 API Key 安全配置方案

## 问题分析

当前问题：
1. ❌ API Key 明文存储在 `config/agent_config.yaml`
2. ❌ Web 前端可直接读取完整 API Key
3. ❌ 配置页面可能泄露敏感信息
4. ❌ 无加密、无审计、无访问控制

---

## 🏗️ 设计方案

### 核心原则

1. **前端永不接触明文 API Key**
2. **加密存储，按需解密**
3. **最小权限，按需访问**
4. **完整审计，可追溯**

---

## 📐 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web 前端                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ 配置页面     │  │ 聊天页面     │  │ 管理页面     │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         ▼                ▼                ▼                      │
│  ┌─────────────────────────────────────────────────┐            │
│  │           API Gateway (Flask Routes)             │            │
│  └─────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        后端服务                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ ConfigMgr   │  │ KeyVault    │  │ AuditLog    │              │
│  │ 配置管理器   │  │ 密钥保险箱   │  │ 审计日志     │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         ▼                ▼                ▼                      │
│  ┌─────────────────────────────────────────────────┐            │
│  │           Encryption Service (Fernet)            │            │
│  └─────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        持久化层                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ config.yaml │  │ secrets.db  │  │ audit.log   │              │
│  │ (不含 Key)  │  │ (加密存储)   │  │ (审计日志)   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔑 核心组件

### 1. KeyVault（密钥保险箱）

**职责：**
- 加密/解密 API Key
- 密钥轮换
- 访问控制

**存储方式：**
```python
# 加密密钥（Fernet 对称加密）
# 主密钥存储在环境变量，不落地
MASTER_KEY = os.getenv('LEARNING_AGENT_MASTER_KEY')

# 加密后的 API Key 存储到 SQLite
# 格式：fernet.encrypt(api_key.encode())
```

**数据库表设计：**
```sql
CREATE TABLE api_secrets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider VARCHAR(50) NOT NULL UNIQUE,  -- 'dashscope', 'openai', etc.
    encrypted_key BLOB NOT NULL,           -- 加密后的 Key
    key_prefix VARCHAR(20),                -- Key 前缀（用于显示，如 sk-sp11***）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

CREATE INDEX idx_provider ON api_secrets(provider);
```

---

### 2. ConfigManager（配置管理器）

**职责：**
- 管理 `agent_config.yaml`
- 验证配置完整性
- 触发配置热更新

**配置结构：**
```yaml
# config/agent_config.yaml
providers:
  dashscope:
    enabled: true
    base_url: https://coding.dashscope.aliyuncs.com/v1
    model: qwen3.5-plus
    # ❌ 不再存储 api_key_value
    # ✅ Key 存储在 secrets.db（加密）

agents:
  master_agent:
    provider: dashscope
    model: qwen3.5-plus
    # ... 其他配置
```

---

### 3. AuditLogger（审计日志）

**职责：**
- 记录所有 Key 相关操作
- 记录配置变更
- 异常行为检测

**日志格式：**
```json
{
  "timestamp": "2026-04-06T08:00:00Z",
  "action": "key_update",
  "provider": "dashscope",
  "user_ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "result": "success",
  "details": {
    "key_prefix": "sk-sp11***",
    "old_prefix": "sk-sp11***"
  }
}
```

---

## 🔒 加密方案

### Fernet 对称加密

```python
from cryptography.fernet import Fernet
import base64
import os

class KeyVault:
    def __init__(self):
        # 从环境变量获取主密钥（32 字节 base64 编码）
        master_key = os.getenv('LEARNING_AGENT_MASTER_KEY')
        if not master_key:
            # 首次运行时生成并提示用户保存
            master_key = Fernet.generate_key().decode()
            print(f"⚠️  请保存主密钥（仅需保存一次）：")
            print(f"LEARNING_AGENT_MASTER_KEY={master_key}")
            raise RuntimeError("Master key not configured")
        
        self.fernet = Fernet(master_key.encode())
    
    def encrypt(self, api_key: str) -> bytes:
        """加密 API Key"""
        return self.fernet.encrypt(api_key.encode())
    
    def decrypt(self, encrypted_key: bytes) -> str:
        """解密 API Key"""
        return self.fernet.decrypt(encrypted_key).decode()
    
    def get_key_prefix(self, api_key: str) -> str:
        """生成 Key 前缀用于显示（如 sk-sp11***3434）"""
        if len(api_key) < 16:
            return "***"
        return f"{api_key[:8]}***{api_key[-4:]}"
```

---

## 🌐 Web API 设计

### 配置页面 API

```python
# GET /api/config/providers - 获取 provider 配置（不含 Key）
{
  "dashscope": {
    "enabled": true,
    "base_url": "https://coding.dashscope.aliyuncs.com/v1",
    "model": "qwen3.5-plus",
    "key_configured": true,        # 是否已配置 Key
    "key_prefix": "sk-sp11***3434"  # Key 前缀（用于显示）
  }
}

# POST /api/config/providers/dashscope/key - 更新 API Key
# Request:
{
  "api_key": "sk-sp-完整 key"  # 前端传入明文
}
# Response:
{
  "success": true,
  "key_prefix": "sk-sp11***3434"
}

# DELETE /api/config/providers/dashscope/key - 删除 API Key
# Response:
{
  "success": true
}

# GET /api/config/audit-log - 获取审计日志（管理员）
# Response:
{
  "logs": [...],
  "total": 100
}
```

---

## 🎨 前端 UI 设计

### 配置页面

```html
<!-- Provider 配置卡片 -->
<div class="provider-card">
  <h3>阿里云 DashScope</h3>
  
  <!-- 已配置状态 -->
  <div class="status configured">
    <span class="icon">✅</span>
    <span class="key-display">sk-sp11***3434</span>
    <span class="last-updated">更新于：2026-04-06 08:00</span>
  </div>
  
  <!-- 操作按钮 -->
  <div class="actions">
    <button onclick="editKey()">✏️ 修改</button>
    <button onclick="testConnection()">🧪 测试连接</button>
    <button onclick="deleteKey()" class="danger">🗑️ 删除</button>
  </div>
  
  <!-- 编辑表单（点击修改后显示） -->
  <div class="edit-form" style="display:none">
    <input type="password" placeholder="请输入 API Key (sk-开头)" />
    <button onclick="saveKey()">💾 保存</button>
    <button onclick="cancelEdit()">取消</button>
  </div>
</div>

<!-- 未配置状态 -->
<div class="status not-configured">
  <span class="icon">❌</span>
  <span>未配置 API Key</span>
  <button onclick="addKey()">➕ 添加</button>
</div>
```

---

## 📁 文件结构

```
learning-agent/
├── config/
│   ├── agent_config.yaml       # 不含 Key
│   └── config_validator.py     # 配置验证
├── data/
│   └── secrets.db              # 加密存储 API Key（新增）
├── logs/
│   └── config_audit.log        # 审计日志（新增）
├── services/
│   ├── key_vault.py            # 密钥保险箱（新增）
│   └── config_manager.py       # 配置管理器（新增）
├── web/
│   ├── routes/
│   │   └── config_routes.py    # 更新：移除 Key 读取
│   └── templates/
│       └── config.html         # 更新：新 UI
└── utils/
    └── audit_logger.py         # 审计日志（新增）
```

---

## 🔐 安全加固

### 1. 访问控制

```python
# 配置管理需要管理员权限
@app.route('/api/config/providers/<provider>/key', methods=['POST'])
@require_admin  # 装饰器验证管理员权限
def update_api_key(provider):
    # ...
```

### 2. 速率限制

```python
# 防止暴力破解
from flask_limiter import Limiter

limiter = Limiter(app, key_func=get_remote_address)

@app.route('/api/config/providers/<provider>/key', methods=['POST'])
@limiter.limit("5 per minute")  # 每分钟最多 5 次
def update_api_key(provider):
    # ...
```

### 3. IP 白名单（可选）

```yaml
# config/agent_config.yaml
security:
  admin_ips:
    - 127.0.0.1
    - 192.168.1.0/24
  config_whitelist: true  # 仅允许白名单 IP 修改配置
```

---

## 🚀 部署步骤

### 1. 首次部署

```bash
# 1. 生成主密钥
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 2. 保存到环境变量
echo "LEARNING_AGENT_MASTER_KEY=生成的密钥" >> .env

# 3. 初始化数据库
python3 -c "from models.database import initialize; initialize()"
python3 -c "from services.key_vault import init_secrets_db; init_secrets_db()"

# 4. 重启服务
sudo systemctl restart learning-agent
```

### 2. 配置 Key

```bash
# 通过 Web 页面配置（推荐）
# 或命令行：
python3 -c "from services.key_vault import KeyVault; kv = KeyVault(); kv.save_key('dashscope', 'sk-sp-...')"
```

---

## 📊 迁移方案

### 从旧配置迁移

```python
# migrate_keys.py
import yaml
from services.key_vault import KeyVault

# 1. 读取旧配置
with open('config/agent_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# 2. 提取旧 Key
old_key = config['providers']['dashscope'].get('api_key_value')

# 3. 加密存储到新位置
if old_key:
    vault = KeyVault()
    vault.save_key('dashscope', old_key)
    
    # 4. 从配置文件移除
    del config['providers']['dashscope']['api_key_value']
    with open('config/agent_config.yaml', 'w') as f:
        yaml.dump(config, f)
    
    print("✅ 迁移完成")
```

---

## ✅ 验收标准

- [ ] API Key 不再出现在 `agent_config.yaml`
- [ ] Key 在数据库中加密存储
- [ ] 前端只能看到 Key 前缀（如 sk-sp11***）
- [ ] 所有 Key 操作都有审计日志
- [ ] 配置页面有访问控制
- [ ] 支持 Key 热更新（无需重启）
- [ ] 旧配置可平滑迁移

---

## 📝 待办事项

1. [ ] 实现 `KeyVault` 服务
2. [ ] 创建 `secrets.db` 数据库表
3. [ ] 更新 `config_routes.py` API
4. [ ] 更新前端配置页面 UI
5. [ ] 实现 `AuditLogger`
6. [ ] 添加访问控制装饰器
7. [ ] 编写迁移脚本
8. [ ] 更新文档

---

_设计时间：2026-04-06_
_版本：v1.0_
