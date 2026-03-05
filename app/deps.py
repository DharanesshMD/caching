from __future__ import annotations
from typing import AsyncIterator

from fastapi import Depends, Request

from app.cache.server_cache import RedisServerCache
from redis.asyncio import Redis


async def get_redis(request: Request) -> Redis:
    """Return the redis client stored on app.state by app.main lifespan."""
    return request.app.state.redis


async def get_cache(redis: Redis = Depends(get_redis)) -> AsyncIterator[RedisServerCache]:
    """Provide a RedisServerCache instance bound to the app's Redis client.

    Yielding a fresh RedisServerCache keeps the dependency simple and avoids
    storing additional globals. The cache is lightweight and simply wraps the
    redis client.
    """
    cache = RedisServerCache(redis=redis, default_ttl=300)
    yield cache
