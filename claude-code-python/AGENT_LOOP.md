# 🤖 CCP Agent 自主执行循环

**版本：** v0.2  
**日期：** 2026-04-03  
**特性：** 完整的 ReAct 模式 Agent 循环

---

## 🎯 问题背景

之前的 CCP 执行模式：
```
用户：分析这个项目
AI: 我来分析一下...
🔧 Using tool: bash (ls -la)
Result: ...
[然后就停止了！❌]
```

**问题：** 执行一个工具后就停止，没有继续分析

---

## ✅ 新的 Agent 循环

现在 CCP 实现了完整的 **ReAct 模式**（Reasoning + Acting）：

```
用户：分析这个项目
AI: 我来帮你分析这个项目...

🔧 Using tool: bash (ls -la)
   Result: total 508, drwxrwxr-x 8 admin...

🔧 Using tool: bash (find . -type f -name "*.py"...)
   Result: ./src/main.py, ./src/cli/entry.py...

🔧 Using tool: file_read (PHASE1_COMPLETE.md)
   Result: # 🎉 第一阶段完成报告...

🔧 Using tool: file_read (src/main.py)
   Result: """Main entry point for CCP"""...

[自主分析中...]

🔧 Using tool: grep (def main)
   Result: Found 3 matches...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Task completed

综合分析：
这个项目是 Claude Code 的 Python 实现，包含...
- 核心模块：src/core/, src/tools/, src/llm/
- 已完成第一阶段开发
- 代码量约 6000+ 行
...
```

**改进：** 自主执行多个工具 → 综合分析 → 输出完整报告

---

## 🔄 Agent 循环流程

```
┌─────────────────────────────────────────────────────────┐
│                    用户输入任务                          │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              调用 LLM（带工具定义）                      │
│         LLM 决定：回复文本 OR 调用工具                   │
└─────────────────────────────────────────────────────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
    【有文本回复】            【有工具调用】
    显示回复                  执行工具
              │                       │
              │                       ▼
              │            ┌──────────────────────┐
              │            │  执行工具 (bash 等)   │
              │            │  获取结果            │
              │            └──────────────────────┘
              │                       │
              │                       ▼
              │            将结果添加到消息历史
              │                       │
              └───────────┬───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  达到最大迭代次数？    │
              │  OR  LLM 无工具调用？   │
              └───────────────────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
             是                       否
              │                       │
              ▼                       │
    【输出最终答案】                  │
    【任务完成】                      │
              │                       │
              └───────────────────────┘
                          │
                          ▼
                  返回循环起点
```

---

## 📋 核心代码

### AgentLoop 类

```python
# src/core/agent.py
class AgentLoop:
    """Agent 自主执行循环"""
    
    def __init__(
        self,
        llm: LLMProvider,
        registry: ToolRegistry,
        context: ToolContext,
        max_iterations: int = 20,  # 最大迭代次数
    ):
        ...
    
    async def run(self, task: str) -> str:
        """执行完整的 Agent 循环"""
        messages = [Message(role="user", content=task)]
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            
            # 1. 调用 LLM
            response = await self.llm.chat(messages, tools=self.tools)
            
            # 2. 显示文本回复
            if response.text:
                click.echo(response.text)
            
            # 3. 没有工具调用 = 任务完成
            if not response.tool_calls:
                break
            
            # 4. 执行所有工具调用
            for tool_call in response.tool_calls:
                result = await self.registry.execute_tool(...)
                # 5. 将结果添加到消息历史
                messages.append(Message(role="user", content=result_text))
            
            # 6. 继续循环，让 LLM 基于结果继续分析
        
        return final_answer
```

---

## 🚀 使用示例

### 批处理模式

```bash
# 一次性任务，自动执行完整分析
ccp run "分析这个项目的代码结构"

# 创建完整项目
ccp run "创建一个 FastAPI 项目，包含用户认证和数据库"

# 代码重构
ccp run "重构 src/目录的代码，提高可读性"
```

### 交互模式

```bash
# 启动交互式 Agent
ccp run -i

You: 分析一下这个项目

Claude: [自主执行多个工具 → 输出完整分析报告]

You: 帮我创建一个测试文件

Claude: [自主创建文件 → 编写测试 → 运行验证]

You: exit
Goodbye!
```

---

## ⚙️ 配置选项

### 最大迭代次数

防止无限循环，默认 20 次：

```python
agent = AgentLoop(llm, registry, context, max_iterations=20)
```

### 工具截断

过长的工具结果会自动截断（2000 字符）：

```python
if len(result_text) > 2000:
    result_text = result_text[:2000] + "\n... (truncated)"
```

---

## 📊 对比

| 特性 | 之前 | 现在 |
|------|------|------|
| 工具执行 | 单次 | 自主多次 |
| 分析深度 | 浅层 | 深度分析 |
| 任务完成 | 需多轮对话 | 一次性完成 |
| 最大迭代 | 无限制 | 20 次（可配置） |
| 结果截断 | 无 | 2000 字符 |

---

## 🎯 典型用例

### 1. 项目分析

```bash
ccp run "分析这个项目的架构和代码质量"
```

**Agent 自主执行：**
1. `ls -la` - 查看目录结构
2. `find . -name "*.py"` - 查找所有 Python 文件
3. `cat README.md` - 阅读项目说明
4. `cat pyproject.toml` - 查看依赖配置
5. `grep -r "def main"` - 查找入口点
6. 综合分析 → 输出报告

### 2. 代码重构

```bash
ccp run "优化 src/tools/目录的代码结构"
```

**Agent 自主执行：**
1. 读取所有相关文件
2. 分析代码问题
3. 提出改进建议
4. 执行代码修改
5. 运行测试验证

### 3. 创建项目

```bash
ccp run "创建一个完整的 FastAPI 项目"
```

**Agent 自主执行：**
1. 创建目录结构
2. 编写所有源文件
3. 创建配置文件
4. 编写测试
5. 输出使用说明

---

## 🔧 调试

### 查看详细日志

```bash
# 启用详细日志
ccp run -v "分析项目"
```

### 日志输出

```
2026-04-03T10:20:00.000Z [info] Agent iteration iteration=1 max=20
2026-04-03T10:20:01.000Z [info] Tool execution requested tool=bash
2026-04-03T10:20:02.000Z [info] Agent completed iterations=5
```

---

## ⚠️ 注意事项

1. **最大迭代次数** - 达到 20 次会自动停止
2. **Token 消耗** - 多次工具调用会增加 Token 使用
3. **执行时间** - 复杂任务可能需要较长时间
4. **工具安全** - 危险命令仍需审批

---

## 📈 后续优化

- [ ] 支持自定义工具执行策略
- [ ] 添加任务进度显示
- [ ] 支持中断后恢复
- [ ] 工具调用并行化
- [ ] 成本预估和限制

---

*最后更新：2026-04-03*  
*作者：小佳 ✨*
