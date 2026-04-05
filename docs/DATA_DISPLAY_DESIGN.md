# 📊 Learning Agent 数据展示方案设计

**日期：** 2026-04-04  
**问题：** 主 Agent 输出 JSON 格式 vs Web 界面需要易读展示

---

## 🎯 核心需求

| 角色 | 需求 | 原因 |
|------|------|------|
| **主 Agent** | JSON 格式 | 便于程序处理、验证、存储 |
| **Web 用户** | 易读格式 | 便于浏览、理解、分享 |
| **系统** | 两者兼容 | 不改变现有架构 |

---

## 📋 方案设计

### 架构总览

```
┌─────────────────────────────────────────────────────────┐
│                    主 Agent (后端)                       │
│  输出：JSON 格式 (结构化数据，便于存储和处理)             │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  API 层 (数据转换)                        │
│  提供两种接口：                                           │
│  1. /api/workflow/layers (原始 JSON)                     │
│  2. /api/workflow/layers?format=html (渲染后 HTML)        │
│  3. /api/workflow/layers?format=markdown (Markdown)       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                Web 界面 (前端展示)                        │
│  提供多种视图切换：                                       │
│  1. 📖 阅读视图 (美化渲染)                               │
│  2. 📋 表格视图 (结构化表格)                             │
│  3. 🔧 JSON 视图 (原始数据，开发者模式)                   │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ 技术实现

### 方案 A：前端渲染（推荐）✅

**优点：**
- ✅ 后端无需改动
- ✅ 灵活定制展示样式
- ✅ 支持视图切换
- ✅ 减少服务器负载

**实现：**

```javascript
// 1. 后端返回标准 JSON
const response = await fetch('/api/workflow/layers');
const data = await response.json();

