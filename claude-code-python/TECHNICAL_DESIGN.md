# Claude Code Python 版 - 技术设计文档

**版本：** v0.1  
**日期：** 2026-04-02  
**作者：** 小佳 ✨

---

## 📋 目录

1. [项目概述](#1-项目概述)
2. [架构设计](#2-架构设计)
3. [技术选型](#3-技术选型)
4. [核心模块设计](#4-核心模块设计)
5. [接口设计](#5-接口设计)
6. [数据结构](#6-数据结构)
7. [实现计划](#7-实现计划)
8. [风险评估](#8-风险评估)

---

## 1. 项目概述

### 1.1 项目目标

用 Python 重写 Claude Code CLI，实现：
- ✅ 终端交互式 AI 编程助手
- ✅ 文件读写/编辑能力
- ✅ 命令执行与安全控制
- ✅ 代码搜索与理解
- ✅ MCP/LSP 协议支持
- ✅ 多 Agent 协作

### 1.2 设计原则

| 原则 | 说明 |
|------|------|
| **Pythonic** | 遵循 Python 最佳实践，非 TS 直译 |
| **模块化** | 高内聚低耦合，便于测试和扩展 |
| **异步优先** | 基于 asyncio，支持并发操作 |
| **安全默认** | 权限审批、沙箱执行、操作审计 |
| **可观测性** | 完整日志、指标追踪、调试支持 |

### 1.3 功能范围 (MVP)

**第一阶段 (核心功能):**
- [ ] 终端 UI 框架
- [ ] Bash 工具（命令执行）
- [ ] 文件工具（读/写/编辑）
- [ ] 搜索工具（Grep/Glob）
- [ ] 权限审批系统

**第二阶段 (增强功能):**
- [ ] MCP 协议客户端
- [ ] LSP 语言服务器
- [ ] Git 集成
- [ ] 多 Agent 协作

**第三阶段 (高级功能):**
- [ ] 计划模式 (Plan Mode)
- [ ] 远程会话
- [ ] 技能系统
- [ ] 语音交互

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Entry Point                        │
│                         (main.py)                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Application Core                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Session   │  │   Context   │  │    State Manager    │  │
│  │  Manager    │  │   Manager   │  │  (Memory/History)   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│   Tool System    │ │  Command System  │ │    UI Layer      │
│  ┌────────────┐  │ │  ┌────────────┐  │ │  ┌────────────┐  │
│  │ BashTool   │  │ │  │ Interactive│  │ │  │  Textual   │  │
│  │ FileTool   │  │ │  │ Batch      │  │ │  │  (TUI)     │  │
│  │ GrepTool   │  │ │  │ Plan Mode  │  │ │  │            │  │
│  │ MCPTool    │  │ │  │            │  │ │  └────────────┘  │
│  └────────────┘  │ │  └────────────┘  │ │                  │
└──────────────────┘ └──────────────────┘ └──────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                          │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌────────────┐  │
│  │   LSP     │ │    MCP    │ │    Git    │ │   HTTP     │  │
│  │  Service  │ │  Service  │ │  Service  │ │   Client   │  │
│  └───────────┘ └───────────┘ └───────────┘ └────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      External APIs                          │
│         Anthropic API │ LLM Providers │ File System         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
claude-code-python/
├── pyproject.toml              # 项目配置和依赖
├── README.md
├── TECHNICAL_DESIGN.md         # 本文档
│
├── src/
│   ├── __init__.py
│   ├── main.py                 # 入口点
│   │
│   ├── cli/                    # CLI 相关
│   │   ├── __init__.py
│   │   ├── entry.py            # 启动逻辑
│   │   ├── args.py             # 参数解析
│   │   └── completion.py       # Shell 自动补全
│   │
│   ├── core/                   # 核心逻辑
│   │   ├── __init__.py
│   │   ├── session.py          # 会话管理
│   │   ├── context.py          # 上下文管理
│   │   ├── state.py            # 状态管理
│   │   └── cost.py             # 成本追踪
│   │
│   ├── tools/                  # 工具系统
│   │   ├── __init__.py
│   │   ├── base.py             # 工具基类
│   │   ├── registry.py         # 工具注册表
│   │   ├── bash.py             # Bash 工具
│   │   ├── file_read.py        # 文件读取
│   │   ├── file_edit.py        # 文件编辑
│   │   ├── grep.py             # 代码搜索
│   │   ├── glob.py             # 文件匹配
│   │   ├── mcp.py              # MCP 协议
│   │   └── lsp.py              # LSP 服务
│   │
│   ├── commands/               # 命令系统
│   │   ├── __init__.py
│   │   ├── base.py             # 命令基类
│   │   ├── interactive.py      # 交互命令
│   │   ├── plan.py             # 计划模式
│   │   └── builtin.py          # 内置命令
│   │
│   ├── ui/                     # 终端 UI
│   │   ├── __init__.py
│   │   ├── app.py              # Textual 应用
│   │   ├── components/         # UI 组件
│   │   │   ├── __init__.py
│   │   │   ├── chat.py         # 聊天窗口
│   │   │   ├── tool_output.py  # 工具输出
│   │   │   ├── permissions.py  # 权限对话框
│   │   │   └── progress.py     # 进度显示
│   │   └── themes/             # 主题
│   │
│   ├── services/               # 服务层
│   │   ├── __init__.py
│   │   ├── mcp/                # MCP 服务
│   │   ├── lsp/                # LSP 服务
│   │   ├── git.py              # Git 服务
│   │   └── http.py             # HTTP 客户端
│   │
│   ├── llm/                    # LLM 抽象层
│   │   ├── __init__.py
│   │   ├── base.py             # LLM 基类
│   │   ├── anthropic.py        # Anthropic 实现
│   │   ├── openai.py           # OpenAI 实现
│   │   └── local.py            # 本地模型
│   │
│   ├── permissions/            # 权限系统
│   │   ├── __init__.py
│   │   ├── engine.py           # 权限引擎
│   │   ├── policies.py         # 策略定义
│   │   └── approval.py         # 审批流程
│   │
│   ├── utils/                  # 工具函数
│   │   ├── __init__.py
│   │   ├── async_utils.py
│   │   ├── file_utils.py
│   │   ├── path_utils.py
│   │   └── logging.py
│   │
│   └── types/                  # 类型定义
│       ├── __init__.py
│       ├── messages.py         # 消息类型
│       ├── tools.py            # 工具类型
│       └── permissions.py      # 权限类型
│
├── tests/                      # 测试
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── scripts/                    # 脚本
│   ├── build.py
│   └── release.py
│
└── docs/                       # 文档
    ├── api/
    ├── guides/
    └── architecture/
```

---

## 3. 技术选型

### 3.1 核心依赖

| 类别 | 库 | 版本 | 用途 |
|------|-----|------|------|
| **TUI 框架** | textual | ^0.50.0 | 终端 UI (替代 React Ink) |
| **异步** | asyncio | builtin | 异步运行时 |
| **HTTP** | httpx | ^0.27.0 | 异步 HTTP 客户端 |
| **CLI** | click | ^8.1.0 | 命令行参数解析 |
| **配置** | pydantic | ^2.6.0 | 配置验证和序列化 |
| **日志** | structlog | ^24.1.0 | 结构化日志 |

### 3.2 可选依赖

| 类别 | 库 | 用途 |
|------|-----|------|
| **进程管理** | asyncio-subprocess | 命令执行 |
| **文件监控** | watchdog | 文件系统事件 |
| **Git 操作** | GitPython | Git 集成 |
| **LSP 客户端** | pylsp-client | 语言服务器协议 |
| **MCP 客户端** | (自研) | Model Context Protocol |

### 3.3 Python 版本要求

```python
# pyproject.toml
[project]
requires-python = ">=3.11"
# 3.11+ 原因：
# - asyncio 性能改进
# - 更好的类型提示
# - exception groups 支持
```

---

## 4. 核心模块设计

### 4.1 工具系统

#### 4.1.1 工具基类

```python
# src/tools/base.py
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T')

class ToolInput(BaseModel):
    """工具输入基类"""
    pass

class ToolResult(BaseModel):
    """工具结果基类"""
    content: list[Any]
    is_error: bool = False

class Tool(ABC, Generic[T]):
    """工具基类"""
    
    name: str
    description: str
    input_schema: type[T]
    
    @abstractmethod
    async def execute(self, input: T, context: ToolContext) -> ToolResult:
        """执行工具"""
        pass
    
    @abstractmethod
    def get_prompt(self) -> str:
        """获取工具提示词"""
        pass
    
    async def validate(self, input: T, context: ToolContext) -> ValidationResult:
        """验证输入（可选）"""
        return ValidationResult(valid=True)
```

#### 4.1.2 Bash 工具

```python
# src/tools/bash.py
class BashInput(ToolInput):
    command: str
    description: str
    timeout: int | None = None
    workdir: str | None = None

class BashTool(Tool[BashInput]):
    name = "bash"
    description = "Execute shell commands"
    
    async def execute(self, input: BashInput, context: ToolContext) -> ToolResult:
        # 1. 安全验证
        validation = await self._validate_command(input.command)
        if not validation.valid:
            return ToolResult(content=[validation.error], is_error=True)
        
        # 2. 权限检查
        if not await context.permissions.approve(
            action="execute",
            resource=input.command,
            reason=input.description
        ):
            return ToolResult(content=["Permission denied"], is_error=True)
        
        # 3. 执行命令
        try:
            process = await asyncio.create_subprocess_shell(
                input.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=input.workdir
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=input.timeout
            )
            
            return ToolResult(content=[
                {"type": "text", "text": stdout.decode()},
                {"type": "text", "text": stderr.decode(), "style": "dim"}
            ])
        except asyncio.TimeoutError:
            return ToolResult(content=["Command timed out"], is_error=True)
```

#### 4.1.3 文件编辑工具

```python
# src/tools/file_edit.py
class FileEditInput(ToolInput):
    file_path: str
    old_text: str | None = None
    new_text: str
    edit_type: Literal["replace", "insert", "delete"] = "replace"

class FileEditTool(Tool[FileEditInput]):
    name = "file_edit"
    description = "Edit files with fine-grained control"
    
    async def execute(self, input: FileEditInput, context: ToolContext) -> ToolResult:
        # 1. 读取原文件
        try:
            with open(input.file_path, 'r') as f:
                original_content = f.read()
        except FileNotFoundError:
            return ToolResult(content=["File not found"], is_error=True)
        
        # 2. 权限检查
        if not await context.permissions.approve(
            action="write",
            resource=input.file_path,
            reason="File edit operation"
        ):
            return ToolResult(content=["Permission denied"], is_error=True)
        
        # 3. 执行编辑
        if input.edit_type == "replace" and input.old_text:
            if input.old_text not in original_content:
                return ToolResult(content=["Old text not found in file"], is_error=True)
            new_content = original_content.replace(input.old_text, input.new_text, 1)
        else:
            # 其他编辑类型...
            pass
        
        # 4. 写入文件
        with open(input.file_path, 'w') as f:
            f.write(new_content)
        
        # 5. 生成 diff
        diff = self._generate_diff(original_content, new_content)
        
        return ToolResult(content=[
            {"type": "diff", "diff": diff},
            {"type": "text", "text": f"Successfully edited {input.file_path}"}
        ])
```

### 4.2 命令系统

```python
# src/commands/base.py
class Command(ABC):
    """命令基类"""
    
    name: str
    aliases: list[str] = []
    description: str
    
    @abstractmethod
    async def execute(self, args: list[str], context: CommandContext) -> CommandResult:
        pass

# src/commands/interactive.py
class InteractiveCommand(Command):
    """交互式命令（默认模式）"""
    name = "interactive"
    
    async def execute(self, args: list[str], context: CommandContext) -> CommandResult:
        # 启动交互式会话
        session = await context.session_manager.create()
        await session.run_interactive()

# src/commands/plan.py
class PlanCommand(Command):
    """计划模式命令"""
    name = "plan"
    
    async def execute(self, args: list[str], context: CommandContext) -> CommandResult:
        # 进入计划模式
        plan = await context.planner.create_plan(context.user_input)
        await context.ui.display_plan(plan)
        
        # 等待用户确认
        if await context.ui.confirm("Execute this plan?"):
            await plan.execute()
```

### 4.3 权限系统

```python
# src/permissions/engine.py
class PermissionEngine:
    """权限引擎"""
    
    def __init__(self, config: PermissionConfig):
        self.config = config
        self.policies: list[Policy] = []
        self.denial_tracker = DenialTracker()
    
    async def check(
        self,
        action: str,
        resource: str,
        context: PermissionContext
    ) -> PermissionResult:
        """检查权限"""
        
        # 1. 检查自动允许策略
        for policy in self.policies:
            if policy.matches(action, resource) and policy.auto_allow:
                return PermissionResult(granted=True, reason="Policy auto-allow")
        
        # 2. 检查自动拒绝策略
        for policy in self.policies:
            if policy.matches(action, resource) and policy.auto_deny:
                return PermissionResult(granted=False, reason="Policy auto-deny")
        
        # 3. 检查危险命令
        if self._is_dangerous(action, resource):
            return PermissionResult(
                granted=False,
                requires_approval=True,
                reason="Dangerous operation"
            )
        
        # 4. 根据模式决定
        if context.mode == PermissionMode.ALWAYS_ASK:
            return PermissionResult(requires_approval=True)
        elif context.mode == PermissionMode.AUTO_EDIT:
            if action == "file_edit":
                return PermissionResult(granted=True)
        
        return PermissionResult(granted=True)

# src/permissions/policies.py
class Policy(BaseModel):
    name: str
    pattern: str  # glob 或 regex 模式
    actions: list[str]
    auto_allow: bool = False
    auto_deny: bool = False
```

### 4.4 终端 UI (Textual)

```python
# src/ui/app.py
from textual.app import App
from textual.widgets import Header, Footer, Input, Static

class ClaudeCodeApp(App):
    """主应用"""
    
    CSS = """
    ChatBox {
        height: 1fr;
        border: solid green;
    }
    
    ToolOutput {
        height: auto;
        border: solid blue;
    }
    
    InputBox {
        dock: bottom;
        height: 3;
    }
    """
    
    def compose(self):
        yield Header()
        yield ChatBox(id="chat")
        yield ToolOutput(id="tool-output")
        yield InputBox(id="input")
        yield Footer()
    
    async def on_input_submitted(self, event: Input.Submitted):
        """处理用户输入"""
        user_input = event.value
        event.input.value = ""
        
        # 发送到 LLM
        await self.process_user_input(user_input)

# src/ui/components/chat.py
class ChatBox(Static):
    """聊天窗口组件"""
    
    def __init__(self):
        super().__init__()
        self.messages: list[Message] = []
    
    def add_message(self, message: Message):
        """添加消息"""
        self.messages.append(message)
        self.update_display()
    
    def update_display(self):
        """更新显示"""
        content = "\n\n".join([
            self._render_message(m) for m in self.messages
        ])
        self.update(content)
```

### 4.5 LLM 抽象层

```python
# src/llm/base.py
class LLMProvider(ABC):
    """LLM 提供者基类"""
    
    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition],
        config: LLMConfig
    ) -> LLMResponse:
        pass

# src/llm/anthropic.py
class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model
        self.client = AsyncAnthropic(api_key=api_key)
    
    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition],
        config: LLMConfig
    ) -> LLMResponse:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=config.max_tokens,
            messages=messages,
            tools=tools
        )
        return self._parse_response(response)

# src/llm/local.py
class LocalLLMProvider(LLMProvider):
    """本地模型支持 (Ollama/vLLM)"""
    
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model
    
    async def chat(...) -> LLMResponse:
        # 调用本地模型 API
        pass
```

---

## 5. 接口设计

### 5.1 消息类型

```python
# src/types/messages.py
class Message(BaseModel):
    """消息基类"""
    role: Literal["user", "assistant", "system"]
    content: str

class ToolUseMessage(Message):
    """工具调用消息"""
    role: Literal["assistant"] = "assistant"
    tool_use_id: str
    name: str
    input: dict[str, Any]

class ToolResultMessage(Message):
    """工具结果消息"""
    role: Literal["user"] = "user"
    tool_use_id: str
    content: list[ContentBlock]

class ContentBlock(BaseModel):
    type: Literal["text", "image", "diff"]
    text: str | None = None
    data: bytes | None = None
```

### 5.2 工具定义

```python
# src/types/tools.py
class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]  # JSON Schema

# 示例：Bash 工具定义
BASH_TOOL = ToolDefinition(
    name="bash",
    description="Execute shell commands safely",
    input_schema={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The command to execute"
            },
            "description": {
                "type": "string",
                "description": "Why this command is needed"
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds"
            }
        },
        "required": ["command", "description"]
    }
)
```

### 5.3 CLI 接口

```python
# src/cli/entry.py
import click

