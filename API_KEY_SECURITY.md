# 🔐 API Key 安全配置指南

## 快速开始

### 1. 统一 API Key 配置

所有项目使用**同一个 API Key**，通过环境变量自动同步：

```bash
# API Key（3 个变量名指向同一个值，确保兼容性）
ANTHROPIC_API_KEY=sk-sp-你的 key
DASHSCOPE_API_KEY=sk-sp-你的 key
ALIYUN_API_KEY=sk-sp-你的 key

# DashScope 专用 API 端点（重要！必须使用 coding.dashscope）
DASHSCOPE_BASE_URL=https://coding.dashscope.aliyuncs.com/v1
```

---

## 📁 配置文件位置

### learning-agent 项目

| 文件 | 权限 | 说明 |
|------|------|------|
| `learning-agent/.env` | 600 | 环境变量（包含 API Key） |
| `learning-agent/config/agent_config.yaml` | 600 | Agent 配置（包含 API Key） |
| `learning-agent/logs/config_audit.log` | 644 | 配置变更审计日志 |

### CCP 项目

| 文件 | 权限 | 说明 |
|------|------|------|
| `claude-code-python/.env` | 600 | 环境变量（包含 API Key） |

---

## 🔒 安全加固措施

### 1. 文件权限保护

```bash
# 已自动设置
chmod 600 .env
chmod 600 config/agent_config.yaml
```

**说明：**
- `600` = 只有所有者可读写
- 其他用户无法查看或修改

### 2. 配置变更审计

所有 API Key 变更都会记录到审计日志：

```bash
# 查看审计日志
tail -f learning-agent/logs/config_audit.log
```

**日志内容：**
- 配置修改时间
- API Key 前缀（不完整 Key，安全）
- 来源 IP 地址
- 修改结果（成功/失败）

### 3. API Key 格式验证

保存配置时自动验证：
- ✅ 必须以 `sk-` 开头
- ❌ 格式错误会拒绝保存

### 4. 多环境变量兼容

支持 3 个环境变量名，确保不同项目都能读取：

```python
# 优先级顺序
api_key = (
    DASHSCOPE_API_KEY or      # learning-agent 使用
    ALIYUN_API_KEY or         # CCP 备用
    ANTHROPIC_API_KEY         # CCP 主要使用
)
```

---

## 🌐 Web 界面配置

### 访问配置页面

```
http://39.97.249.78:5001/config
```

### 配置步骤

1. **打开配置页面**
2. **输入 API Key**（以 `sk-` 开头）
3. **点击"保存全部配置"**
4. **等待成功提示**

### 安全特性

- ✅ HTTPS 传输（如果启用了 SSL）
- ✅ 审计日志记录
- ✅ 格式验证
- ✅ 不显示完整 Key（前端只显示前缀）

---

## 🔍 验证配置

### 方法 1: 检查环境变量

```bash
# learning-agent
cd learning-agent
source venv/bin/activate
python3 -c "import os; print(os.getenv('DASHSCOPE_API_KEY', 'NOT SET')[:15] + '...')"

# CCP
cd claude-code-python
python3 -c "import os; print(os.getenv('ANTHROPIC_API_KEY', 'NOT SET')[:15] + '...')"
```

### 方法 2: 测试 API 调用

```bash
cd learning-agent
python3 -c "
from services.llm_client import LLMClient
import os
client = LLMClient(api_key=os.getenv('DASHSCOPE_API_KEY'))
result = client.chat([{'role': 'user', 'content': '你好'}])
print('Success:', result.get('success'))
"
```

### 方法 3: 查看配置文件

```bash
# 查看配置（注意权限）
cat learning-agent/config/agent_config.yaml | grep api_key_value
cat learning-agent/.env | grep DASHSCOPE
```

---

## ⚠️ 常见问题

### Q1: API Key 无效（401 错误）

**原因：**
- Key 已过期
- 配额用完
- 使用了错误的 API 端点

**解决：**
1. 去阿里云重新生成：https://dashscope.console.aliyun.com/apiKey
2. 确保使用 `coding.dashscope.aliyuncs.com` 端点
3. 更新配置并重启服务

### Q2: 400 Bad Request

**原因：**
- API 端点错误
- 请求格式问题

**解决：**
```bash
# 检查 base_url 是否正确
grep DASHSCOPE_BASE_URL learning-agent/.env
# 应该是：https://coding.dashscope.aliyuncs.com/v1
```

### Q3: 配置保存失败

**原因：**
- 文件权限问题
- 磁盘空间不足

**解决：**
```bash
# 修复权限
chmod 600 learning-agent/.env
chmod 600 learning-agent/config/agent_config.yaml

# 检查磁盘
df -h
```

---

## 📊 安全最佳实践

### ✅ 推荐做法

1. **定期轮换 API Key**（每 30-90 天）
2. **使用环境变量**而非硬编码
3. **限制文件权限**（600）
4. **查看审计日志**监控异常
5. **不同环境使用不同 Key**（开发/生产分离）

### ❌ 避免做法

1. ❌ 将 `.env` 文件提交到 Git
2. ❌ 在聊天中分享完整 API Key
3. ❌ 使用默认权限（644）
4. ❌ 多人共享同一个 Key
5. ❌ 长期不轮换 Key

---

## 🚨 应急响应

### 如果 API Key 泄露

1. **立即撤销**：去阿里云控制台禁用该 Key
2. **生成新 Key**：创建新的 API Key
3. **更新配置**：替换所有使用旧 Key 的地方
4. **检查日志**：查看是否有异常调用
5. **通知相关人员**：如果涉及团队

### 检查异常调用

```bash
# 查看最近的 API 调用记录
tail -100 learning-agent/data/llm_audit_logs/llm_calls_$(date +%Y-%m-%d).jsonl

# 统计调用次数
grep -c "success.*true" learning-agent/data/llm_audit_logs/llm_calls_*.jsonl
```

---

## 📞 技术支持

- **阿里云 DashScope 文档**：https://help.aliyun.com/zh/dashscope/
- **API Key 管理**：https://dashscope.console.aliyun.com/apiKey
- **问题反馈**：查看 `logs/config_audit.log` 获取详细错误信息

---

*最后更新：2026-04-04*
*版本：v1.0*
