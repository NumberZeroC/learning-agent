# 💬 Learning Agent 聊天窗口格式化展示方案

**日期：** 2026-04-04  
**问题：** Agent 回复 JSON 格式，聊天窗口需要易读展示

---

## 🎯 核心需求

### 当前问题

```
用户：帮我生成一个学习路线
Agent: {"layer":1,"layer_name":"基础理论层","topics":[...]}  ← ❌ 难以阅读
```

### 期望效果

```
用户：帮我生成一个学习路线
Agent: 
┌─────────────────────────────────────┐
│ 📚 第 1 层：基础理论层    ✅ 已完成 │
├─────────────────────────────────────┤
│ 🤖 AI 基础                          │
│ ✅ 机器学习基础范式                 │
│    监督学习、无监督学习...          │
└─────────────────────────────────────┘
```

---

## 📋 方案设计

### 架构总览

```
┌─────────────────────────────────────────────────────────┐
│                    主 Agent                              │
│  输出：JSON 格式（结构化数据）                           │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              聊天路由层 (chat_routes.py)                 │
│  保持 JSON 不变，直接返回给前端                          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              前端聊天窗口 (chat.html)                    │
│  新增：消息格式化器 (MessageFormatter)                   │
│  功能：                                                  │
│  1. 检测 JSON 格式                                       │
│  2. 自动渲染为美化卡片                                   │
│  3. 支持代码高亮、Markdown 渲染                          │
│  4. 流式输出兼容                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ 技术实现

### 1. 前端消息格式化器

```javascript
// web/static/js/chat-formatter.js

class ChatMessageFormatter {
    /**
     * 格式化 Agent 回复
     * @param {string|object} content - Agent 回复内容
     * @returns {string} - HTML 格式
     */
    static format(content) {
        // 1. 尝试解析 JSON
        const jsonData = this.tryParseJSON(content);
        
        if (jsonData) {
            // 2. 是 JSON，渲染为美化卡片
            return this.renderWorkflowCard(jsonData);
        } else {
            // 3. 普通文本，渲染 Markdown
            return this.renderMarkdown(content);
        }
    }
    
    /**
     * 尝试解析 JSON
     */
    static tryParseJSON(str) {
        try {
            const obj = JSON.parse(str);
            // 验证是否是工作流数据结构
            if (obj.layer && obj.layer_name && obj.topics) {
                return obj;
            }
            return null;
        } catch (e) {
            return null;
        }
    }
    
