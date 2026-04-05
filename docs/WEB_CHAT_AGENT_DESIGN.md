# 🤖 Web Chat Agent 设计方案

**日期：** 2026-04-04  
**目的：** 创建专门用于 Web 聊天的 Agent，与 master_agent 分离

---

## 📋 问题背景

### 原有架构问题

```
用户问题 → master_agent → JSON 格式输出 ❌
```

**master_agent 设计用途：**
- ✅ 工作流任务分解
- ✅ 协调子 Agent
- ✅ 输出 JSON 格式（程序处理）

**不适合聊天的原因：**
- ❌ 输出 JSON，不易阅读
- ❌ 设计用于任务分解，不是知识问答
- ❌ 回复格式僵硬，不够自然

---

## 🎯 解决方案

### 新增 web_chat_agent

```
用户问题 → web_chat_agent → 自然语言回答 ✅
```

**设计定位：**
- ✅ 专门用于 Web 聊天窗口
- ✅ 输出自然语言（Markdown 格式）
- ✅ 支持代码示例、概念讲解
- ✅ 友好、专业、易懂

---

## 📊 Agent 对比

| 特性 | master_agent | web_chat_agent |
|------|--------------|----------------|
| **用途** | 工作流任务分解 | Web 聊天问答 |
| **输出格式** | JSON 结构化数据 | 自然语言（Markdown） |
| **使用场景** | 后台批量执行 | 实时对话交互 |
| **回复风格** | 正式、结构化 | 友好、易懂 |
| **代码示例** | 完整项目代码 | 片段示例 |
| **调用时机** | 工作流生成时 | 用户提问时 |

---

## 🛠️ 技术实现

### 1. Agent 配置

**文件：** `config/agent_config.yaml`

```yaml
agents:
  web_chat_agent:
    description: 专门用于 Web 聊天窗口的知识问答 Agent
    enabled: true
    hot_reload: true
    layer: 0
    llm_config:
      max_tokens: 4000
      temperature: 0.7
      top_p: 0.9
    model: qwen3.5-plus
    provider: dashscope
    role: AI 知识问答助手
    system_prompt: |
      你是 Learning Agent 系统的**AI 知识问答助手**。
      
      ## 你的身份
      - 资深 AI 技术专家，精通 AI/ML/Agent 领域
      - 优秀的教育者，善于用通俗易懂的方式讲解复杂概念
      - 实战经验丰富，能提供可运行的代码示例
      
      ## 你的职责
      1. 回答技术问题
      2. 概念讲解
      3. 代码示例
      4. 学习建议
      5. 问题诊断
      
      ## 回答原则
      - 清晰易懂
      - 结构化
      - 实用导向
      - 举例说明
      - 循序渐进
      
      ## 输出格式
      - 使用 Markdown 格式
      - 代码块标注语言类型
      - 重要概念加粗或高亮
      - **不要输出 JSON 格式**
```

### 2. 后端路由修改

**文件：** `web/routes/chat_routes.py`

```python
@chat_bp.route('/stream', methods=['POST'])
def stream_message():
    """
    发送消息给 Agent (Ask 模式) - 流式响应 (SSE)
    
    请求体:
    {
        "message": "用户消息",
        "agent": "web_chat_agent"  # 默认 web_chat_agent
    }
    """
    data = request.get_json()
    message = data.get('message', '')
    # 默认使用 web_chat_agent 而不是 master_agent
    agent_name = data.get('agent', 'web_chat_agent')
```

### 3. 前端调用修改

**文件：** `web/templates/chat.html`

```javascript
// 发送 POST 请求接收 SSE 流
const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        message: message,
        agent: 'web_chat_agent'  // 使用专门的聊天 Agent
    })
});
```

---

## 📝 使用示例

### 用户提问

```
用户：什么是 Transformer 架构？
```

### master_agent 回复（旧）❌

```json
{
  "layer": 1,
  "layer_name": "基础理论层",
  "topics": [
    {
      "name": "大模型原理",
      "tasks": [...]
    }
  ]
}
```

### web_chat_agent 回复（新）✅

```markdown
## Transformer 架构详解

Transformer 是一种基于**自注意力机制**的深度学习模型，由 Google 在 2017 年提出。

### 核心组件

1. **编码器（Encoder）**
   - 处理输入序列
   - 提取特征表示

2. **解码器（Decoder）**
   - 生成输出序列
   - 基于编码结果

3. **多头注意力（Multi-Head Attention）**
   - 捕捉长距离依赖
   - 并行计算

### 代码示例

```python
import torch
import torch.nn as nn

class Transformer(nn.Module):
    def __init__(self, d_model=512, nhead=8):
        super().__init__()
        self.encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, 
            nhead=nhead
        )
        self.transformer_encoder = nn.TransformerEncoder(
            self.encoder_layer, 
            num_layers=6
        )
    
    def forward(self, src):
        return self.transformer_encoder(src)
```

### 应用场景

- 机器翻译
- 文本生成
- 问答系统
- 图像识别（Vision Transformer）
```

---

## 🎯 回答风格指南

### web_chat_agent 的回答特点

1. **友好开场**
   ```
   你好！这是一个很好的问题...
   ```

2. **结构化讲解**
   ```markdown
   ## 概念定义
   ...
   
   ## 核心原理
   ...
   
   ## 代码示例
   ...
   
   ## 应用场景
   ...
   ```

3. **代码示例**
   - 简短、可运行
   - 标注语言类型
   - 包含注释说明

4. **鼓励追问**
   ```
   如果还有疑问，欢迎继续提问！
   ```

---

## 📊 测试验证

### 测试问题

```bash
# 问题 1：概念讲解
"什么是 ReAct 框架？"

# 问题 2：代码示例
"如何用 Python 实现一个简单的 Agent？"

# 问题 3：学习建议
"我想学习 AI Agent，应该从哪里开始？"
```

### 预期效果

- ✅ 自然语言回答
- ✅ Markdown 格式化
- ✅ 代码高亮显示
- ✅ 结构清晰易懂
- ✅ 无 JSON 输出

---

## 🚀 部署步骤

### 1. 更新配置文件

```bash
# 编辑 agent_config.yaml
nano config/agent_config.yaml

# 添加 web_chat_agent 配置
```

### 2. 修改后端路由

```bash
# 编辑 chat_routes.py
nano web/routes/chat_routes.py

# 修改默认 agent 为 web_chat_agent
```

### 3. 修改前端调用

```bash
# 编辑 chat.html
nano web/templates/chat.html

# 修改 agent 参数为 web_chat_agent
```

### 4. 重启服务

```bash
pkill -f "python3 web/app.py"
cd learning-agent && python3 web/app.py
```

### 5. 测试验证

```bash
# 访问聊天页面
http://localhost:5001/chat

# 发送测试问题
"你好，介绍一下你自己"
```

---

## ✅ 验证清单

- [x] web_chat_agent 配置已添加
- [x] 后端路由默认 agent 已修改
- [x] 前端调用 agent 已修改
- [x] 服务已重启
- [ ] 聊天测试通过
- [ ] 代码高亮正常
- [ ] 无 JSON 输出

---

## 📈 后续优化

### 短期优化

- [ ] 添加对话上下文记忆
- [ ] 支持多轮对话
- [ ] 添加问题分类（技术/学习/项目）

### 长期优化

- [ ] 集成 RAG（检索增强生成）
- [ ] 支持文件上传和分析
- [ ] 添加对话历史搜索
- [ ] 支持多模态（图片 + 文本）

---

**状态：** ✅ 已部署，等待测试验证
