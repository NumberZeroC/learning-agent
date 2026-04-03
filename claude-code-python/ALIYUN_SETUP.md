# 阿里云通义千问 (Qwen) 配置指南

本指南介绍如何将 CCP 对接到阿里云大模型（通义千问）。

---

## 📋 前提条件

1. **阿里云账号** - 注册阿里云账号
2. **开通 DashScope 服务** - 在阿里云控制台开通
3. **API Key** - 从 DashScope 控制台获取

---

## 🔑 获取 API Key

1. 访问 [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/)
2. 登录阿里云账号
3. 进入 "API-KEY Management" 页面
4. 创建新的 API Key
5. 复制并保存 API Key

---

## ⚙️ 配置方式

### 方式 1：环境变量（推荐）

```bash
# 设置使用阿里云
export USE_ALIYUN=1

# 设置 API Key
export DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx

# 或者使用这个变量名
export ALIYUN_API_KEY=sk-xxxxxxxxxxxxxxxx
```

### 方式 2：命令行指定

```bash
# 临时使用阿里云
USE_ALIYUN=1 DASHSCOPE_API_KEY=sk-xxx ccp run "Hello"
```

### 方式 3：永久配置

将以下内容添加到 `~/.bashrc` 或 `~/.zshrc`：

```bash
# 使用阿里云通义千问
export USE_ALIYUN=1
export DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx
```

---

## 🚀 运行

### CLI 模式

```bash
# 激活虚拟环境
cd /home/admin/.openclaw/workspace/claude-code-python
source .venv/bin/activate

# 设置环境变量
export USE_ALIYUN=1
export DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx

# 运行任务
ccp run "Hello, World!"

# 交互模式
ccp run -i
```

### UI 模式

```bash
# 设置环境变量
export USE_ALIYUN=1
export DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx

# 启动 UI
python -m src.main
```

---

## 📊 可用模型

| 模型 | 说明 | 推荐用途 |
|------|------|----------|
| `qwen-turbo` | 速度快，成本低 | 简单任务 |
| `qwen-plus` | 平衡性能和成本 | 日常使用（默认） |
| `qwen-max` | 最强性能 | 复杂任务 |
| `qwen-max-longcontext` | 支持长上下文 | 长文档分析 |

### 切换模型

```bash
# 使用 qwen-max
ccp run -m qwen-max "复杂任务"

# 使用 qwen-turbo
ccp run -m qwen-turbo "简单任务"
```

---

## 💰 价格参考

| 模型 | 输入价格 | 输出价格 |
|------|----------|----------|
| qwen-turbo | ¥0.002/1K tokens | ¥0.006/1K tokens |
| qwen-plus | ¥0.004/1K tokens | ¥0.012/1K tokens |
| qwen-max | ¥0.04/1K tokens | ¥0.12/1K tokens |

*价格可能变动，请以官网为准*

---

## 🔧 代码修改说明

### 新增文件

- `src/llm/aliyun.py` - 阿里云 Provider 实现

### 修改文件

- `src/llm/__init__.py` - 导出 AliyunProvider
- `src/main.py` - 支持自动检测阿里云
- `src/cli/entry.py` - CLI 支持阿里云

### 核心类

```python
from src.llm import AliyunProvider

# 创建阿里云 Provider
provider = AliyunProvider(
    api_key="sk-xxx",
    model="qwen-plus",  # 可选：qwen-turbo, qwen-max
)

# 使用
response = await provider.chat(messages)
```

---

## ✅ 验证配置

```bash
# 测试连接
ccp run "Hello, 请回复我"

# 查看版本
ccp --version

# 查看帮助
ccp --help
```

---

## ⚠️ 常见问题

### 1. API Key 无效

```
Error: Invalid API key
```

**解决：** 检查 API Key 是否正确复制，确保没有多余空格

### 2. 余额不足

```
Error: Insufficient balance
```

**解决：** 在阿里云控制台充值

### 3. 模型不存在

```
Error: Model not found
```

**解决：** 检查模型名称是否正确，确保已开通该模型

### 4. 网络问题

```
Error: Connection timeout
```

**解决：** 检查网络连接，确保可以访问 dashscope.aliyuncs.com

---

## 📚 参考链接

- [阿里云 DashScope 文档](https://help.aliyun.com/zh/dashscope/)
- [通义千问模型介绍](https://help.aliyun.com/zh/dashscope/developer-reference/model-introduction)
- [API 参考](https://help.aliyun.com/zh/dashscope/developer-reference/api-reference)

---

*最后更新：2026-04-02*
