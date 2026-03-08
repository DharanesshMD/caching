from __future__ import annotations
import asyncio
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.cache.base import CacheResult
from app.cache.in_memory import InMemoryCache
from app.middleware import metrics

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


async def get_memory_cache() -> InMemoryCache:
    return InMemoryCache()


@router.get("/demo/in-memory", response_class=HTMLResponse)
async def memory_demo(request: Request, cache: InMemoryCache = Depends(get_memory_cache)) -> Any:
    key = "demo:memory:time"

    try:
        r: CacheResult[Any] = await cache.get(key)
    except Exception:
        r = CacheResult(value=None, hit=False, latency_ms=0.0)

    if not r.hit:
        await asyncio.sleep(0.005)
        payload = {"time": asyncio.get_event_loop().time()}
        try:
            await cache.set(key, payload)
        except Exception:
            pass
        r = CacheResult(value=payload, hit=False, latency_ms=r.latency_ms)

    headers = {"X-Cache": "HIT" if r.hit else "MISS"}
    return templates.TemplateResponse(
        "demo/in-memory.html", {"request": request, "cache_result": r}, headers=headers
    )
