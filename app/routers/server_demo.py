from __future__ import annotations
import asyncio
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.cache.base import CacheResult
from app.middleware import metrics
from app.deps import get_cache

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/demo/server", response_class=HTMLResponse)
async def server_demo(request: Request, cache=Depends(get_cache)) -> Any:
    """Demo route that exercises the server Redis cache.

    Flow:
    - Try to get key from cache
    - If miss, simulate an origin fetch (async sleep + payload)
    - Set cache and render template with CacheResult
    - Add an X-Cache header indicating HIT/MISS
    """
    key = "demo:server:time"

    try:
        r: CacheResult[Any] = await cache.get(key)
    except Exception:
        # If Redis is unavailable or the cache raises, treat as miss but keep working
        r = CacheResult(value=None, hit=False, latency_ms=0.0)

    if not r.hit:
        # Simulate slow origin fetch
        await asyncio.sleep(0.01)
        payload = {"time": asyncio.get_event_loop().time()}
        try:
            await cache.set(key, payload)
        except Exception:
            # swallow errors so demo still renders
            pass
        # record miss metric
        metrics.log_miss("server", key)
        # create a CacheResult representing the post-fetch state
        r = CacheResult(value=payload, hit=False, latency_ms=r.latency_ms)
    else:
        metrics.log_hit("server", key)

    headers = {"X-Cache": "HIT" if r.hit else "MISS"}
    return templates.TemplateResponse(
        "demo/server.html", {"request": request, "cache_result": r}, headers=headers
    )
