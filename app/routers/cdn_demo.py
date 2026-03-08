from __future__ import annotations
import asyncio
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.cache.base import CacheResult
from app.cache.cdn_cache import CDNCached
from app.middleware import metrics

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


async def get_cdn_cache() -> CDNCached:
    return CDNCached()


@router.get("/demo/cdn", response_class=HTMLResponse)
async def cdn_demo(request: Request, cache: CDNCached = Depends(get_cdn_cache)) -> Any:
    key = "demo:cdn:time"

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
    return templates.TemplateResponse("demo/cdn.html", {"request": request, "cache_result": r}, headers=headers)
