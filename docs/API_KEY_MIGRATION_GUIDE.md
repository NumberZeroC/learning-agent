# 🔐 API Key 安全迁移指南

## 概述

本次迁移将 API Key 从明文配置文件迁移到加密存储（KeyVault），提升安全性。

---

## 📋 迁移前检查

### 1. 检查当前状态

```bash
cd /home/admin/.openclaw/workspace/learning-agent

# 检查配置文件是否包含明文 Key
grep "api_key_value" config/agent_config.yaml

# 检查是否已安装 cryptography
python3 -c "from cryptography.fernet import Fernet; print('✅ cryptography 已安装')"
```

### 2. 备份

```bash
# 备份配置文件
cp config/agent_config.yaml config/agent_config.yaml.bak

# 备份数据库
cp data/learning_agent.db data/learning_agent.db.bak

# 备份 .env 文件
cp .env .env.bak
```

---

## 🚀 迁移步骤

### 步骤 1：安装依赖

```bash
cd /home/admin/.openclaw/workspace/learning-agent
source venv/bin/activate
pip install cryptography
```

### 步骤 2：生成主密钥

```bash
# 生成主密钥
python3 scripts/migrate_keys.py --generate-key

# 保存到 .env 文件
echo "LEARNING_AGENT_MASTER_KEY=生成的密钥" >> .env

# 验证
grep LEARNING_AGENT_MASTER_KEY .env
```

### 步骤 3：执行迁移

```bash
# 运行迁移脚本
python3 scripts/migrate_keys.py
```

**输出示例：**
```
🔐 API Key 迁移工具
============================================================
📄 配置文件：/home/admin/.openclaw/workspace/learning-agent/config/agent_config.yaml

🔑 初始化 KeyVault...
✅ KeyVault 已初始化

🔄 开始迁移 API Key...

  📌 dashscope:
     当前 Key 前缀：sk-sp-1103...
     ✅ 已迁移到 KeyVault (前缀：sk-sp11***6e16)

🧹 清理配置文件中的明文 Key...
     ✅ 已移除 dashscope 的明文 Key

✅ 配置文件已更新

============================================================
📊 迁移总结:
   成功迁移：1 个 Provider
   Provider 列表：dashscope

⚠️  重要提示:
   1. 请重启服务使更改生效：sudo systemctl restart learning-agent
   2. 请备份主密钥（如果尚未保存）
   3. 建议检查审计日志：tail -f logs/config_audit.log

✅ 迁移完成！
```

### 步骤 4：验证迁移

```bash
# 检查配置文件（应该没有 api_key_value）
grep "api_key_value" config/agent_config.yaml
# 应该无输出

# 检查数据库（secrets.db 应该已创建）
ls -la data/secrets.db

# 测试服务
python3 -c "from services.key_vault import get_key_vault; vault = get_key_vault(); print('Key configured:', vault.is_key_configured('dashscope'))"
```

### 步骤 5：重启服务

```bash
# 重启 systemd 服务
sudo systemctl restart learning-agent

# 检查状态
sudo systemctl status learning-agent

# 查看日志
sudo journalctl -u learning-agent -f
```

---

## 🧪 测试

### 1. 测试 Web 配置页面

访问：`http://localhost:5001/config`

**预期结果：**
- ✅ 显示 "已配置 API Key"
- ✅ 显示 Key 前缀（如 `sk-sp11***6e16`）
- ✅ 不显示完整 Key

### 2. 测试 API

```bash
# 获取 Provider 配置（应该没有明文 Key）
curl http://localhost:5001/api/config/providers | jq

# 测试连接
curl -X POST http://localhost:5001/api/config/providers/dashscope/test | jq
```

### 3. 测试聊天功能

```bash
# 发送测试消息
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好", "agent_name": "master_agent"}' | jq
```

---

## 🔍 故障排查

### 问题 1：KeyVault 初始化失败

**错误信息：**
```
KeyVaultError: 主密钥无效
```

**解决方案：**
```bash
# 检查 .env 文件
cat .env | grep LEARNING_AGENT_MASTER_KEY

# 如果为空或格式错误，重新生成
python3 scripts/migrate_keys.py --generate-key
# 更新 .env 文件
```

### 问题 2：API Key 无法解密

**错误信息：**
```
cryptography.fernet.InvalidToken
```

**原因：** 主密钥已更改，但数据是用旧密钥加密的

**解决方案：**
```bash
# 1. 恢复旧的主密钥（如果有备份）
# 2. 或者重新配置所有 API Key（通过 Web 页面）
```

### 问题 3：服务启动失败

**检查日志：**
```bash
sudo journalctl -u learning-agent -n 50 --no-pager
```

**常见问题：**
- 依赖未安装：`pip install cryptography`
- 权限问题：`chmod 600 data/secrets.db`
- 主密钥未配置：检查 `.env` 文件

---

## 📊 迁移后验证清单

- [ ] `config/agent_config.yaml` 不包含 `api_key_value`
- [ ] `data/secrets.db` 已创建
- [ ] `logs/config_audit.log` 有迁移记录
- [ ] Web 配置页面显示 Key 前缀
- [ ] 聊天功能正常工作
- [ ] 服务重启后仍然正常
- [ ] 主密钥已备份

---

## 🔒 安全最佳实践

### 1. 主密钥管理

```bash
# 查看主密钥（用于备份）
cat .env | grep LEARNING_AGENT_MASTER_KEY

# 备份到安全位置
cp .env /secure/location/learning-agent.env.backup

# 设置严格的文件权限
chmod 600 .env
chmod 600 data/secrets.db
```

### 2. 定期审计

```bash
# 查看配置变更日志
tail -f logs/config_audit.log

# 通过 API 查看审计日志
curl http://localhost:5001/api/config/audit-logs | jq
```

### 3. Key 轮换

```bash
# 通过 Web 页面更新 API Key
# 1. 访问 /config
# 2. 点击 "修改"
# 3. 输入新 Key
# 4. 保存

# 审计日志会自动记录
```

---

## 📝 回滚方案

如果需要回滚到旧配置：

```bash
# 1. 停止服务
sudo systemctl stop learning-agent

# 2. 恢复备份
cp config/agent_config.yaml.bak config/agent_config.yaml

# 3. 重启服务
sudo systemctl start learning-agent
```

---

## 🆘 获取帮助

如果遇到问题：

```bash
# 查看详细日志
sudo journalctl -u learning-agent -f

# 检查 KeyVault 状态
python3 -c "from services.key_vault import KeyVault; v = KeyVault(); print(v.list_providers())"

# 检查配置文件
python3 -c "import yaml; print(yaml.safe_load(open('config/agent_config.yaml')))"
```

---

_文档版本：v1.0_
_更新时间：2026-04-06_
