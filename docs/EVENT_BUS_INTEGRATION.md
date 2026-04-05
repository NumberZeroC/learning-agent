# 事件总线集成指南

**文档版本：** 1.0  
**更新日期：** 2026-04-05  
**状态：** ✅ 已完成集成

---

## 📢 概述

事件总线（Event Bus）已集成到 learning-agent 的核心模块，实现模块间解耦和实时通知。

### 集成模块

| 模块 | 事件类型 | 状态 |
|------|---------|------|
| `llm_client.py` | LLM_CALL_START/COMPLETE/ERROR | ✅ 已集成 |
| `workflow_orchestrator.py` | WORKFLOW_START/PROGRESS/COMPLETE | ✅ 已集成 |
| `ask_service.py` | （可选） | ⏸️ 待集成 |
| `task_service.py` | （可选） | ⏸️ 待集成 |

---

## 🎯 事件类型总览

### LLM 相关事件

#### `llm.call.start`
**触发时机：** LLM API 调用开始时  
**数据来源：** `llm_client.py`

```python
{
    "agent": "web_chat_agent",
    "model": "qwen3.5-plus",
    "messages_count": 2
}
```

#### `llm.call.complete`
**触发时机：** LLM API 调用成功时  
**数据来源：** `llm_client.py`

```python
{
    "agent": "web_chat_agent",
    "model": "qwen3.5-plus",
    "tokens": 1392,
    "cost": 0.014216,
    "duration_ms": 18065.42,
    "success": True
}
```

#### `llm.call.error`
**触发时机：** LLM API 调用失败时  
**数据来源：** `llm_client.py`

```python
{
    "agent": "web_chat_agent",
    "model": "qwen3.5-plus",
    "error": "HTTP Error 400: Bad Request",
    "retries": 3,
    "duration_ms": 45000.0
}
```

### 工作流相关事件

#### `workflow.start`
**触发时机：** 工作流开始执行时  
**数据来源：** `workflow_orchestrator.py`

```python
{
    "workflow_id": "20260405_220000",
    "total_tasks": 17,
    "total_layers": 5
}
```

#### `workflow.progress`
**触发时机：** 每个任务完成时  
**数据来源：** `workflow_orchestrator.py`

```python
{
    "workflow_id": "20260405_220000",
    "layer_num": 1,
    "task_index": 3,
    "total_tasks": 17,
    "topic_name": "AI 基础",
    "status": "completed"
}
```

#### `workflow.complete`
**触发时机：** 工作流完成时  
**数据来源：** `workflow_orchestrator.py`

```python
{
    "workflow_id": "20260405_220000",
    "success_count": 17,
    "failed_count": 0,
    "skipped_count": 0,
    "total_tasks": 17,
    "duration_seconds": 3386.36
}
```

---

## 💡 使用示例

### 1. 订阅 LLM 调用完成事件（成本监控）

```python
from utils.event_bus import subscribe_event, EventType

def on_llm_complete(event):
    """LLM 调用完成时的处理"""
    data = event.data
    print(f"Agent: {data['agent']}")
    print(f"Tokens: {data['tokens']}")
    print(f"Cost: ¥{data['cost']:.4f}")
    
    # 成本超阈值告警
    if data['cost'] > 0.1:
        send_alert(f"⚠️ LLM 成本超阈值：¥{data['cost']:.4f}")

# 订阅事件
subscribe_event(EventType.LLM_CALL_COMPLETE, on_llm_complete)
```

### 2. 订阅工作流进度事件（实时进度条）

```python
from utils.event_bus import subscribe_event, EventType

def on_workflow_progress(event):
    """工作流进度更新"""
    data = event.data
    progress = (data['task_index'] / data['total_tasks']) * 100
    print(f"进度：{progress:.1f}% - {data['topic_name']}")
    
    # 更新 Web UI 进度条
    update_progress_bar(progress)

# 订阅事件
subscribe_event(EventType.WORKFLOW_PROGRESS, on_workflow_progress)
```

### 3. 订阅工作流完成事件（QQ 推送通知）

```python
from utils.event_bus import subscribe_event, EventType
from message import send  # OpenClaw message 工具

def on_workflow_complete(event):
    """工作流完成通知"""
    data = event.data
    
    # 构建通知消息
    message = f"""
🎉 工作流完成通知

📊 执行统计:
- 成功：{data['success_count']} 任务
- 失败：{data['failed_count']} 任务
- 跳过：{data['skipped_count']} 任务
- 总耗时：{data['duration_seconds']:.1f} 秒

✅ 所有任务已完成！
"""
    
    # 发送 QQ 推送
    send(
        action="send",
        channel="qqbot",
        to="qqbot:c2c:6BD7A1BCF3F92369D0580647287C0D52",
        message=message
    )

# 订阅事件
subscribe_event(EventType.WORKFLOW_COMPLETE, on_workflow_complete, async_mode=True)
```

### 4. 订阅所有事件（调试模式）