@click.group()
@click.option('--model', '-m', default='claude-sonnet-4-20250514')
@click.option('--config', '-c', type=click.Path())
@click.pass_context
def cli(ctx, model, config):
    """Claude Code Python CLI"""
    ctx.ensure_object(dict)
    ctx.obj['model'] = model
    ctx.obj['config'] = load_config(config)

@cli.command()
@click.argument('task', required=False)
@click.option('--interactive', '-i', is_flag=True)
@click.pass_context
def run(ctx, task, interactive):
    """Run a task"""
    if interactive or not task:
        run_interactive(ctx.obj)
    else:
        run_batch(task, ctx.obj)

@cli.command()
@click.pass_context
def config(ctx):
    """Interactive configuration"""
    configure_interactive()

if __name__ == '__main__':
    cli()
```

---

## 6. 数据结构

### 6.1 会话状态

```python
# src/core/state.py
class SessionState(BaseModel):
    """会话状态"""
    id: str
    created_at: datetime
    updated_at: datetime
    messages: list[Message]
    tool_history: list[ToolCall]
    working_directory: str
    permission_mode: PermissionMode
    cost: CostTracker
    
class CostTracker(BaseModel):
    """成本追踪"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_cost: float = 0.0
    
    def add(self, usage: Usage):
        self.input_tokens += usage.input_tokens
        self.output_tokens += usage.output_tokens
        self.total_cost += usage.cost
```

### 6.2 工具调用历史

```python
# src/types/tools.py
class ToolCall(BaseModel):
    id: str
    name: str
    input: dict[str, Any]
    result: ToolResult | None
    status: Literal["pending", "completed", "failed", "cancelled"]
    started_at: datetime | None
    completed_at: datetime | None
```

---

## 7. 实现计划

### 7.1 第一阶段：核心框架 (Day 1-7)

| 天 | 任务 | 交付物 |
|----|------|--------|
| 1 | 项目初始化 + 基础架构 | 目录结构、依赖配置 |
| 2 | LLM 抽象层 | Anthropic 集成 |
| 3 | 工具系统基类 | Tool 基类、注册表 |
| 4 | Bash 工具 | 命令执行 + 安全 |
| 5 | 文件工具 | 读/写/编辑 |
| 6 | 终端 UI 框架 | Textual 基础组件 |
| 7 | 集成测试 | 端到端测试 |

### 7.2 第二阶段：增强功能 (Day 8-14)

| 天 | 任务 | 交付物 |
|----|------|--------|
| 8 | 搜索工具 | Grep/Glob |
| 9 | 权限系统 | 策略引擎 + 审批 |
| 10 | 命令系统 | 交互/批处理模式 |
| 11 | 会话管理 | 历史/恢复 |
| 12 | MCP 协议 | MCP 客户端 |
| 13 | LSP 集成 | 语言服务器 |
| 14 | 性能优化 | 缓存/并发 |

### 7.3 第三阶段：完善发布 (Day 15-21)

| 天 | 任务 | 交付物 |
|----|------|--------|
| 15-16 | Git 集成 | commit/push/PR |
| 17 | 多 Agent 协作 | Agent 调度 |
| 18 | 计划模式 | Plan Mode UI |
| 19 | 文档 | API 文档 + 指南 |
| 20 | 全面测试 | 单元测试 + E2E |
| 21 | 发布准备 | PyPI 打包 |

---

## 8. 风险评估

### 8.1 技术风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| Textual 功能不足 | 中 | 高 | 准备备用方案 (Rich) |
| asyncio 复杂性 | 高 | 中 | 充分测试 + 超时处理 |
| LSP 协议复杂 | 中 | 中 | 使用现有客户端库 |
| MCP 协议变化 | 低 | 高 | 保持协议抽象层 |

### 8.2 项目风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 范围蔓延 | 高 | 高 | 严格 MVP 范围 |
| 依赖问题 | 中 | 中 | 锁定版本 + 镜像 |
| 测试不足 | 中 | 高 | TDD + CI/CD |

### 8.3 法律风险

⚠️ **重要提示：**
- 本项目的目的是**学习和研究**
- 不应直接分发 Anthropic 专有代码
- 实现应基于公开接口，而非内部实现细节
- 建议命名为不同的产品名称

---

## 附录

### A. 关键依赖版本

```toml
# pyproject.toml
[project]
dependencies = [
    "textual>=0.50.0",
    "httpx>=0.27.0",
    "click>=8.1.0",
    "pydantic>=2.6.0",
    "structlog>=24.1.0",
    "anthropic>=0.25.0",
    "GitPython>=3.1.0",
    "watchdog>=4.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.0.0",
]
```

### B. 参考资源

- [Textual 文档](https://textual.textualize.io/)
- [Anthropic API 文档](https://docs.anthropic.com/)
- [MCP 协议规范](https://modelcontextprotocol.io/)
- [LSP 规范](https://microsoft.github.io/language-server-protocol/)

---

*文档版本：v0.1 | 最后更新：2026-04-02*
