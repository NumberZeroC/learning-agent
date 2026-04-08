# 🔐 .env 文件中的两个密钥区别

**文件位置：** `/home/admin/.openclaw/workspace/learning-agent/.env`

---

## 📋 两个密钥

```bash
# 密钥 1：阿里云 API Key
DASHSCOPE_API_KEY=sk-sp-1103f012953e45d984ab8fbd486e6e16

# 密钥 2：本地加密主密钥
LEARNING_AGENT_MASTER_KEY=7P04PX1T1j6bLTE6cIPenkjSORb9e5kLuyGrEoRr-z0=
```

---

## 🔑 密钥 1：DASHSCOPE_API_KEY（阿里云 API Key）

### 用途
- **作用：** 调用阿里云 DashScope API 的凭证
- **类型：** 第三方服务 API Key
- **来源：** 阿里云控制台申请
- **格式：** `sk-sp-` 开头

### 功能
```
用于访问：
- 通义千问（Qwen）大模型
- 阿里云 DashScope 服务
- AI 对话、文本生成等能力
```

### 安全性
- ⚠️ **敏感级别：高**
- ⚠️ **泄露风险：** 他人可盗用你的 API 额度
- ⚠️ **存储方式：** 明文（已废弃，建议删除）

### 获取方式
1. 访问阿里云官网：https://www.aliyun.com/
2. 注册/登录账号
3. 开通 DashScope 服务
4. 创建 API Key
5. 复制 Key 到配置文件

### 当前状态
```
⚠️ 已废弃（向后兼容）
✅ 实际使用：KeyVault 加密存储（data/secrets.db）
⚠️ .env 中的明文 Key 建议删除
```

---

## 🔑 密钥 2：LEARNING_AGENT_MASTER_KEY（本地加密主密钥）

### 用途
- **作用：** 加密存储本地敏感数据（如 API Key）
- **类型：** 本地加密密钥（Fernet Key）
- **来源：** 系统自动生成
- **格式：** Base64 编码的 32 字节随机数

### 功能
```
用于加密：
- API Key（如 DASHSCOPE_API_KEY）
- 其他敏感配置
- 存储在 data/secrets.db 中
```

### 加密原理
```python
from cryptography.fernet import Fernet

# 生成主密钥
master_key = Fernet.generate_key()  # 例如：7P04PX1T1j6bLTE6cIPenkjSORb9e5kLuyGrEoRr-z0=

# 使用主密钥加密 API Key
fernet = Fernet(master_key.encode())
encrypted_api_key = fernet.encrypt(b'sk-sp-1103f012953e45d984ab8fbd486e6e16')

# 加密后的数据存储在 data/secrets.db
```

### 安全性
- 🔒 **敏感级别：极高**
- 🔒 **泄露风险：** 他人可解密你的所有加密数据
- 🔒 **存储方式：** 仅存储在 .env（不上传 Git）
- 🔒 **丢失后果：** 无法解密已加密的 API Key，需重新配置

### 获取方式
```bash
# 自动生成（首次运行时）
python3 scripts/migrate_keys.py --generate-key

# 或手动生成
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 当前状态
```
✅ 必需配置
✅ 系统自动生成一次
✅ 永久保存，不要丢失
```

---

## 📊 对比表格

| 特性 | DASHSCOPE_API_KEY | LEARNING_AGENT_MASTER_KEY |
|------|-------------------|---------------------------|
| **用途** | 调用阿里云 API | 加密本地数据 |
| **类型** | 第三方 API Key | 本地加密密钥 |
| **来源** | 阿里云控制台 | 系统自动生成 |
| **格式** | `sk-sp-xxx` | Base64 编码（44 字符） |
| **敏感性** | 高 | 极高 |
| **泄露风险** | 盗用 API 额度 | 解密所有敏感数据 |
| **丢失后果** | 重新申请即可 | 所有加密数据无法读取 |
| **更换频率** | 可随时更换 | 永久不变（除非重新初始化） |
| **当前状态** | ⚠️ 已废弃（向后兼容） | ✅ 必需 |
| **建议操作** | 删除（已从 KeyVault 存储） | 妥善保管，不要泄露 |

---

## 🎯 关系说明

```
┌─────────────────────────────────────────────────────────┐
│  用户输入 API Key（Web 页面）                            │
│  sk-sp-1103f012953e45d984ab8fbd486e6e16                 │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  LEARNING_AGENT_MASTER_KEY（加密密钥）                   │
│  7P04PX1T1j6bLTE6cIPenkjSORb9e5kLuyGrEoRr-z0=           │
│                                                          │
│  使用 Fernet 算法加密：                                   │
│  encrypted = fernet.encrypt(api_key)                    │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  data/secrets.db（加密存储）                             │
│  存储加密后的 API Key                                    │
│  （即使数据库泄露，没有主密钥也无法解密）                 │
└─────────────────────────────────────────────────────────┘
```

---

## 🔒 安全建议

### DASHSCOPE_API_KEY（阿里云 API Key）

**✅ 正确做法：**
1. 通过 Web 页面配置（`http://localhost:5001/config`）
2. 自动加密存储到 `data/secrets.db`
3. 从 `.env` 文件删除明文 Key

