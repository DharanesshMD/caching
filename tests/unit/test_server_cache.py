import pytest
import asyncio

from app.cache.server_cache import RedisServerCache
from app.cache.base import CacheResult


class DummyRedis:
    def __init__(self):
        self.store = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ex=None):
        self.store[key] = value

    async def delete(self, key):
        self.store.pop(key, None)


@pytest.mark.asyncio
async def test_set_get_delete():
    redis = DummyRedis()
    cache = RedisServerCache(redis=redis, default_ttl=60)

    await cache.set("server:foo", {"a": 1}, ttl=30)
    r = await cache.get("server:foo")
    assert isinstance(r, CacheResult)
    assert r.hit is True
    assert r.value == {"a": 1}

    await cache.delete("server:foo")
    r2 = await cache.get("server:foo")
    assert r2.hit is False
    assert r2.value is None
