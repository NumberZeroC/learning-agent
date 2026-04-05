#!/usr/bin/env python3
"""
事件总线（Event Bus）

轻量级事件总线，支持：
- 发布/订阅模式
- 同步/异步事件处理
- 事件过滤
- 线程安全

用于模块解耦，例如：
- LLM 调用完成 → 触发审计日志记录
- 工作流完成 → 触发通知推送
- 配置变更 → 触发热更新
"""

import threading
import logging
from typing import Dict, List, Callable, Any, Optional
from collections import defaultdict
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class Event:
    """事件对象"""
    
    def __init__(self, event_type: str, data: Dict[str, Any], 
                 source: str = "unknown"):
        self.event_type = event_type
        self.data = data
        self.source = source
        self.timestamp = datetime.now().isoformat()
        self.id = f"{event_type}_{self.timestamp.replace(':', '').replace('.', '_')}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "data": self.data,
            "source": self.source,
            "timestamp": self.timestamp
        }
    
    def __repr__(self) -> str:
        return f"Event(type={self.event_type}, source={self.source})"


class EventBus:
    """
    事件总线
    
    特性：
    - 发布/订阅模式
    - 支持多个订阅者
    - 线程安全
    - 支持事件过滤
    - 支持同步/异步处理
    """
    
    _instance: Optional['EventBus'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'EventBus':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        # 订阅者存储：event_type -> List[(callback, filter_func, async_mode)]
        self._subscribers: Dict[str, List[tuple]] = defaultdict(list)
        
        # 事件历史（用于调试和重放）
        self._event_history: List[Event] = []
        self._history_max_size = 1000
        
        # 线程锁
        self._lock = threading.RLock()
        
        # 统计信息
        self._stats = {
            "total_events": 0,
            "events_by_type": defaultdict(int),
            "subscribers_by_type": defaultdict(int)
        }
        
        self._initialized = True
        logger.info("✅ 事件总线初始化完成")
    
    def subscribe(self, event_type: str, callback: Callable[[Event], Any],
                  filter_func: Optional[Callable[[Event], bool]] = None,
                  async_mode: bool = False):
        """
        订阅事件
        
        Args:
            event_type: 事件类型（支持通配符 "*" 订阅所有事件）
            callback: 回调函数，接收 Event 对象
            filter_func: 可选的过滤函数，返回 True 才处理
            async_mode: 是否异步处理（默认同步）
        """
        with self._lock:
            self._subscribers[event_type].append((callback, filter_func, async_mode))
            self._stats["subscribers_by_type"][event_type] += 1
        
        logger.debug(f"📬 订阅事件：{event_type} (async={async_mode})")
    
    def unsubscribe(self, event_type: str, callback: Callable[[Event], Any]):
        """取消订阅"""
        with self._lock:
            subscribers = self._subscribers.get(event_type, [])
            self._subscribers[event_type] = [
                (cb, flt, async_m) for cb, flt, async_m in subscribers
                if cb != callback
            ]
            self._stats["subscribers_by_type"][event_type] = len(self._subscribers[event_type])
        
        logger.debug(f"📭 取消订阅：{event_type}")
    
    def publish(self, event_type: str, data: Dict[str, Any], 
                source: str = "unknown", async_mode: Optional[bool] = None):
        """
        发布事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
            source: 事件来源
            async_mode: 是否强制异步（None 表示使用订阅时的设置）
        """
        event = Event(event_type, data, source)
        
        with self._lock:
            # 记录事件历史
            self._event_history.append(event)
            if len(self._event_history) > self._history_max_size:
                self._event_history.pop(0)
            
            # 更新统计
            self._stats["total_events"] += 1
            self._stats["events_by_type"][event_type] += 1
            
            # 获取订阅者（包括通配符订阅）
            subscribers = self._subscribers.get(event_type, []).copy()
            if event_type != "*":
                subscribers.extend(self._subscribers.get("*", []))
        
        # 通知订阅者（在锁外执行，避免死锁）
        for callback, filter_func, sub_async_mode in subscribers:
            # 使用传入的 async_mode 或订阅时的设置
            use_async = async_mode if async_mode is not None else sub_async_mode
            
            # 应用过滤器
            if filter_func and not filter_func(event):
                continue
            
            try:
                if use_async:
                    # 异步处理
                    thread = threading.Thread(
                        target=self._invoke_callback,
                        args=(callback, event),
                        daemon=True
                    )
                    thread.start()
                else:
                    # 同步处理
                    self._invoke_callback(callback, event)
            except Exception as e:
                logger.error(f"❌ 事件处理失败：{event_type} - {e}")
        
        logger.debug(f"📢 发布事件：{event_type} (订阅者：{len(subscribers)})")
    
    def _invoke_callback(self, callback: Callable[[Event], Any], event: Event):
        """调用回调函数"""
        try:
            callback(event)
        except Exception as e:
            logger.error(f"❌ 回调执行失败：{event.event_type} - {e}")
            raise
    
    def get_history(self, event_type: Optional[str] = None, 
                   limit: int = 100) -> List[Dict]:
        """获取事件历史"""
        with self._lock:
            history = self._event_history.copy()
        
        if event_type:
            history = [e for e in history if e.event_type == event_type]
        
        return [e.to_dict() for e in history[-limit:]]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                "total_events": self._stats["total_events"],
                "events_by_type": dict(self._stats["events_by_type"]),
                "subscribers_by_type": dict(self._stats["subscribers_by_type"]),
                "total_subscribers": sum(self._stats["subscribers_by_type"].values())
            }
    
    def clear_history(self):
        """清空事件历史"""
        with self._lock:
            self._event_history.clear()
        logger.debug("🧹 事件历史已清空")
    
    def list_event_types(self) -> List[str]:
        """列出所有有订阅者的事件类型"""
        with self._lock:
            return list(self._subscribers.keys())


