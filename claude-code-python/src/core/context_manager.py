"""
上下文窗口管理器 - 智能压缩策略

实现类似 Claude Code 的上下文管理：
- 消息优先级排序
- 智能摘要压缩
- Token 计数与限制
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from ..models.messages import Message

logger = structlog.get_logger(__name__)


class MessagePriority(Enum):
    """消息优先级"""
    CRITICAL = 1      # 系统提示、关键配置 - 永不压缩
    HIGH = 2          # 用户最新请求 - 保留完整
    MEDIUM = 3        # 工具结果摘要 - 可压缩
    LOW = 4           # 早期对话历史 - 优先压缩


@dataclass
class CompressionStats:
    """压缩统计"""
    original_tokens: int = 0
    compressed_tokens: int = 0
    messages_removed: int = 0
    messages_summarized: int = 0
    
    @property
    def compression_ratio(self) -> float:
        if self.original_tokens == 0:
            return 0.0
        return 1.0 - (self.compressed_tokens / self.original_tokens)


class ContextManager:
    """
    上下文窗口管理器
    
    功能：
    1. Token 计数与监控
    2. 消息优先级排序
    3. 智能摘要压缩
    4. 自动清理低优先级消息
    """
    
    # Token 限制（根据模型调整）
    DEFAULT_MAX_TOKENS = 100000
    COMPRESSION_THRESHOLD = 0.8  # 达到 80% 时开始压缩
    
    def __init__(self, max_tokens: int = DEFAULT_MAX_TOKENS):
        self.max_tokens = max_tokens
        self.stats = CompressionStats()
        self._message_priorities: dict[int, MessagePriority] = {}
    
    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的 Token 数量
        
        简化算法：英文 ~4 字符/token，中文 ~1.5 字符/token
        """
        if not text:
            return 0
        
        # 统计中英文字符
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        
        # 估算：中文 1.5 字符/token，英文 4 字符/token
        tokens = chinese_chars + (other_chars // 4)
        return max(1, tokens)
    
    def count_messages_tokens(self, messages: list[Message]) -> int:
        """计算消息列表的总 Token 数"""
        total = 0
        for msg in messages:
            total += self.estimate_tokens(msg.content or "")
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    total += self.estimate_tokens(json.dumps(tc.input))
        return total
    
    def assign_priority(self, message: Message, index: int, total: int) -> MessagePriority:
        """
        为消息分配优先级
        
        Args:
            message: 消息对象
            index: 消息索引（从 0 开始）
            total: 消息总数
        """
        # 系统提示 - 最高优先级
        if message.role == "system":
            return MessagePriority.CRITICAL
        
        # 最新的用户消息 - 高优先级
        if message.role == "user" and index == total - 1:
            return MessagePriority.HIGH
        
        # 工具结果 - 中优先级
        if "[Tool" in (message.content or ""):
            return MessagePriority.MEDIUM
        
        # 早期对话 - 低优先级
        return MessagePriority.LOW
    
    def summarize_tool_result(self, result_text: str, max_length: int = 500) -> str:
        """
        智能摘要工具结果
        
        策略：
        1. 保留关键信息（错误、成功状态）
        2. 截断冗长的输出
        3. 保留结构化数据
        """
        if len(result_text) <= max_length:
            return result_text
        
        # 检查是否是错误信息
        if result_text.startswith("Error:") or "[Error]" in result_text:
            # 保留完整错误信息
            return result_text[:max_length + 500] + "\n... (truncated)"
        
        # 检查是否是文件内容
        if result_text.startswith("```"):
            # 保留代码块结构，压缩中间内容
            lines = result_text.split("\n")
            if len(lines) > 50:
                compressed = lines[:20] + [f"\n... ({len(lines) - 40} lines omitted) ...\n"] + lines[-20:]
                return "\n".join(compressed)
        
        # 默认：保留开头和结尾
        return result_text[:max_length // 2] + "\n... (truncated) ...\n" + result_text[-max_length // 2:]
    
    def compress_messages(
        self,
        messages: list[Message],
        target_tokens: int | None = None
    ) -> list[Message]:
        """
        压缩消息列表
        
        策略：
        1. 保留系统提示和最新消息
        2. 摘要冗长的工具结果
        3. 移除最早的低优先级消息
        
        Args:
            messages: 原始消息列表
            target_tokens: 目标 Token 数（默认 max_tokens * 0.7）
            
        Returns:
            压缩后的消息列表
        """
        if target_tokens is None:
            target_tokens = int(self.max_tokens * COMPRESSION_THRESHOLD)
        
        self.stats = CompressionStats()
        self.stats.original_tokens = self.count_messages_tokens(messages)
        
        if self.stats.original_tokens <= target_tokens:
            return messages  # 无需压缩
        
        logger.info("Starting context compression", 
                   original=self.stats.original_tokens, 
                   target=target_tokens)
        
        # 1. 为每条消息分配优先级
        prioritized = []
        for i, msg in enumerate(messages):
            priority = self.assign_priority(msg, i, len(messages))
            prioritized.append((i, priority, msg))
        
        # 2. 按优先级分组
        critical = [(i, m) for i, p, m in prioritized if p == MessagePriority.CRITICAL]
        high = [(i, m) for i, p, m in prioritized if p == MessagePriority.HIGH]
        medium = [(i, m) for i, p, m in prioritized if p == MessagePriority.MEDIUM]
        low = [(i, m) for i, p, m in prioritized if p == MessagePriority.LOW]
        
        # 3. 首先尝试摘要中等优先级的工具结果
        compressed_medium = []
        for i, msg in medium:
            if msg.content and "[Tool" in msg.content:
                summarized = self.summarize_tool_result(msg.content)
                if len(summarized) < len(msg.content):
                    msg = Message(role=msg.role, content=summarized)
                    self.stats.messages_summarized += 1
            compressed_medium.append((i, msg))
        
        # 4. 计算当前 Token 数
        current_messages = [m for _, m in critical + high + compressed_medium + low]
        current_tokens = self.count_messages_tokens(current_messages)
        
        # 5. 如果仍然超出，移除最早的低优先级消息
        while current_tokens > target_tokens and low:
            # 移除最早的低优先级消息
            removed = low.pop(0)
            self.stats.messages_removed += 1
            current_messages = [m for _, m in critical + high + compressed_medium + low]
            current_tokens = self.count_messages_tokens(current_messages)
            
            if len(low) == 0:
                # 没有更多低优先级消息，尝试移除中等优先级
                if compressed_medium:
                    removed = compressed_medium.pop(0)
                    self.stats.messages_removed += 1
        
        # 6. 重新组合消息（保持原始顺序）
        remaining_indices = set()
        for i, _ in critical + high + compressed_medium + low:
            remaining_indices.add(i)
        
        compressed_messages = [messages[i] for i in sorted(remaining_indices)]
        
        self.stats.compressed_tokens = self.count_messages_tokens(compressed_messages)
        
        logger.info("Compression completed",
                   compressed_tokens=self.stats.compressed_tokens,
                   ratio=f"{self.stats.compression_ratio:.1%}")
        
        return compressed_messages
    
    def should_compress(self, messages: list[Message]) -> bool:
        """检查是否需要压缩"""
        current_tokens = self.count_messages_tokens(messages)
        return current_tokens > (self.max_tokens * self.COMPRESSION_THRESHOLD)
    
    def get_stats(self) -> CompressionStats:
        """获取压缩统计"""
        return self.stats


@dataclass
class MemoryEntry:
    """记忆条目"""
    key: str
    content: str
    created_at: float = field(default_factory=lambda: 0)
    access_count: int = 0
    tags: list[str] = field(default_factory=list)


class SessionMemory:
    """
    跨会话记忆系统
    
    功能：
    1. 持久化存储用户偏好
    2. 项目上下文记忆
    3. LRU 缓存管理
    """
    
    def __init__(self, memory_file: str = ".ccp_memory.json"):
        self.memory_file = memory_file
        self.entries: dict[str, MemoryEntry] = {}
        self._load()
    
    def _load(self):
        """从文件加载记忆"""
        import os
        import json
        
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r") as f:
                    data = json.load(f)
                    for key, value in data.items():
                        self.entries[key] = MemoryEntry(**value)
                logger.info("Loaded session memory", count=len(self.entries))
            except Exception as e:
                logger.warning("Failed to load memory", error=str(e))
    
    def _save(self):
        """保存记忆到文件"""
        import json
        
        try:
            with open(self.memory_file, "w") as f:
                data = {k: {
                    "key": v.key,
                    "content": v.content,
                    "created_at": v.created_at,
                    "access_count": v.access_count,
                    "tags": v.tags
                } for k, v in self.entries.items()}
                json.dump(data, f, indent=2)
            logger.debug("Saved session memory")
        except Exception as e:
            logger.warning("Failed to save memory", error=str(e))
    
    def set(self, key: str, content: str, tags: list[str] = None):
        """设置记忆条目"""
        import time
        
        self.entries[key] = MemoryEntry(
            key=key,
            content=content,
            created_at=time.time(),
            access_count=0,
            tags=tags or []
        )
        self._save()
    
    def get(self, key: str) -> str | None:
        """获取记忆条目"""
        if key in self.entries:
            self.entries[key].access_count += 1
            return self.entries[key].content
        return None
    
    def search(self, query: str) -> list[MemoryEntry]:
        """搜索记忆"""
        results = []
        query_lower = query.lower()
        
        for entry in self.entries.values():
            if (query_lower in entry.key.lower() or 
                query_lower in entry.content.lower() or
                any(query_lower in tag.lower() for tag in entry.tags)):
                results.append(entry)
        
        # 按访问次数排序
        results.sort(key=lambda e: e.access_count, reverse=True)
        return results
    
    def delete(self, key: str) -> bool:
        """删除记忆条目"""
        if key in self.entries:
            del self.entries[key]
            self._save()
            return True
        return False
    
    def clear(self):
        """清空所有记忆"""
        self.entries.clear()
        self._save()
    
    def get_context(self, query: str, max_entries: int = 5) -> str:
        """获取相关记忆作为上下文"""
        results = self.search(query)
        
        if not results:
            return ""
        
        context_parts = ["[Relevant Memory]"]
        for entry in results[:max_entries]:
            context_parts.append(f"- {entry.key}: {entry.content}")
        
        return "\n".join(context_parts)