**❌ 错误做法：**
1. 直接写在代码中
2. 提交到 Git 仓库
3. 在配置文件明文存储

**删除命令：**
```bash
# 编辑 .env 文件
vim .env

# 删除这行：
DASHSCOPE_API_KEY=sk-sp-1103f012953e45d984ab8fbd486e6e16

# 保留这行：
LEARNING_AGENT_MASTER_KEY=7P04PX1T1j6bLTE6cIPenkjSORb9e5kLuyGrEoRr-z0=
```

---

### LEARNING_AGENT_MASTER_KEY（本地加密主密钥）

**✅ 正确做法：**
1. 系统自动生成一次
2. 永久保存，不要丢失
3. 备份到安全位置
4. 不上传 Git

**❌ 错误做法：**
1. 随意更改（会导致无法解密）
2. 泄露给他人
3. 上传到公开仓库

**备份命令：**
```bash
# 备份 .env 文件到安全位置
cp .env /secure/location/learning-agent.env.backup

# 或仅备份主密钥
grep LEARNING_AGENT_MASTER_KEY .env >> ~/passwords.txt
```

---

## 🆘 常见问题

### Q1: 我可以删除 DASHSCOPE_API_KEY 吗？

**A:** ✅ 可以且建议删除！

现在系统从 KeyVault 获取 API Key（加密存储在 `data/secrets.db`），`.env` 中的明文 Key 仅用于向后兼容。

**删除步骤：**
```bash
# 1. 编辑 .env 文件
vim .env

# 2. 删除 DASHSCOPE_API_KEY 行
# 保留 LEARNING_AGENT_MASTER_KEY

# 3. 重启服务
sudo systemctl restart learning-agent
```

---

### Q2: LEARNING_AGENT_MASTER_KEY 丢失了怎么办？

**A:** ⚠️ 严重后果！

**后果：**
- 无法解密 `data/secrets.db` 中的 API Key
- 需要重新配置所有 API Key
- 历史审计日志无法关联

**恢复方法：**
1. 从备份恢复 `.env` 文件
2. 或重新生成主密钥，然后重新配置所有 API Key

**预防：**
```bash
# 立即备份
cp .env /secure/location/learning-agent.env.backup
```

---

### Q3: 两个 Key 都可以泄露吗？

**A:** ❌ 都不可以！

**泄露风险：**
| Key | 泄露后果 | 紧急程度 |
|-----|---------|---------|
| DASHSCOPE_API_KEY | 他人盗用 API 额度 | 🔴 高 |
| LEARNING_AGENT_MASTER_KEY | 解密所有敏感数据 | 🔴 极高 |

**泄露应对：**
1. **DASHSCOPE_API_KEY 泄露：**
   - 立即在阿里云控制台撤销
   - 重新生成新 Key
   - 通过 Web 页面更新配置

2. **LEARNING_AGENT_MASTER_KEY 泄露：**
   - 立即生成新的主密钥
   - 重新配置所有 API Key
   - 删除旧的 `data/secrets.db`

---

## 📝 总结

| Key | 作用 | 建议 |
|-----|------|------|
| **DASHSCOPE_API_KEY** | 调用阿里云 API | ⚠️ 从 .env 删除，使用 KeyVault |
| **LEARNING_AGENT_MASTER_KEY** | 加密本地数据 | 🔒 永久保存，不要丢失 |

**一句话：**
- `DASHSCOPE_API_KEY` = 保险箱里的钱（可以更换）
- `LEARNING_AGENT_MASTER_KEY` = 保险箱钥匙（不能丢失）

---

_文档更新时间：2026-04-06 11:37_  
_版本：v1.0_
