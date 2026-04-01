# 📁 公共配置目录

**位置：** `/home/admin/.openclaw/workspace/config/`

**用途：** 存储多个项目共享的配置文件（API Token、数据库连接等）

---

## 📦 配置文件

### 1. Tushare Pro 配置

**文件：** `tushare.yaml`

**用途：** 存储 Tushare Pro API Token

**权限：** 600（仅所有者可读写）

**内容：**
```yaml
tushare:
  token: "your_token_here"
  account:
    points: 2000
```

---

## 🔧 使用方法

### 方法 1：使用配置加载器（推荐）

```python
from config_loader import get_tushare_token

# 获取 Tushare Token
token = get_tushare_token()

# 初始化数据源
from tushare_pro_source import TushareProSource
ts = TushareProSource(token=token)
```

### 方法 2：直接读取配置文件

```python
import yaml

with open('/home/admin/.openclaw/workspace/config/tushare.yaml') as f:
    config = yaml.safe_load(f)
    token = config['tushare']['token']
```

### 方法 3：使用环境变量

```bash
# 设置环境变量
export TUSHARE_TOKEN=$(python3 -c "import yaml; print(yaml.safe_load(open('/home/admin/.openclaw/workspace/config/tushare.yaml'))['tushare']['token'])")

# 在代码中使用
import os
token = os.getenv('TUSHARE_TOKEN')
```

---

## 🔐 安全说明

### 文件权限

所有包含敏感信息的配置文件都应设置为 600 权限：

```bash
chmod 600 /home/admin/.openclaw/workspace/config/tushare.yaml
```

### 访问控制

- ✅ 允许：同一用户下的项目访问
- ❌ 禁止：将配置文件提交到 Git
- ❌ 禁止：分享给其他用户

### Git 忽略

确保 `.gitignore` 包含：

```gitignore
# 忽略公共配置目录
config/*.yaml
config/*.json
config/*.env
```

---

## 📝 添加新配置

### 步骤

1. **创建配置文件**
   ```bash
   touch /home/admin/.openclaw/workspace/config/new_service.yaml
   chmod 600 /home/admin/.openclaw/workspace/config/new_service.yaml
   ```

2. **编辑配置内容**
   ```yaml
   new_service:
     api_key: "your_api_key"
     endpoint: "https://api.example.com"
   ```

3. **更新配置加载器**
   ```python
   # 在 config_loader.py 中添加函数
   def get_new_service_key() -> Optional[str]:
       config = load_config('new_service')
       if config:
           return config.get('new_service', {}).get('api_key')
       return None
   ```

---

## 🛠️ 工具函数

### config_loader.py 提供的函数

| 函数 | 说明 | 示例 |
|------|------|------|
| `get_tushare_token()` | 获取 Tushare Token | `token = get_tushare_token()` |
| `load_config(name)` | 加载配置文件 | `config = load_config('tushare')` |
| `save_config(name, config)` | 保存配置文件 | `save_config('tushare', config)` |
| `get_env_with_fallback(var, config, *keys)` | 环境变量 + 配置回退 | `get_env_with_fallback('TUSHARE_TOKEN', 'tushare', 'tushare', 'token')` |

### 命令行工具

```bash
# 获取 Tushare Token
python3 config_loader.py get-token

# 测试配置加载
python3 config_loader.py test
```

---

## 📊 配置加载优先级

```
1. 环境变量 (最高优先级)
   ↓
2. 公共配置文件 (/home/admin/.openclaw/workspace/config/)
   ↓
3. 项目本地配置 (项目目录下的 config.yaml)
   ↓
4. 默认值 (最低优先级)
```

---

## 🔄 已集成的项目

### stock-notification

- ✅ 自动从公共配置加载 Tushare Token
- ✅ 支持环境变量覆盖
- ✅ 失败时回退到本地配置

### stock-agent

- ✅ 已配置公共 Token
- ✅ 可切换到公共配置加载

### stock-notification-web

- ✅ 通过 stock-notification 间接使用
- ✅ 无需单独配置

---

## 📞 故障排查

### 问题：无法加载 Token

**检查步骤：**

1. 确认配置文件存在
   ```bash
   ls -la /home/admin/.openclaw/workspace/config/tushare.yaml
   ```

2. 验证文件权限
   ```bash
   stat -c "%a" /home/admin/.openclaw/workspace/config/tushare.yaml
   # 应该是 600
   ```

3. 测试配置加载
   ```bash
   python3 /home/admin/.openclaw/workspace/config/config_loader.py test
   ```

4. 检查 Python 路径
   ```python
   import sys
   sys.path.insert(0, '/home/admin/.openclaw/workspace/config')
   from config_loader import get_tushare_token
   ```

### 问题：权限错误

**解决方案：**

```bash
# 修复文件权限
chmod 600 /home/admin/.openclaw/workspace/config/*.yaml

# 修复目录权限
chmod 700 /home/admin/.openclaw/workspace/config
```

---

## 📚 相关文档

- [Tushare Pro 文档](https://tushare.pro/document/2)
- [stock-notification 使用指南](../stock-notification/README.md)
- [stock-agent 使用指南](../stock-agent/README.md)

---

*最后更新：2026-03-29*
