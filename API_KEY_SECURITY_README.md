# 🔐 API Key 安全配置快速指南

## 一分钟了解

**问题：** API Key 明文存储在配置文件中，有泄露风险

**解决：** 使用 KeyVault 加密存储，前端只能看到前缀（如 `sk-sp11***6e16`）

---

## 🚀 快速开始

### 1. 检查状态

```bash
cd /home/admin/.openclaw/workspace/learning-agent

# 检查是否已完成迁移
grep "api_key_value" config/agent_config.yaml
# 无输出 = ✅ 已迁移
# 有输出 = ❌ 需要迁移
```

### 2. 如果未完成迁移

```bash
# 安装依赖
source venv/bin/activate
pip install cryptography

# 生成主密钥并保存
python3 scripts/migrate_keys.py --generate-key
echo "LEARNING_AGENT_MASTER_KEY=生成的密钥" >> .env

# 执行迁移
python3 scripts/migrate_keys.py

# 重启服务
sudo systemctl restart learning-agent
```

---

## 🎨 前端使用

### 配置页面

访问：`http://localhost:5001/config`

**功能：**
- ✅ 查看 Key 状态（前缀显示）
- ✅ 修改 API Key
- ✅ 测试连接
- ✅ 删除 Key

### API 使用

```bash
# 获取 Provider 配置（不含明文 Key）
curl http://localhost:5001/api/config/providers

# 更新 API Key
curl -X POST http://localhost:5001/api/config/providers/dashscope/key \
  -H "Content-Type: application/json" \
  -d '{"api_key": "sk-sp-xxx"}'

# 测试连接
curl -X POST http://localhost:5001/api/config/providers/dashscope/test

# 查看审计日志
curl http://localhost:5001/api/config/audit-logs
```

---

## 📁 核心文件

| 文件 | 说明 |
|------|------|
| `services/key_vault.py` | KeyVault 核心（加密存储） |
| `data/secrets.db` | 加密数据库（权限 600） |
| `scripts/migrate_keys.py` | 迁移脚本 |
| `docs/API_KEY_MIGRATION_GUIDE.md` | 详细迁移指南 |

---

## 🔍 故障排查

### KeyVault 初始化失败

```bash
# 检查主密钥
grep LEARNING_AGENT_MASTER_KEY .env

# 重新生成
python3 scripts/migrate_keys.py --generate-key
```

### API Key 无法解密

```bash
# 检查主密钥是否正确
cat .env | grep MASTER_KEY

# 重新配置 Key（通过 Web 页面）
```

### 查看详细日志

```bash
sudo journalctl -u learning-agent -f
tail -f logs/config_audit.log
```

---

## 📚 详细文档

- **设计方案：** `docs/API_KEY_DESIGN.md`
- **迁移指南：** `docs/API_KEY_MIGRATION_GUIDE.md`
- **完成报告：** `docs/API_KEY_SECURITY_COMPLETE.md`

---

## ✅ 安全检查清单

定期检查：

- [ ] `.env` 文件权限：`chmod 600 .env`
- [ ] `secrets.db` 权限：`chmod 600 data/secrets.db`
- [ ] 主密钥已备份
- [ ] 审计日志正常
- [ ] 配置文件无明文 Key

---

_更新时间：2026-04-06_
