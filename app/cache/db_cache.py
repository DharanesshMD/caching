from __future__ import annotations
import asyncio
import json
import time
from typing import Any, Dict, Optional

from .base import AsyncCache, CacheResult
from ..middleware import metrics


class DBCache(AsyncCache[Any]):
    def __init__(self, default_ttl: int = 600) -> None:
        # For demo purposes use in-process store to simulate query caching
        self._store: Dict[str, Dict[str, Any]] = {}
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()

    async def _cleanup(self) -> None:
        now = time.time()
        keys = [k for k, v in self._store.items() if v["expires_at"] is not None and v["expires_at"] < now]
        for k in keys:
            self._store.pop(k, None)

    async def get(self, key: str) -> CacheResult[Any]:
        start = time.perf_counter()
        async with self._lock:
            await self._cleanup()
            entry = self._store.get(key)
            latency_ms = (time.perf_counter() - start) * 1000.0
            if not entry:
                metrics.log_miss("database", key)
                return CacheResult(value=None, hit=False, latency_ms=latency_ms)

            try:
                value = json.loads(entry["value"])
            except Exception:
                metrics.log_miss("database", key)
                return CacheResult(value=None, hit=False, latency_ms=latency_ms)

            metrics.log_hit("database", key)
            return CacheResult(value=value, hit=True, latency_ms=latency_ms)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl or self._default_ttl
        raw = json.dumps(value)
        expires_at = time.time() + ttl if ttl is not None else None
        async with self._lock:
            self._store[key] = {"value": raw, "expires_at": expires_at}

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)
