import pytest
import asyncio

from app.cache.in_memory import InMemoryCache
from app.cache.cdn_cache import CDNCached
from app.cache.db_cache import DBCache
from app.cache.browser_cache import BrowserCache
from app.cache.base import CacheResult


@pytest.mark.asyncio
async def test_in_memory_cache_set_get_delete():
    c = InMemoryCache(default_ttl=1)
    await c.set("m:foo", {"a": 1}, ttl=1)
    r = await c.get("m:foo")
    assert isinstance(r, CacheResult)
    assert r.hit is True
    assert r.value == {"a": 1}
    await c.delete("m:foo")
    r2 = await c.get("m:foo")
    assert r2.hit is False


@pytest.mark.asyncio
async def test_cdn_cache_set_get_delete():
    c = CDNCached(default_ttl=1)
    await c.set("c:foo", {"b": 2}, ttl=1)
    r = await c.get("c:foo")
    assert r.hit is True
    assert r.value == {"b": 2}
    await c.delete("c:foo")
    r2 = await c.get("c:foo")
    assert r2.hit is False


@pytest.mark.asyncio
async def test_db_cache_set_get_delete():
    c = DBCache(default_ttl=1)
    await c.set("d:foo", {"c": 3}, ttl=1)
    r = await c.get("d:foo")
    assert r.hit is True
    assert r.value == {"c": 3}
    await c.delete("d:foo")
    r2 = await c.get("d:foo")
    assert r2.hit is False


@pytest.mark.asyncio
async def test_browser_cache_behaviour():
    c = BrowserCache()
    r = await c.get("b:foo")
    assert r.hit is False
    await c.set("b:foo", {"x": 1})
    # Still returns miss because browser cache is client-side
    r2 = await c.get("b:foo")
    assert r2.hit is False
