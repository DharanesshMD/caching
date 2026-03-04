from __future__ import annotations
import json
import time
from typing import Any

from redis.asyncio import Redis

from .base import AsyncCache, CacheResult
from ..middleware import metrics


class RedisServerCache(AsyncCache[Any]):
    """Async Redis-backed server cache.

    Uses JSON serialization for values. Assumes a redis.asyncio.Redis client is provided.
    """

    def __init__(self, redis: Redis, default_ttl: int = 300) -> None:
        self._redis = redis
        self._default_ttl = default_ttl

    async def get(self, key: str) -> CacheResult[Any]:
        start = time.perf_counter()
        raw = await self._redis.get(key)
        latency_ms = (time.perf_counter() - start) * 1000.0

        if raw is None:
            metrics.log_miss("server", key)
            return CacheResult(value=None, hit=False, latency_ms=latency_ms)

        try:
            value = json.loads(raw)
        except Exception:
            # If deserialization fails, treat as miss
            metrics.log_miss("server", key)
            return CacheResult(value=None, hit=False, latency_ms=latency_ms)

        metrics.log_hit("server", key)
        return CacheResult(value=value, hit=True, latency_ms=latency_ms)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        ttl = ttl or self._default_ttl
        raw = json.dumps(value)
        await self._redis.set(key, raw, ex=ttl)

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)