```python
from utils.event_bus import subscribe_event

def on_all_events(event):
    """通配符订阅所有事件（用于调试）"""
    print(f"[事件] {event.event_type} @ {event.timestamp}")
    print(f"  来源：{event.source}")
    print(f"  数据：{event.data}")

# 订阅所有事件
subscribe_event("*", on_all_events)
```

---

## 🔧 高级用法

### 事件过滤

```python
from utils.event_bus import subscribe_event, Event, EventType

def high_cost_filter(event: Event) -> bool:
    """只处理高成本事件"""
    return event.data.get('cost', 0) > 0.05

# 带过滤器的订阅
subscribe_event(
    EventType.LLM_CALL_COMPLETE,
    callback=on_llm_complete,
    filter_func=high_cost_filter
)
```

### 异步事件处理

```python
# 异步处理（不阻塞主线程）
subscribe_event(
    EventType.WORKFLOW_COMPLETE,
    callback=send_notification,
    async_mode=True  # 启用异步
)
```

### 取消订阅

```python
from utils.event_bus import get_event_bus

bus = get_event_bus()
bus.unsubscribe(EventType.LLM_CALL_COMPLETE, on_llm_complete)
```

---

## 📊 事件统计

### 查看事件历史

```python
from utils.event_bus import get_event_bus

bus = get_event_bus()

# 获取所有事件历史
history = bus.get_history(limit=100)

# 获取特定类型事件历史
llm_history = bus.get_history(EventType.LLM_CALL_COMPLETE, limit=50)

for event in llm_history:
    print(f"{event['event_type']} @ {event['timestamp']}")
```

### 获取统计信息

```python
from utils.event_bus import get_event_bus

bus = get_event_bus()
stats = bus.get_stats()

print(f"总事件数：{stats['total_events']}")
print(f"订阅者总数：{stats['total_subscribers']}")
print(f"事件类型：{list(stats['events_by_type'].keys())}")
```

---

## 🎯 实际应用场景

### 场景 1：实时成本监控

```python
# 在应用启动时订阅
subscribe_event(EventType.LLM_CALL_COMPLETE, lambda e: cost_tracker.add(e.data))

# 定期检查成本
def check_daily_cost():
    if cost_tracker.daily_total > 10.0:
        send_alert("⚠️ 每日成本超阈值！")
```

### 场景 2：工作流进度 Web UI

```javascript
// 前端通过 WebSocket 接收进度更新
// 后端通过事件总线推送
@websocket.route('/workflow/progress')
def workflow_progress(ws):
    def on_progress(event):
        ws.send(json.dumps(event.data))
    
    subscribe_event(EventType.WORKFLOW_PROGRESS, on_progress)
```

### 场景 3：性能分析

```python
# 收集 LLM 调用性能数据
llm_latencies = []

def collect_latency(event):
    llm_latencies.append(event.data['duration_ms'])

subscribe_event(EventType.LLM_CALL_COMPLETE, collect_latency)

# 分析性能
def analyze_performance():
    avg_latency = sum(llm_latencies) / len(llm_latencies)
    print(f"平均延迟：{avg_latency:.0f}ms")
```

---

## ⚠️ 注意事项

### 1. 事件总线可用性

```python
try:
    from utils.event_bus import publish_event, EventType
    EVENT_BUS_AVAILABLE = True
except Exception:
    EVENT_BUS_AVAILABLE = False  # 降级处理，不影响主流程

# 使用
if EVENT_BUS_AVAILABLE:
    publish_event(...)
```

### 2. 异常处理

事件处理函数中的异常不会影响主流程：

```python
def on_event(event):
    try:
        # 可能失败的操作
        risky_operation()
    except Exception as e:
        logger.error(f"事件处理失败：{e}")
        # 不影响其他订阅者和主流程
```

### 3. 内存管理

事件历史有限制（默认 1000 条），定期清理：

```python
bus = get_event_bus()
bus.clear_history()  # 清空历史
```

---

## 📈 性能影响

| 操作 | 耗时 | 影响 |
|------|------|------|
| 发布事件（同步） | <1ms | 微小 |
| 发布事件（异步） | <0.1ms | 可忽略 |
| 订阅事件 | <0.1ms | 可忽略 |
| 事件历史查询 | <5ms | 微小 |

**建议：** 对于耗时操作（如发送通知），使用异步模式 `async_mode=True`

---

## 🔍 调试技巧

### 1. 启用调试日志

```python
import logging
logging.getLogger('event_bus').setLevel(logging.DEBUG)
```

### 2. 查看所有订阅者

```python
bus = get_event_bus()
print(bus.list_event_types())  # 列出所有有订阅者的事件类型
```

### 3. 测试事件发布

```bash
# 运行事件总线测试
python3 utils/event_bus.py
```

---

## 📚 相关文档

- [事件总线源码](../utils/event_bus.py)
- [LLMClient 集成](../services/llm_client.py)
- [工作流编排器集成](../workflow_orchestrator.py)
- [第一周优化总结](./WEEK1_OPTIMIZATION_SUMMARY.md)

---

**文档维护者：** AI 助手  
**最后更新：** 2026-04-05 23:00