    /**
     * 渲染工作流卡片
     */
    static renderWorkflowCard(data) {
        const statusIcon = data.status === 'completed' ? '✅' : '⏳';
        
        return `
            <div class="workflow-card">
                <div class="workflow-header">
                    <span class="workflow-icon">📚</span>
                    <span class="workflow-title">第${data.layer}层：${data.layer_name}</span>
                    <span class="workflow-status">${statusIcon}</span>
                </div>
                
                <div class="workflow-topics">
                    ${data.topics.map(topic => `
                        <div class="topic-card">
                            <div class="topic-header">
                                <span class="topic-icon">🤖</span>
                                <span class="topic-title">${topic.name}</span>
                            </div>
                            <div class="topic-tasks">
                                ${topic.tasks.map(task => `
                                    <div class="task-item">
                                        <span class="task-icon">${task.status === 'completed' ? '✅' : '⏳'}</span>
                                        <span class="task-name">${task.name}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                <div class="workflow-footer">
                    <small class="completion-time">
                        完成时间：${this.formatTime(data.completed_at)}
                    </small>
                </div>
            </div>
        `;
    }
    
    /**
     * 渲染 Markdown
     */
    static renderMarkdown(text) {
        // 使用 marked.js 渲染
        return marked.parse(text);
    }
    
    /**
     * 格式化时间
     */
    static formatTime(isoString) {
        if (!isoString) return '-';
        const date = new Date(isoString);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}
```

### 2. 聊天窗口集成

```javascript
// web/templates/chat.html 中的消息添加逻辑

function addMessage(content, sender) {
    const messagesDiv = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    // 格式化内容
    let formattedContent;
    if (sender === 'assistant') {
        // Agent 消息：使用格式化器
        formattedContent = ChatMessageFormatter.format(content);
    } else {
        // 用户消息：直接显示
        formattedContent = content;
    }
    
    messageDiv.innerHTML = `
        <div class="message-avatar">
            ${sender === 'user' ? '👤' : '🤖'}
        </div>
        <div class="message-content">
            ${formattedContent}
        </div>
    `;
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}
```

### 3. 流式输出兼容

```javascript
// 支持流式输出的格式化

class StreamingFormatter {
    constructor(containerElement) {
        this.container = containerElement;
        this.currentContent = '';
        this.isJsonMode = false;
        this.jsonBuffer = '';
    }
    
    /**
     * 接收流式数据块
     */
    append(chunk) {
        this.currentContent += chunk;
        
        // 检测是否是 JSON 开头
        if (!this.isJsonMode && this.currentContent.trim().startsWith('{')) {
            this.isJsonMode = true;
        }
        
        if (this.isJsonMode) {
            this.jsonBuffer += chunk;
            this.renderJsonPreview();
        } else {
            this.renderMarkdownPreview();
        }
    }
    
    /**
     * 渲染 JSON 预览（流式）
     */
    renderJsonPreview() {
        try {
            // 尝试解析完整 JSON
            const data = JSON.parse(this.jsonBuffer);
            // 解析成功，渲染完整卡片
            this.container.innerHTML = ChatMessageFormatter.renderWorkflowCard(data);
        } catch (e) {
            // JSON 不完整，显示加载中
            this.container.innerHTML = `
                <div class="loading-card">
                    <div class="spinner"></div>
                    <p>正在生成学习路线...</p>
                    <pre class="json-preview">${this.escapeHtml(this.jsonBuffer)}</pre>
                </div>
            `;
        }
    }
    
    /**
     * 渲染 Markdown 预览（流式）
     */
    renderMarkdownPreview() {
        this.container.innerHTML = marked.parse(this.currentContent);
    }
    
    /**
     * 完成输出
     */
    complete() {
        if (this.isJsonMode) {
            try {
                const data = JSON.parse(this.jsonBuffer);
                this.container.innerHTML = ChatMessageFormatter.renderWorkflowCard(data);
            } catch (e) {
                // JSON 解析失败，显示原始内容
                this.container.innerHTML = marked.parse(this.jsonBuffer);
            }
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
```

---

## 🎨 CSS 样式设计

```css
/* web/static/css/chat-workflow.css */

/* 工作流卡片 */
.workflow-card {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    border-radius: 12px;
    padding: 20px;
    margin: 10px 0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    border-left: 5px solid #667eea;
}

/* 卡片头部 */
.workflow-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 2px solid rgba(102, 126, 234, 0.2);
}

.workflow-icon {
    font-size: 24px;
}

.workflow-title {
    font-size: 18px;
    font-weight: 600;
    color: #333;
    flex: 1;
}

.workflow-status {
    font-size: 14px;
    padding: 4px 12px;
    background: white;
    border-radius: 20px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

/* 主题卡片 */
.workflow-topics {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.topic-card {
    background: white;
    border-radius: 8px;
    padding: 15px;
    border-left: 3px solid #667eea;
}

.topic-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
}

.topic-icon {
    font-size: 18px;
}

.topic-title {
    font-weight: 600;
    color: #555;
}

/* 任务列表 */
.topic-tasks {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.task-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 5px 0;
}

.task-icon {
    font-size: 16px;
}

.task-name {
    color: #666;
    font-size: 14px;
}

/* 卡片底部 */
.workflow-footer {
    margin-top: 15px;
    padding-top: 10px;
    border-top: 1px solid rgba(102, 126, 234, 0.2);
}

.completion-time {
    color: #999;
    font-size: 12px;
}

/* 加载中卡片 */
.loading-card {
    text-align: center;
    padding: 30px;
}

.spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #667eea;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 15px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.json-preview {
    background: #2d2d2d;
    color: #f8f8f2;
    padding: 10px;
    border-radius: 5px;
    font-size: 12px;
    text-align: left;
    max-height: 200px;
    overflow-y: auto;
    margin-top: 15px;
}

/* 消息气泡适配 */
.message.assistant .message-content {
    max-width: 800px;
}

.message.assistant .workflow-card {
    margin: 0;
}
```

---

## 📝 完整示例

### Agent 输出（JSON）

```json
{
  "layer": 1,
  "layer_name": "基础理论层",
  "agent": "theory_worker",
  "status": "completed",
  "topics": [
    {
      "name": "AI 基础",
      "tasks": [
        {
          "name": "机器学习基础范式",
          "status": "completed"
        },
        {
          "name": "深度学习基础架构",
          "status": "completed"
        }
      ]
    },
    {
      "name": "大模型原理",
      "tasks": [
        {
          "name": "Transformer 架构",
          "status": "completed"
        }
      ]
    }
  ],
  "completed_at": "2026-04-04T21:30:00Z"
}
```

### 聊天窗口展示

```
┌─────────────────────────────────────────────────────┐
│ 👤 用户                                              │
│ 帮我生成一个 AI 学习路线                             │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ 🤖 Agent                                            │
│ ┌─────────────────────────────────────────────────┐ │
│ │ 📚 第 1 层：基础理论层              ✅ 已完成   │ │
│ │                                                 │ │
│ │ 🤖 AI 基础                                      │ │
│ │ ✅ 机器学习基础范式                             │ │
│ │ ✅ 深度学习基础架构                             │ │
│ │                                                 │ │
│ │ 🤖 大模型原理                                   │ │
│ │ ✅ Transformer 架构                             │ │
│ │                                                 │ │
│ │ 完成时间：2026-04-04 21:30                      │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 实施步骤

### 步骤 1：创建格式化器（30 分钟）

```bash
# 创建文件
touch /home/admin/.openclaw/workspace/learning-agent/web/static/js/chat-formatter.js
```

**内容：** 复制上面的 `ChatMessageFormatter` 类

### 步骤 2：引入聊天页面（10 分钟）

```html
<!-- web/templates/chat.html -->
<head>
    <!-- 现有脚本 -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    
    <!-- 新增格式化器 -->
    <script src="/static/js/chat-formatter.js"></script>
    <link rel="stylesheet" href="/static/css/chat-workflow.css">
</head>
```

### 步骤 3：修改消息添加逻辑（20 分钟）

```javascript
// 找到 addMessage 函数，修改为：

function addMessage(content, sender) {
    const messagesDiv = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    let formattedContent;
    if (sender === 'assistant') {
        formattedContent = ChatMessageFormatter.format(content);
    } else {
        formattedContent = content;
    }
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${sender === 'user' ? '👤' : '🤖'}</div>
        <div class="message-content">${formattedContent}</div>
    `;
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}
```

### 步骤 4：添加 CSS 样式（20 分钟）

```bash
# 创建文件
touch /home/admin/.openclaw/workspace/learning-agent/web/static/css/chat-workflow.css
```

**内容：** 复制上面的 CSS 样式

### 步骤 5：测试（10 分钟）

```bash
# 重启 Web 服务
pkill -f "python3 web/app.py"
cd learning-agent && python3 web/app.py

# 访问聊天页面
http://localhost:5001/chat

# 发送测试消息
"帮我生成一个学习路线"
```

---

## ✅ 预期效果

### 修改前

```
🤖 Agent
{"layer":1,"layer_name":"基础理论层","topics":[{"name":"AI 基础","tasks":...}]}
```

### 修改后

```
🤖 Agent
┌──────────────────────────────────┐
│ 📚 第 1 层：基础理论层  ✅ 已完成 │
│ 🤖 AI 基础                        │
│ ✅ 机器学习基础范式               │
│ ✅ 深度学习基础架构               │
└──────────────────────────────────┘
```

---

## 📊 功能对比

| 功能 | 修改前 | 修改后 |
|------|--------|--------|
| **JSON 展示** | ❌ 原始文本 | ✅ 美化卡片 |
| **代码高亮** | ❌ 无 | ✅ 支持 |
| **Markdown** | ❌ 无 | ✅ 支持 |
| **流式兼容** | ✅ 支持 | ✅ 支持 |
| **状态图标** | ❌ 无 | ✅ ✅/⏳ |
| **时间显示** | ❌ 无 | ✅ 格式化 |

---

## 🎯 推荐实施方案

**前端格式化方案**

- ✅ 后端无需改动
- ✅ 兼容现有 JSON 输出
- ✅ 支持流式输出
- ✅ 易于扩展

**预计工时：** 1-1.5 小时  
**风险：** 低

---

**状态：** ✅ 方案设计完成，等待实施
