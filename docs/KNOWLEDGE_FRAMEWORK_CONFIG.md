# 📐 知识架构配置与自动生成

**创建日期：** 2026-04-18  
**配置文件：** `config/knowledge_framework.yaml`

---

## 🎯 功能概述

### 核心特性

1. **外置知识架构配置** - 从硬编码改为 YAML 配置文件
2. **自动生成功能** - 配置文件不存在时调用大模型自动生成
3. **5 层架构限定** - 严格遵循 5 层知识体系设计
4. **灵活扩展** - 支持手动编辑和版本管理

---

## 📁 文件位置

```
learning-agent/
├── config/
│   ├── agent_config.yaml        # Agent 配置（System Prompt 等）
│   └── knowledge_framework.yaml # 知识架构配置（新增）
├── workflow_orchestrator.py     # 工作流编排器（已更新）
└── run_workflow.py              # 启动脚本（已更新）
```

---

## 🏗️ 架构设计

### 5 层知识体系

```yaml
name: Agent 开发面试知识体系
version: "1.0"
description: AI Agent 开发岗位面试知识体系

layers:
  - layer: 1
    name: 基础理论层
    agent: theory_worker
    topics: [...]
    
  - layer: 2
    name: 技术栈层
    agent: tech_stack_worker
    topics: [...]
    
  - layer: 3
    name: 核心能力层
    agent: core_skill_worker
    topics: [...]
    
  - layer: 4
    name: 工程实践层
    agent: engineering_worker
    topics: [...]
    
  - layer: 5
    name: 面试准备层
    agent: interview_worker
    topics: [...]
```

---

## 🤖 自动生成流程

### 触发条件

```python
# 配置文件不存在时自动触发
if not Path("config/knowledge_framework.yaml").exists():
    # 调用大模型生成架构
    architecture = self._generate_architecture()
```

### 生成步骤

```
1. 检测配置文件是否存在
   │
   ├─ 存在 → 加载 YAML 配置
   │
   └─ 不存在 → 调用大模型生成
       │
       ├─ 构建 System Prompt（限定 5 层架构）
       │
       ├─ 调用 Qwen3.5-Plus 生成 YAML
       │
       ├─ 解析并验证 YAML 格式
       │
       └─ 保存到 config/knowledge_framework.yaml
```

### System Prompt 关键内容

```
你是 AI 教育专家和知识架构师...

要求：
1. 严格分为 5 个层级（必须按顺序）：
   - 第 1 层：基础理论层
   - 第 2 层：技术栈层
   - 第 3 层：核心能力层
   - 第 4 层：工程实践层
   - 第 5 层：面试准备层

2. 每层 3-4 个主题，每个主题包含：
   - name, description, priority, subtopics

3. 输出格式：严格的 YAML 格式
```

---

## 📝 配置项说明

### 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 架构名称 |
| `version` | string | ✅ | 版本号 |
| `description` | string | ❌ | 架构描述 |
| `layers` | array | ✅ | 层级列表 |

### 层级字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `layer` | int | ✅ | 层级编号 (1-5) |
| `name` | string | ✅ | 层级名称 |
| `agent` | string | ✅ | 负责 Agent（与 agent_config.yaml 对应） |
| `topics` | array | ✅ | 主题列表 |

### 主题字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 主题名称 |
| `description` | string | ✅ | 主题描述 |
| `priority` | string | ✅ | 优先级 (high/medium) |
| `subtopics` | array | ❌ | 子主题列表 |

---

## 🚀 使用方式

### 方式 1：使用现有配置

```bash
cd /home/admin/.openclaw/workspace/learning-agent

# 配置文件已存在，直接运行
python3 run_workflow.py
```

**输出：**
```
📐 知识架构配置：
   ✅ 配置文件存在：config/knowledge_framework.yaml
   📚 架构名称：Agent 开发面试知识体系
   📊 层级数量：5
   📝 主题总数：17
```

---

### 方式 2：自动生成配置

```bash
# 删除或重命名现有配置
mv config/knowledge_framework.yaml config/knowledge_framework.yaml.bak

# 运行工作流（自动触发生成）
python3 run_workflow.py
```

**输出：**
```
📐 知识架构配置：
   ⚠️  配置文件不存在：config/knowledge_framework.yaml
   🤖 将自动调用大模型生成知识架构...

🤖 调用大模型生成知识架构...
✅ 大模型生成成功，解析 YAML...
📄 知识架构已保存到：config/knowledge_framework.yaml
```