# ============================================
# 预定义事件类型
# ============================================

class EventType:
    """预定义事件类型"""
    
    # LLM 相关
    LLM_CALL_START = "llm.call.start"
    LLM_CALL_COMPLETE = "llm.call.complete"
    LLM_CALL_ERROR = "llm.call.error"
    
    # 工作流相关
    WORKFLOW_START = "workflow.start"
    WORKFLOW_PROGRESS = "workflow.progress"
    WORKFLOW_COMPLETE = "workflow.complete"
    WORKFLOW_ERROR = "workflow.error"
    
    # 配置相关
    CONFIG_CHANGE = "config.change"
    CONFIG_RELOAD = "config.reload"
    
    # 系统相关
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_HEALTH = "system.health"
    
    # 通知相关
    NOTIFICATION_READY = "notification.ready"
    NOTIFICATION_SEND = "notification.send"


# ============================================
# 便捷函数
# ============================================

def get_event_bus() -> EventBus:
    """获取事件总线单例"""
    return EventBus()


def publish_event(event_type: str, data: Dict[str, Any], source: str = "unknown"):
    """便捷函数：发布事件"""
    get_event_bus().publish(event_type, data, source)


def subscribe_event(event_type: str, callback: Callable[[Event], Any], 
                   async_mode: bool = False):
    """便捷函数：订阅事件"""
    get_event_bus().subscribe(event_type, callback, async_mode=async_mode)


# ============================================
# 示例用法
# ============================================

if __name__ == "__main__":
    import time
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 获取事件总线
    bus = get_event_bus()
    
    # 定义回调
    def on_llm_call(event: Event):
        print(f"📝 [LLM 回调] 收到事件：{event.event_type}")
        print(f"   数据：{event.data}")
    
    def on_workflow_complete(event: Event):
        print(f"✅ [工作流完成] 工作流 {event.data.get('workflow_id')} 完成")
    
    # 订阅事件
    bus.subscribe(EventType.LLM_CALL_COMPLETE, on_llm_call)
    bus.subscribe(EventType.WORKFLOW_COMPLETE, on_workflow_complete)
    bus.subscribe("*", lambda e: print(f"🔍 [通配符] 捕获事件：{e.event_type}"))
    
    # 发布事件
    print("\n📢 发布 LLM 调用完成事件...")
    bus.publish(EventType.LLM_CALL_COMPLETE, {
        "agent": "test_agent",
        "model": "qwen3.5-plus",
        "tokens": 1000,
        "cost": 0.01
    }, source="test")
    
    time.sleep(0.1)
    
    print("\n📢 发布工作流完成事件...")
    bus.publish(EventType.WORKFLOW_COMPLETE, {
        "workflow_id": "wf_123",
        "success_count": 10,
        "failed_count": 0
    }, source="workflow_orchestrator")
    
    time.sleep(0.1)
    
    # 打印统计
    print("\n📊 统计信息:")
    stats = bus.get_stats()
    print(f"   总事件数：{stats['total_events']}")
    print(f"   订阅者总数：{stats['total_subscribers']}")
    print(f"   事件类型：{list(stats['events_by_type'].keys())}")
    
    # 查看历史
    print("\n📜 事件历史:")
    for event in bus.get_history(limit=5):
        print(f"   - {event['event_type']} @ {event['timestamp']}")
