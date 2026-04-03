"""Caching utilities for performance optimization"""

from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Generic, TypeVar

import structlog

logger = structlog.get_logger(__name__)

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """A cache entry with metadata"""
    value: T
    created_at: float = field(default_factory=time.time)
    expires_at: float | None = None
    hit_count: int = 0
    
    @property
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    @property
    def age(self) -> float:
        """Get entry age in seconds"""
        return time.time() - self.created_at


class LRUCache(Generic[T]):
    """
    Least Recently Used cache.
    
    Features:
    - Configurable max size
    - TTL support
    - Hit/miss statistics
    - Thread-safe operations
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: float | None = None,
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: dict[str, CacheEntry[T]] = {}
        self._access_order: list[str] = []
        self._hits = 0
        self._misses = 0
    
    @property
    def size(self) -> int:
        """Get current cache size"""
        return len(self._cache)
    
    @property
    def hit_rate(self) -> float:
        """Get cache hit rate"""
        total = self._hits + self._misses
        if total == 0:
            return 0.0
        return self._hits / total
    
    def get(self, key: str, default: T | None = None) -> T | None:
        """Get value from cache"""
        entry = self._cache.get(key)
        
        if entry is None:
            self._misses += 1
            return default
        
        if entry.is_expired:
            self._misses += 1
            del self._cache[key]
            self._access_order.remove(key)
            return default
        
        # Update access order
        self._access_order.remove(key)
        self._access_order.append(key)
        entry.hit_count += 1
        self._hits += 1
        
        return entry.value
    
    def set(
        self,
        key: str,
        value: T,
        ttl: float | None = None,
    ) -> None:
        """Set value in cache"""
        
        # Check if we need to evict
        if key not in self._cache and len(self._cache) >= self.max_size:
            self._evict()
        
        # Calculate expiration
        expires_at = None
        if ttl is not None or self.default_ttl is not None:
            expires_at = time.time() + (ttl or self.default_ttl)
        
        # Create entry
        entry = CacheEntry(
            value=value,
            expires_at=expires_at,
        )
        
        # Update cache
        if key in self._cache:
            self._access_order.remove(key)
        
        self._cache[key] = entry
        self._access_order.append(key)
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self._cache:
            del self._cache[key]
            self._access_order.remove(key)
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
        self._access_order.clear()
        self._hits = 0
        self._misses = 0
    
    def _evict(self) -> None:
        """Evict least recently used entry"""
        if not self._access_order:
            return
        
        # Remove oldest accessed
        oldest_key = self._access_order.pop(0)
        if oldest_key in self._cache:
            del self._cache[oldest_key]
    
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": self.size,
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self.hit_rate,
        }
    
    def __len__(self) -> int:
        return len(self._cache)
    
    def __contains__(self, key: str) -> bool:
        return key in self._cache and not self._cache[key].is_expired
    
    def __repr__(self) -> str:
        return f"LRUCache(size={self.size}, max={self.max_size}, hit_rate={self.hit_rate:.2f})"


class AsyncCache(Generic[T]):
    """Async-compatible cache with locking"""
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: float | None = None,
    ):
        self._cache = LRUCache[T](max_size, default_ttl)
        self._locks: dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()
    
    async def get(
        self,
        key: str,
        default: T | None = None,
    ) -> T | None:
        """Get value from cache"""
        return self._cache.get(key, default)
    
    async def set(
        self,
        key: str,
        value: T,
        ttl: float | None = None,
    ) -> None:
        """Set value in cache"""
        async with self._global_lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
        
        async with self._locks[key]:
            self._cache.set(key, value, ttl)
    
    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], T],
        ttl: float | None = None,
    ) -> T:
        """Get value or compute and cache it"""
        value = self._cache.get(key)
        
        if value is not None:
            return value
        
        async with self._global_lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
        
        async with self._locks[key]:
            # Double-check after acquiring lock
            value = self._cache.get(key)
            if value is not None:
                return value
            
            # Compute and cache
            if asyncio.iscoroutinefunction(factory):
                value = await factory()
            else:
                value = factory()
            
            self._cache.set(key, value, ttl)
            return value
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        async with self._global_lock:
            result = self._cache.delete(key)
            if key in self._locks:
                del self._locks[key]
            return result
    
    async def clear(self) -> None:
        """Clear cache"""
        async with self._global_lock:
            self._cache.clear()
            self._locks.clear()
    
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        return self._cache.get_stats()


def compute_hash(data: Any) -> str:
    """Compute hash for cache key"""
    serialized = str(data)
    return hashlib.md5(serialized.encode()).hexdigest()


def cached(
    cache: AsyncCache,
    key_prefix: str = "",
    ttl: float | None = None,
):
    """Decorator for caching async function results"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_data = f"{key_prefix}:{func.__name__}:{args}:{kwargs}"
            key = compute_hash(key_data)
            
            # Try cache
            result = await cache.get(key)
            if result is not None:
                return result
            
            # Compute and cache
            result = await func(*args, **kwargs)
            await cache.set(key, result, ttl)
            
            return result
        
        return wrapper
    return decorator
