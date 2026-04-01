# AutoGen 架构深度分析

**分析日期：** 2026-03-26  
**版本：** AutoGen v0.4+ (Python)  
**目的：** 面试大模型应用开发准备 - 深入理解 AutoGen 架构设计

---

## 📋 目录

1. [整体架构概览](#整体架构概览)
2. [核心模块解析](#核心模块解析)
3. [消息系统设计](#消息系统设计)
4. [Agent 架构](#agent 架构)
5. [团队协作机制](#团队协作机制)
6. [MCP 集成架构](#mcp 集成架构)
7. [状态管理与持久化](#状态管理与持久化)
8. [设计模式总结](#设计模式总结)
9. [面试考点](#面试考点)

---

## 🏗️ 整体架构概览

### 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        AutoGen Ecosystem                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              AgentChat (高层对话框架)                     │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │   │
│  │  │  Agents    │  │   Teams    │  │   Tools    │         │   │
│  │  │ (智能体)    │  │  (团队编排) │  │  (工具集)  │         │   │
│  │  └────────────┘  └────────────┘  └────────────┘         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Core (核心运行时)                            │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │   │
│  │  │   Agent    │  │   Topic    │  │  Message   │         │   │
│  │  │  Runtime   │  │   System   │  │  Factory   │         │   │
│  │  └────────────┘  └────────────┘  └────────────┘         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Extensions (扩展层)                          │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │   │
│  │  │   Models   │  │   Tools    │  │   Memory   │         │   │
│  │  │ (模型客户端)│  │ (MCP/工具) │  │  (记忆)    │         │   │
│  │  └────────────┘  └────────────┘  └────────────┘         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 代码目录结构

```
autogen/
├── python/
│   ├── packages/
│   │   ├── autogen-agentchat/          # 高层对话框架
│   │   │   └── src/autogen_agentchat/
│   │   │       ├── agents/             # Agent 实现
│   │   │       │   ├── _assistant_agent.py
│   │   │       │   ├── _base_chat_agent.py
│   │   │       │   ├── _user_proxy_agent.py
│   │   │       │   └── _code_executor_agent.py
│   │   │       ├── base/               # 基础接口定义
│   │   │       │   ├── _chat_agent.py  # ChatAgent 协议
│   │   │       │   ├── _team.py        # Team 协议
│   │   │       │   ├── _task.py        # TaskRunner
│   │   │       │   └── _termination.py # 终止条件
│   │   │       ├── messages.py         # 消息类型定义
│   │   │       ├── teams/              # 团队编排
│   │   │       │   └── _group_chat/
│   │   │       │       ├── _base_group_chat.py
│   │   │       │       ├── _selector_group_chat.py
│   │   │       │       ├── _round_robin_group_chat.py
│   │   │       │       └── _swarm_group_chat.py
│   │   │       ├── tools/              # 工具系统
│   │   │       ├── state/              # 状态管理
│   │   │       └── ui/                 # 用户界面
│   │   │
│   │   └── autogen-ext/                # 扩展模块
│   │       └── src/autogen_ext/
│   │           ├── models/             # 模型客户端
│   │           │   ├── openai/
│   │           │   ├── anthropic/
│   │           │   └── azure/
│   │           ├── tools/              # 工具实现
│   │           │   ├── mcp/            # MCP 协议支持
│   │           │   └── http/
│   │           ├── memory/             # 记忆系统
│   │           └── code_executors/     # 代码执行器
│   │
│   └── samples/                        # 示例代码
```

---

## 🔧 核心模块解析

### 1. AgentChat 框架

**定位：** 高层对话 API，简化多 Agent 应用开发

**核心类：**

| 类名 | 文件 | 职责 |
|------|------|------|
| `ChatAgent` | `_chat_agent.py` | Agent 协议接口 |
| `AssistantAgent` | `_assistant_agent.py` | 助手 Agent 实现 |
| `BaseGroupChat` | `_base_group_chat.py` | 群聊基类 |
| `Team` | `_team.py` | 团队协议接口 |

**关键接口定义：**

```python
# ChatAgent 协议 (autogen_agentchat/base/_chat_agent.py)
class ChatAgent(ABC, TaskRunner, ComponentBase[BaseModel]):
    component_type = "agent"
    
    @property
    @abstractmethod
    def name(self) -> str:
        """唯一标识符"""
        ...
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Agent 描述，用于团队决策"""
        ...
    
    @property
    @abstractmethod
    def produced_message_types(self) -> Sequence[type[BaseChatMessage]]:
        """产生的消息类型"""
        ...
    
    @abstractmethod
    async def on_messages(
        self, 
        messages: Sequence[BaseChatMessage], 
        cancellation_token: CancellationToken
    ) -> Response:
        """处理消息并返回响应"""
        ...
    
    @abstractmethod
    def on_messages_stream(
        self, 
        messages: Sequence[BaseChatMessage], 
        cancellation_token: CancellationToken
    ) -> AsyncGenerator[BaseAgentEvent | BaseChatMessage | Response, None]:
        """流式处理消息"""
        ...
```

---

### 2. AssistantAgent 实现

**核心流程：**

```python
# autogen_agentchat/agents/_assistant_agent.py
class AssistantAgent(BaseChatAgent, Component[AssistantAgentConfig]):
    """
    核心工作流程：
    1. 接收消息 → 2. 调用 LLM → 3. 处理工具调用 → 4. 返回响应
    """
    
    async def on_messages(
        self, 
        messages: Sequence[BaseChatMessage], 
        cancellation_token: CancellationToken
    ) -> Response:
        # 1. 将消息添加到上下文
        await self._model_context.add_messages(messages)
        
        # 2. 调用 LLM
        response = await self._model_client.create(
            messages=await self._model_context.get_messages(),
            tools=self._tools,
            cancellation_token=cancellation_token
        )
        
        # 3. 处理工具调用
        if response.tool_calls:
            # 执行工具
            results = await self._execute_tool_calls(
                response.tool_calls, 
                cancellation_token
            )
            
            # 是否反思
            if self._reflect_on_tool_use:
                # 再次调用 LLM 反思
                ...
            else:
                # 直接返回工具结果
                return Response(
                    chat_message=ToolCallSummaryMessage(...)
                )
        
        # 4. 返回文本响应
        return Response(
            chat_message=TextMessage(content=response.content)
        )
```

**关键配置参数：**

```python
class AssistantAgentConfig(BaseModel):
    name: str                              # Agent 名称
    model_client: ComponentModel           # 模型客户端
    tools: List[ComponentModel] | None     # 工具列表
    workbench: List[ComponentModel] | None # 工作台 (MCP)
    handoffs: List[HandoffBase | str] | None  # 移交配置
    model_context: ComponentModel | None   # 上下文管理
    memory: List[ComponentModel] | None    # 记忆系统
    system_message: str | None             # 系统提示
    model_client_stream: bool              # 流式输出
    reflect_on_tool_use: bool              # 工具使用后反思
    max_tool_iterations: int = 1           # 最大工具迭代次数
```

---

## 💬 消息系统设计

### 消息类型层次结构

```
BaseMessage (ABC)
│
├── BaseChatMessage (ABC)          # Agent 间通信
│   ├── BaseTextChatMessage (ABC)
│   │   ├── TextMessage
│   │   ├── StopMessage
│   │   └── HandoffMessage
│   ├── StructuredMessage[T]       # 结构化输出
│   └── ToolCallSummaryMessage
│
└── BaseAgentEvent (ABC)           # 事件通知
    ├── ToolCallRequestEvent
    ├── ToolCallExecutionEvent
    ├── ToolCallResultEvent
    ├── ThoughtEvent
    ├── MemoryQueryEvent
    └── ModelClientStreamingChunkEvent
```

### 消息类实现

```python
# autogen_agentchat/messages.py
class BaseMessage(BaseModel, ABC):
    """所有消息类型的抽象基类"""
    
    @abstractmethod
    def to_text(self) -> str:
        """转换为字符串表示（用于控制台渲染）"""
        ...
    
    def dump(self) -> Mapping[str, Any]:
        """序列化为 JSON 字典"""
        return self.model_dump(mode="json")
    
    @classmethod
    def load(cls, data: Mapping[str, Any]) -> Self:
        """从字典反序列化"""
        return cls.model_validate(data)


class BaseChatMessage(BaseMessage, ABC):
    """Agent 间通信的消息基类"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str                          # 发送者
    models_usage: RequestUsage | None    # 模型使用统计
    metadata: Dict[str, str] = {}        # 元数据
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @abstractmethod
    def to_model_text(self) -> str:
        """转换为模型文本（用于 LLM 输入）"""
        ...
    
    @abstractmethod
    def to_model_message(self) -> UserMessage:
        """转换为模型消息对象"""
        ...


class TextMessage(BaseTextChatMessage):
    """普通文本消息"""
    content: str
    source: str


class HandoffMessage(BaseChatMessage):
    """Agent 移交消息"""
    content: str
    target: str                          # 目标 Agent
    context: Sequence[LLMMessage]        # 上下文传递


class StructuredMessage(BaseChatMessage, Generic[T]):
    """结构化消息（Pydantic 模型）"""
    content: T                           # Pydantic 模型
    content_type: str                    # 内容类型标识
```

---

## 🤖 Agent 架构

### Agent 继承层次

```
ComponentBase[BaseModel]
│
└── ChatAgent (ABC, TaskRunner)
    │
    └── BaseChatAgent
        │
        ├── AssistantAgent              # 助手 Agent
        ├── UserProxyAgent              # 用户代理
        ├── CodeExecutorAgent           # 代码执行 Agent
        ├── SocietyOfMindAgent          # 思维社会 Agent
        └── MessageFilterAgent          # 消息过滤 Agent
```

### BaseChatAgent 核心实现

```python
# autogen_agentchat/agents/_base_chat_agent.py
class BaseChatAgent(ChatAgent, ABC):
    """ChatAgent 的基础实现"""
    
    def __init__(self, name: str, description: str):
        self._name = name
        self._description = description
        self._message_history: List[BaseChatMessage] = []
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    async def run(
        self, 
        *, 
        task: str | None = None,
        cancellation_token: CancellationToken | None = None
    ) -> TaskResult:
        """运行任务并返回结果"""
        messages = [TextMessage(content=task, source="user")] if task else []
        response = await self.on_messages(messages, cancellation_token)
        return TaskResult(messages=[response.chat_message])
    
    async def run_stream(...) -> AsyncGenerator[...]:
        """流式运行任务"""
        ...
    
    @abstractmethod
    async def on_reset(self, cancellation_token: CancellationToken) -> None:
        """重置 Agent 状态"""
        ...
```

---

## 👥 团队协作机制

### 团队类型

```
Team (ABC)
│
└── BaseGroupChat (ABC)
    │
    ├── RoundRobinGroupChat          # 轮询模式
    ├── SelectorGroupChat            # 选择器模式 (LLM 选择)
    ├── SwarmGroupChat               # 群体模式
    └── MagenticOneGroupChat         # 磁控模式
```

### BaseGroupChat 核心设计

```python
# autogen_agentchat/teams/_group_chat/_base_group_chat.py
class BaseGroupChat(Team, ABC, ComponentBase[BaseModel]):
    """群聊团队的基类"""
    
    def __init__(
        self,
        name: str,
        description: str,
        participants: List[ChatAgent | Team],
        group_chat_manager_name: str,
        group_chat_manager_class: type[SequentialRoutedAgent],
        termination_condition: TerminationCondition | None = None,
        max_turns: int | None = None,
        runtime: AgentRuntime | None = None,
    ):
        self._name = name
        self._description = description
        self._participants = participants
        self._team_id = str(uuid.uuid4())  # 团队唯一标识
        
        # Topic 系统设计（基于发布/订阅）
        self._group_topic_type = f"group_topic_{self._team_id}"
        self._group_chat_manager_topic_type = f"{name}_{self._team_id}"
        self._participant_topic_types = [
            f"{p.name}_{self._team_id}" for p in participants
        ]
        self._output_topic_type = f"output_topic_{self._team_id}"
        
        # 输出消息队列
        self._output_message_queue: asyncio.Queue[...] = asyncio.Queue()
        
        # 运行时
        self._runtime = runtime or SingleThreadedAgentRuntime()
    
    async def _init(self, runtime: AgentRuntime) -> None:
        """初始化团队"""
        # 1. 注册 Group Chat Manager
        await self._group_chat_manager_class.register(
            runtime,
            self._group_chat_manager_topic_type,
            self._create_group_chat_manager_factory(...)
        )
        
        # 2. 注册参与者（使用 ChatAgentContainer 包装）
        for participant, agent_type in zip(
            self._participants, 
            self._participant_topic_types
        ):
            await ChatAgentContainer.register(
                runtime,
                agent_type,
                self._create_participant_factory(...)
            )
        
        # 3. 设置订阅关系
        for topic_type in self._participant_topic_types:
            await runtime.add_subscription(
                TypeSubscription(topic_type, self._group_topic_type)
            )
    
    async def run(
        self, 
        *, 
        task: str | None = None,
        cancellation_token: CancellationToken | None = None
    ) -> TaskResult:
        """运行团队任务"""
        # 1. 发送启动消息到 Group Topic
        await self._runtime.send_message(
            GroupChatStart(messages=[...]),
            recipient=AgentId(self._group_chat_manager_topic_type, self._team_id)
        )
        
        # 2. 从输出队列收集消息
        output_messages: List[BaseAgentEvent | BaseChatMessage] = []
        while True:
            message = await self._output_message_queue.get()
            if isinstance(message, GroupChatTermination):
                break
            output_messages.append(message)
        
        return TaskResult(messages=output_messages)
```

### SelectorGroupChat (LLM 选择下一个发言者)

```python
# autogen_agentchat/teams/_group_chat/_selector_group_chat.py
class SelectorGroupChatManager(BaseGroupChatManager):
    """使用 LLM 选择下一个发言者的群聊管理器"""
    
    def __init__(
        self,
        name: str,
        ...,
        model_client: ChatCompletionClient,      # 用于选择的 LLM
        selector_prompt: str,                     # 选择提示模板
        allow_repeated_speaker: bool,             # 是否允许重复发言
        selector_func: Optional[SelectorFuncType], # 自定义选择函数
        max_selector_attempts: int,               # 最大尝试次数
        candidate_func: Optional[CandidateFuncType], # 候选人生成函数
    ):
        self._model_client = model_client
        self._selector_prompt = selector_prompt
        self._previous_speaker: str | None = None
        self._model_context = UnboundedChatCompletionContext()
    
    async def select_speaker(
        self, 
        messages: Sequence[BaseAgentEvent | BaseChatMessage]
    ) -> str:
        """选择下一个发言者"""
        
        # 1. 构建选择提示
        participant_context = self._get_participant_context()
        conversation_history = self._get_conversation_history(messages)
        
        prompt = self._selector_prompt.format(
            participants=participant_context,
            history=conversation_history,
            previous_speaker=self._previous_speaker
        )
        
        # 2. 调用 LLM 选择
        response = await self._model_client.create(
            messages=[UserMessage(content=prompt, source="system")]
        )
        
        # 3. 解析选择结果
        selected_name = self._parse_speaker_name(response.content)
        
        # 4. 验证选择
        if selected_name not in self._participant_names:
            raise ValueError(f"Invalid speaker: {selected_name}")
        
        self._previous_speaker = selected_name
        return selected_name
```

### 通信流程

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Agent A    │     │ Group Chat Mgr   │     │  Agent B    │
│             │     │                  │     │             │
│  send msg   │────▶│  receive & eval  │────▶│  select B   │
│             │     │                  │     │             │
│             │◀────│  publish to B    │◀────│             │
│             │     │                  │     │             │
│  process    │     │  collect result  │     │  process    │
│             │     │                  │     │             │
└─────────────┘     └──────────────────┘     └─────────────┘
       │                    │                      │
       └────────────────────┴──────────────────────┘
                    │
              Output Queue
                    │
                    ▼
              TaskResult
```

---

## 🔌 MCP 集成架构

### MCP (Model Context Protocol) 支持

**文件结构：**

```
autogen_ext/tools/mcp/
├── _base.py           # MCP 工具基类
├── _actor.py          # MCP Actor 实现
├── _factory.py        # MCP 工厂
├── _stdio.py          # 标准输入/输出传输
├── _sse.py            # SSE 传输
├── _streamable_http.py # HTTP 流式传输
├── _workbench.py      # MCP Workbench
└── _host/
    ├── __init__.py
    └── _sampling.py   # 采样工具
```

### MCP Workbench 使用

```python
# 示例代码
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams

# 1. 定义 MCP 服务器参数
server_params = StdioServerParams(
    command="npx",
    args=["@playwright/mcp@latest", "--headless"]
)

# 2. 创建 Workbench
async with McpWorkbench(server_params) as mcp:
    # 3. 创建使用 MCP 的 Agent
    agent = AssistantAgent(
        "web_browsing_assistant",
        model_client=model_client,
        workbench=mcp,  # 使用 MCP Workbench
        max_tool_iterations=10
    )
    
    # 4. 运行任务
    await agent.run(task="查找 microsoft/autogen 的 contributor 数量")
```

### MCP Workbench 实现

```python
# autogen_ext/tools/mcp/_workbench.py
class McpWorkbench(Workbench, AsyncContextManager[..., Self]):
    """MCP Workbench - 管理 MCP 会话和工具"""
    
    def __init__(self, server_params: StdioServerParams | SseServerParams | ...):
        self._server_params = server_params
        self._session: McpSession | None = None
        self._tools: Dict[str, BaseTool] = {}
    
    async def __aenter__(self) -> Self:
        # 1. 创建 MCP 会话
        self._session = await McpSession.create(self._server_params)
        
        # 2. 获取可用工具列表
        tools_response = await self._session.list_tools()
        
        # 3. 将 MCP 工具转换为 AutoGen 工具
        for tool_def in tools_response.tools:
            auto_tool = self._convert_mcp_tool_to_autogen(tool_def)
            self._tools[tool_def.name] = auto_tool
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # 关闭会话
        if self._session:
            await self._session.close()
    
    def get_tools(self) -> Sequence[BaseTool]:
        """获取所有工具"""
        return list(self._tools.values())
    
    async def call_tool(
        self, 
        name: str, 
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """调用工具"""
        if not self._session:
            raise RuntimeError("Workbench not initialized")
        
        result = await self._session.call_tool(name, arguments)
        return self._convert_result(result)
```

---

## 💾 状态管理与持久化

### 状态保存/恢复接口

```python
# autogen_agentchat/base/_chat_agent.py
class ChatAgent(ABC, ...):
    @abstractmethod
    async def save_state(self) -> Mapping[str, Any]:
        """保存 Agent 状态"""
        ...
    
    @abstractmethod
    async def load_state(self, state: Mapping[str, Any]) -> None:
        """恢复 Agent 状态"""
        ...
```

### AssistantAgent 状态实现

```python
# autogen_agentchat/state/_assistant_agent.py
class AssistantAgentState(BaseModel):
    """AssistantAgent 的状态"""
    model_context: Mapping[str, Any]
    current_turn: int


# autogen_agentchat/agents/_assistant_agent.py
class AssistantAgent(...):
    async def save_state(self) -> Mapping[str, Any]:
        state = AssistantAgentState(
            model_context=await self._model_context.save_state(),
            current_turn=self._current_turn
        )
        return state.model_dump()
    
    async def load_state(self, state: Mapping[str, Any]) -> None:
        assistant_state = AssistantAgentState.model_validate(state)
        await self._model_context.load_state(
            assistant_state.model_context
        )
        self._current_turn = assistant_state.current_turn
```

### GroupChat 状态管理

```python
# autogen_agentchat/state/_team_state.py
class TeamState(BaseModel):
    """团队状态"""
    name: str
    participant_states: Dict[str, Mapping[str, Any]]
    message_thread: List[Mapping[str, Any]]
    current_turn: int


# autogen_agentchat/teams/_group_chat/_base_group_chat.py
class BaseGroupChat(...):
    async def save_state(self) -> Mapping[str, Any]:
        # 1. 保存 Group Chat Manager 状态
        manager_state = await self._get_manager_state()
        
        # 2. 保存所有参与者状态
        participant_states = {}
        for participant in self._participants:
            participant_states[participant.name] = (
                await participant.save_state()
            )
        
        return TeamState(
            name=self._name,
            participant_states=participant_states,
            message_thread=manager_state.get("message_thread", []),
            current_turn=manager_state.get("current_turn", 0)
        ).model_dump()
```

---

## 🎨 设计模式总结

### 1. 协议/接口分离模式

```python
# 定义协议
class ChatAgent(ABC, ...):
    """协议接口"""
    ...

# 提供基础实现
class BaseChatAgent(ChatAgent, ...):
    """基础实现，减少重复代码"""
    ...

# 具体实现
class AssistantAgent(BaseChatAgent, ...):
    """助手 Agent"""
    ...
```

**优点：**
- 清晰的接口定义
- 代码复用
- 易于扩展

---

### 2. 组件模式 (Component Pattern)

```python
class ComponentBase(Generic[T], ABC):
    """组件基类"""
    component_type: str
    
    @classmethod
    def from_config(cls, config: T) -> Self:
        """从配置创建组件"""
        ...
    
    def dump_component(self) -> ComponentModel:
        """导出组件模型"""
        ...
```

**应用：**
- Agent 可序列化/反序列化
- 支持配置驱动创建
- 便于持久化

---

### 3. 发布/订阅模式 (Pub/Sub)

```python
# Topic 系统
self._group_topic_type = f"group_topic_{self._team_id}"
self._participant_topic_types = [...]

# 订阅关系
await runtime.add_subscription(
    TypeSubscription(topic_type, self._group_topic_type)
)

# 发布消息
await runtime.send_message(message, recipient=AgentId(topic_type, id))
```

**优点：**
- 松耦合通信
- 支持广播
- 易于扩展

---

### 4. 工厂模式 (Factory Pattern)

```python
def _create_group_chat_manager_factory(...) -> Callable[[], SequentialRoutedAgent]:
    """创建 Group Chat Manager 工厂"""
    def factory() -> SequentialRoutedAgent:
        return SelectorGroupChatManager(
            name=...,
            group_topic_type=...,
            ...
        )
    return factory

# 注册时使用工厂
await ChatAgentContainer.register(
    runtime,
    agent_type,
    factory  # 传入工厂函数
)
```

**优点：**
- 延迟初始化
- 依赖注入
- 便于测试

---

### 5. 策略模式 (Strategy Pattern)

```python
# 不同的群聊策略
class RoundRobinGroupChat(BaseGroupChat):
    """轮询策略"""
    def _create_group_chat_manager_factory(...):
        ...

class SelectorGroupChat(BaseGroupChat):
    """LLM 选择策略"""
    def _create_group_chat_manager_factory(...):
        ...

class SwarmGroupChat(BaseGroupChat):
    """群体策略"""
    def _create_group_chat_manager_factory(...):
        ...
```

**优点：**
- 算法可互换
- 符合开闭原则
- 易于添加新策略

---

### 6. 装饰器/包装模式 (Decorator/Wrapper Pattern)

```python
class ChatAgentContainer:
    """包装 ChatAgent，添加运行时功能"""
    
    def __init__(
        self,
        parent_topic_type: str,
        output_topic_type: str,
        agent: ChatAgent,  # 被包装的 Agent
        message_factory: MessageFactory
    ):
        self._agent = agent
        self._parent_topic_type = parent_topic_type
        self._output_topic_type = output_topic_type
    
    async def on_message(self, message: ...):
        # 1. 预处理（日志、验证等）
        ...
        
        # 2. 委托给被包装的 Agent
        response = await self._agent.on_messages(...)
        
        # 3. 后处理（发布到输出 Topic）
        ...
```

**优点：**
- 职责分离
- 功能组合灵活
- 不修改原有代码

---

## 🎯 面试考点

### 1. 多 Agent 通信机制

**问题：** "AutoGen 中 Agent 之间如何通信？"

**回答要点：**
- 基于 Topic 的发布/订阅系统
- Group Chat Manager 协调通信
- 消息类型系统（BaseChatMessage / BaseAgentEvent）
- 支持同步和异步通信

**代码示例：**
```python
# 发布消息
await runtime.send_message(
    TextMessage(content="Hello", source="A"),
    recipient=AgentId("B_team", "123")
)

# 订阅消息
await runtime.add_subscription(
    TypeSubscription("topic_A", "group_topic")
)
```

---

### 2. 状态管理设计

**问题：** "如何实现 Agent 状态的保存和恢复？"

**回答要点：**
- Pydantic 模型序列化
- 分层状态管理（Agent/Team）
- 上下文持久化
- 支持中断恢复

**代码示例：**
```python
async def save_state(self) -> Mapping[str, Any]:
    return AssistantAgentState(
        model_context=await self._model_context.save_state(),
        current_turn=self._current_turn
    ).model_dump()

async def load_state(self, state: Mapping[str, Any]) -> None:
    assistant_state = AssistantAgentState.model_validate(state)
    await self._model_context.load_state(assistant_state.model_context)
```

---

### 3. 工具调用流程

**问题：** "AutoGen 如何处理工具调用？"

**回答要点：**
1. LLM 返回 tool_calls
2. 并行/串行执行工具
3. 可选反思（reflect_on_tool_use）
4. 返回结果或再次调用 LLM

**流程图：**
```
LLM Response (with tool_calls)
         │
         ▼
   Execute Tools (parallel)
         │
         ▼
   reflect_on_tool_use?
    ┌────┴────┐
    │         │
   Yes       No
    │         │
    ▼         ▼
LLM Again  Return Result
```

---

### 4. MCP 协议理解

**问题：** "什么是 MCP？AutoGen 如何集成 MCP？"

**回答要点：**
- MCP = Model Context Protocol
- 标准化的工具协议
- 支持多种传输（stdio/SSE/HTTP）
- Workbench 抽象层

**代码示例：**
```python
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams

server_params = StdioServerParams(command="npx", args=["@playwright/mcp@latest"])
async with McpWorkbench(server_params) as mcp:
    agent = AssistantAgent("assistant", workbench=mcp)
```

---

### 5. 系统设计题

**题目：** "设计一个多 Agent 代码审查系统"

**参考方案：**

```python
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination

# 1. 定义角色
coder = AssistantAgent(
    "coder",
    system_message="你是资深程序员，负责编写代码",
    model_client=model_client
)

reviewer = AssistantAgent(
    "reviewer", 
    system_message="你是代码审查专家，负责审查代码质量",
    model_client=model_client
)

tester = AssistantAgent(
    "tester",
    system_message="你是测试专家，负责编写和运行测试",
    model_client=model_client
)

# 2. 定义终止条件
termination = TextMentionTermination("LGTM")  # 审查通过

# 3. 创建团队
team = RoundRobinGroupChat(
    [coder, reviewer, tester],
    termination_condition=termination,
    max_turns=10
)

# 4. 运行任务
await team.run(task="实现一个快速排序算法")
```

---

## 📚 总结

### AutoGen 架构特点

| 特点 | 实现方式 | 价值 |
|------|----------|------|
| **分层设计** | AgentChat / Core / Extensions | 清晰的职责划分 |
| **协议驱动** | ABC + Protocol | 易于扩展和测试 |
| **消息系统** | Pydantic 模型 + 类型系统 | 类型安全、可序列化 |
| **团队协作** | Pub/Sub + Group Chat Manager | 灵活的协作模式 |
| **状态管理** | save_state/load_state | 支持中断恢复 |
| **工具集成** | MCP + Workbench | 标准化、可扩展 |

### 学习建议

1. **阅读核心源码：**
   - `_assistant_agent.py` - 理解 Agent 实现
   - `_base_group_chat.py` - 理解团队协作
   - `messages.py` - 理解消息系统

2. **实践项目：**
   - 实现自定义 Agent
   - 创建自定义 Team 策略
   - 集成 MCP 工具

3. **深入理解：**
   - 发布/订阅模式
   - 状态管理设计
   - 异步编程模式

---

**祝面试顺利！** 🎉