---

### 方式 3：手动编辑配置

```bash
# 编辑配置文件
vim config/knowledge_framework.yaml

# 修改后运行
python3 run_workflow.py
```

---

## 🔧 代码集成

### WorkflowOrchestrator 初始化

```python
orchestrator = WorkflowOrchestrator(
    config_path="config/agent_config.yaml",
    framework_path="config/knowledge_framework.yaml",
    max_concurrent=1,              # 层内并发数
    enable_cache=True,             # 启用缓存
    auto_generate_framework=True   # 自动生成架构
)
```

### 关键方法

| 方法 | 功能 | 调用时机 |
|------|------|---------|
| `_load_or_generate_architecture()` | 加载或生成架构 | `__init__` |
| `_load_architecture_from_file()` | 从 YAML 文件加载 | 文件存在时 |
| `_generate_architecture()` | 调用大模型生成 | 文件不存在时 |
| `_get_default_architecture()` | 返回默认架构 | 生成失败降级 |

---

## 📊 生成示例

### 自动生成日志

```
2026-04-18 15:20:00 - ⚠️  知识架构配置文件不存在，开始自动生成...
2026-04-18 15:20:00 - 🤖 调用大模型生成知识架构...
2026-04-18 15:20:15 - ✅ 大模型生成成功，解析 YAML...
2026-04-18 15:20:15 - 📄 知识架构已保存到：config/knowledge_framework.yaml
2026-04-18 15:20:15 - ✅ 成功加载知识架构：Agent 开发面试知识体系 v1.0
2026-04-18 15:20:15 -    层级数：5
```

### 生成的配置文件

```yaml
# AI Agent 开发面试知识体系架构
# 自动生成时间：2026-04-18T15:20:15.123456
# 生成模型：qwen3.5-plus

name: Agent 开发面试知识体系
version: "1.0"
description: AI Agent 开发岗位面试知识体系

layers:
  - layer: 1
    name: 基础理论层
    agent: theory_worker
    topics:
      - name: AI 基础
        description: 机器学习和深度学习基础概念和原理
        priority: high
        subtopics:
          - 监督学习与无监督学习
          - 神经网络基础
          - 优化算法
      # ... 更多主题
```

---

## ⚠️ 注意事项

### 1. API Key 配置

自动生成需要有效的 API Key：

```bash
# 检查 API Key
cat .env | grep DASHSCOPE_API_KEY

# 如果为空，需要配置
export DASHSCOPE_API_KEY=sk-xxx
```

### 2. 生成失败降级

如果大模型生成失败，会降级到默认架构：

```python
except Exception as e:
    logger.error(f"❌ 知识架构生成异常：{e}")
    logger.warning("⚠️  使用默认知识架构")
    return self._get_default_architecture()
```

### 3. YAML 格式验证

生成的 YAML 会经过解析验证，确保格式正确：

```python
try:
    data = yaml.safe_load(yaml_content)
    # 保存到文件
except yaml.YAMLError as e:
    logger.error(f"❌ YAML 解析失败：{e}")
    raise
```

### 4. 版本管理

建议将 `knowledge_framework.yaml` 纳入版本管理：

```bash
git add config/knowledge_framework.yaml
git commit -m "📐 添加知识架构配置文件"
```

---

## 🔄 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-04-18 | 初始版本，5 层 17 主题 |

---

## 🔗 相关文档

- [CONCURRENCY_TEST_REPORT.md](./CONCURRENCY_TEST_REPORT.md) - 并发测试报告
- [LAYER_CONCURRENCY_FIX.md](./LAYER_CONCURRENCY_FIX.md) - 层间并发修复
- [WORKFLOW_PERFORMANCE_ANALYSIS.md](./WORKFLOW_PERFORMANCE_ANALYSIS.md) - 性能分析

---

## 📞 总结

**核心价值：**
1. ✅ **配置外置** - 架构与代码分离，易于维护
2. ✅ **自动生成** - 降低使用门槛
3. ✅ **灵活扩展** - 支持自定义架构
4. ✅ **版本管理** - 可追踪架构演进

**下一步：**
- 运行一次完整测试验证自动生成功能
- 根据实际需求调整架构内容
- 考虑添加架构验证工具
