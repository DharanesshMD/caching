from __future__ import annotations
from dataclasses import dataclass
from typing import Generic, Optional, Protocol, TypeVar

T = TypeVar("T")

@dataclass
class CacheResult(Generic[T]):
    """Result returned by cache operations.

    Fields:
    - value: the stored value or None for a miss
    - hit: True when the value was returned from cache
    - latency_ms: round-trip time in milliseconds for the cache operation
    """

    value: Optional[T]
    hit: bool
    latency_ms: float


class AsyncCache(Protocol[T]):
    """Minimal async cache protocol used across the project."""

    async def get(self, key: str) -> CacheResult[T]:
        ...

    async def set(self, key: str, value: T, ttl: int | None = None) -> None:
        ...

    async def delete(self, key: str) -> None:
        ...
