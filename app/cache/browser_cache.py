from __future__ import annotations
import json
import time
from typing import Any, Optional

from .base import AsyncCache, CacheResult
from ..middleware import metrics


class BrowserCache(AsyncCache[Any]):
    """Browser cache is header-driven. For demo purposes we always return a MISS
    because the server cannot simulate client-side cache without request headers.

    But we keep the same API so the demo can display headers and behavior.
    """

    def __init__(self, default_ttl: int = 31536000) -> None:
        self._default_ttl = default_ttl

    async def get(self, key: str) -> CacheResult[Any]:
        # Browser caching is client-driven; treat as miss from server POV.
        metrics.log_miss("browser", key)
        return CacheResult(value=None, hit=False, latency_ms=0.0)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        # No-op server-side: browser caches by headers included in responses.
        return None

    async def delete(self, key: str) -> None:
        return None
