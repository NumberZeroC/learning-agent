# 🐛 Bug 修复报告

**日期：** 2026-04-03  
**问题：** Message 对象缺少 tool_calls 属性  
**状态：** ✅ 已修复

---

## 📋 问题描述

用户在运行 CCP 时遇到错误：

```
AttributeError: 'Message' object has no attribute 'tool_calls'
```

**错误位置：** `src/core/agent.py` 中访问 `response.tool_calls`

**原因：** `Message` 基类没有定义 `tool_calls` 属性

---

## ✅ 修复方案

### 1. 新增 ToolCall 类型

```python
# src/types/messages.py
class ToolCall(BaseModel):
    """Tool call definition"""
    
    id: str
    name: str
    input: dict[str, Any]
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
```

### 2. 更新 Message 类

```python
class Message(BaseModel):
    """Base message class"""
    
    role: Literal["user", "assistant", "system"]
    content: str | None = None  # 改为可选
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)
    tool_calls: list[ToolCall] | None = None  # 新增属性
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
```

---

## 🧪 测试验证

```bash
$ .venv/bin/python -c "
from src.types.messages import Message, ToolCall

# 测试普通消息
m1 = Message(role='user', content='test')
print(f'tool_calls={m1.tool_calls}')  # None

# 测试带工具调用的消息
tc = ToolCall(id='call_1', name='web_search', input={'query': 'test'})
m2 = Message(role='assistant', tool_calls=[tc])
print(f'tool_calls={m2.tool_calls}')  # [ToolCall(...)]
"

✓ 普通消息：tool_calls=None
✓ 工具调用消息：tool_calls=[ToolCall(id='call_1', name='web_search', input={'query': 'test'})]

✅ Message 类型修复成功！
```

---

## 📝 修改文件

| 文件 | 修改内容 |
|------|----------|
| `src/types/messages.py` | 新增 ToolCall 类，Message 添加 tool_calls 属性 |

---

## ✅ 验证通过

- [x] Message 类可以正常创建（无 tool_calls）
- [x] Message 类支持 tool_calls 属性
- [x] ToolCall 类型正确定义
- [x] 兼容原有代码

---

*修复时间：2026-04-03*  
*修复人：小佳 ✨*  
*状态：✅ 完成*