// 2. 前端根据数据渲染
function renderLayer(layer) {
    return `
        <div class="layer-card">
            <h3>${layer.layer_name}</h3>
            <div class="topics">
                ${layer.topics.map(topic => `
                    <div class="topic">
                        <h4>${topic.name}</h4>
                        <div class="tasks">
                            ${topic.tasks.map(task => `
                                <div class="task">
                                    <span class="task-icon">${task.completed ? '✅' : '⏳'}</span>
                                    <span class="task-name">${task.name}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// 3. 提供视图切换
function switchView(viewType) {
    switch(viewType) {
        case 'read': renderReadView(); break;
        case 'table': renderTableView(); break;
        case 'json': renderJsonView(); break;
    }
}
```

### 方案 B：后端渲染（备选）

**优点：**
- ✅ SEO 友好
- ✅ 前端代码简单

**缺点：**
- ❌ 增加服务器负载
- ❌ 不够灵活

**实现：**

```python
# web/routes/workflow_routes.py

@workflow_bp.route('/layers')
def get_layers():
    format_type = request.args.get('format', 'json')
    
    layers = load_layers_from_db()
    
    if format_type == 'json':
        return jsonify(layers)
    elif format_type == 'html':
        return render_template('workflow_rendered.html', layers=layers)
    elif format_type == 'markdown':
        md = generate_markdown(layers)
        return Response(md, mimetype='text/markdown')
```

---

## 📝 JSON 数据结构设计

### 原始 JSON（Agent 输出）

```json
{
  "layer": 1,
  "layer_name": "基础理论层",
  "agent": "theory_worker",
  "topics": [
    {
      "id": "topic_1_1",
      "name": "AI 基础",
      "tasks": [
        {
          "id": "task_1_1_1",
          "name": "机器学习基础范式",
          "status": "completed",
          "content": "监督学习、无监督学习、强化学习...",
          "knowledge_points": [
            "回归与分类算法",
            "特征工程基础",
            "模型评估指标"
          ]
        }
      ],
      "completed_at": "2026-04-04T09:00:00Z"
    }
  ],
  "completed_at": "2026-04-04T09:15:00Z"
}
```

### 前端展示数据（渲染后）

```javascript
// 前端接收 JSON 后转换为展示数据
const displayData = {
    layer: 1,
    title: "基础理论层",
    icon: "📚",
    progress: 75,  // 完成度百分比
    topics: [
        {
            title: "AI 基础",
            icon: "🤖",
            status: "completed",  // completed | in-progress | pending
            tasks: [
                {
                    title: "机器学习基础范式",
                    status: "completed",
                    icon: "✅",
                    details: "..."
                }
            ]
        }
    ]
};
```

---

## 🎨 Web 界面设计

### 视图切换按钮

```html
<div class="view-switcher">
    <button class="btn active" data-view="read">
        <i class="bi bi-book"></i> 阅读视图
    </button>
    <button class="btn" data-view="table">
        <i class="bi bi-table"></i> 表格视图
    </button>
    <button class="btn" data-view="json">
        <i class="bi bi-braces"></i> JSON 视图
    </button>
</div>
```

### 阅读视图（默认）

```
┌─────────────────────────────────────────────────────┐
│  📚 第 1 层：基础理论层                    ✅ 已完成   │
│  完成时间：2026-04-04 09:15                         │
├─────────────────────────────────────────────────────┤
│  🤖 AI 基础                              ✅ 已完成   │
│  ─────────────────────────────────────────────────  │
│  ✅ 机器学习基础范式                                 │
│     监督学习、无监督学习、强化学习...                │
│                                                     │
│  ✅ 深度学习基础架构                                 │
│     CNN、RNN、Transformer...                        │
│                                                     │
│  ⏳ 大模型原理                                       │
│     等待生成中...                                   │
└─────────────────────────────────────────────────────┘
```

### 表格视图

| 层级 | 主题 | 任务 | 状态 | 完成时间 |
|------|------|------|------|----------|
| 1 | AI 基础 | 机器学习基础 | ✅ | 09:00 |
| 1 | AI 基础 | 深度学习架构 | ✅ | 09:05 |
| 1 | AI 基础 | 大模型原理 | ⏳ | - |

### JSON 视图（开发者模式）

```json
{
  "layer": 1,
  "layer_name": "基础理论层",
  "topics": [...]
}
```

---

## 📦 文件结构

```
learning-agent/
├── web/
│   ├── routes/
│   │   └── workflow_routes.py      # API 路由（返回 JSON）
│   ├── templates/
│   │   ├── workflow.html           # 主页面
│   │   └── components/
│   │       ├── layer-card.html     # 层级卡片组件
│   │       └── topic-list.html     # 主题列表组件
│   └── static/
│       ├── js/
│       │   ├── workflow-viewer.js  # 视图渲染器
│       │   └── view-switcher.js    # 视图切换器
│       └── css/
│           ├── workflow-read.css   # 阅读视图样式
│           ├── workflow-table.css  # 表格视图样式
│           └── workflow-json.css   # JSON 视图样式
└── docs/
    └── DATA_DISPLAY_DESIGN.md      # 本文档
```

---

## 🚀 实施步骤

### 阶段 1：前端渲染器（1-2 小时）

```javascript
// web/static/js/workflow-viewer.js

class WorkflowViewer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.currentView = 'read';
    }
    
    async loadLayers() {
        const response = await fetch('/api/workflow/layers');
        const data = await response.json();
        this.render(data);
    }
    
    render(data) {
        switch(this.currentView) {
            case 'read':
                this.container.innerHTML = this.renderReadView(data);
                break;
            case 'table':
                this.container.innerHTML = this.renderTableView(data);
                break;
            case 'json':
                this.container.innerHTML = this.renderJsonView(data);
                break;
        }
    }
    
    renderReadView(data) {
        // 美化渲染逻辑
    }
    
    renderTableView(data) {
        // 表格渲染逻辑
    }
    
    renderJsonView(data) {
        return `<pre><code>${JSON.stringify(data, null, 2)}</code></pre>`;
    }
    
    switchView(viewType) {
        this.currentView = viewType;
        this.loadLayers();
    }
}
```

### 阶段 2：样式优化（1 小时）

```css
/* web/static/css/workflow-read.css */

.layer-card {
    background: white;
    border-radius: 10px;
    padding: 20px;
    margin: 20px 0;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.layer-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.topic-card {
    border-left: 4px solid #667eea;
    padding-left: 15px;
    margin: 15px 0;
}

.task-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 0;
}
```

### 阶段 3：视图切换（30 分钟）

```javascript
// web/static/js/view-switcher.js

document.querySelectorAll('[data-view]').forEach(btn => {
    btn.addEventListener('click', (e) => {
        const view = e.target.dataset.view;
        
        // 更新按钮状态
        document.querySelectorAll('[data-view]').forEach(b => 
            b.classList.remove('active'));
        e.target.classList.add('active');
        
        // 切换视图
        viewer.switchView(view);
        
        // 保存用户偏好
        localStorage.setItem('workflow_view', view);
    });
});
```

---

## 📊 数据流对比

### 修改前

```
Agent → JSON → 前端 → 直接显示 JSON
```

### 修改后

```
Agent → JSON → 前端 → 渲染器 → 美化 HTML → 用户
                        ↓
                   视图切换
                        ↓
            阅读视图 | 表格视图 | JSON 视图
```

---

## ✅ 优势总结

| 特性 | 说明 |
|------|------|
| **向后兼容** | 不改变 Agent 输出格式 |
| **灵活展示** | 支持多种视图切换 |
| **用户友好** | 默认美化渲染，易于阅读 |
| **开发者友好** | 提供 JSON 原始数据视图 |
| **性能优化** | 前端渲染，减少服务器负载 |
| **易于扩展** | 可添加更多视图（如思维导图） |

---

## 🎯 推荐实施方案

**使用方案 A（前端渲染）**

1. ✅ 保持 Agent JSON 输出不变
2. ✅ 前端添加渲染器（WorkflowViewer 类）
3. ✅ 提供 3 种视图切换（阅读/表格/JSON）
4. ✅ 保存用户视图偏好

**预计工时：** 3-4 小时  
**风险：** 低（不影响现有功能）

---

**状态：** ✅ 方案设计完成，等待实施
