from __future__ import annotations
import asyncio
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.cache.base import CacheResult
from app.cache.browser_cache import BrowserCache
from app.middleware import cache_headers

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


async def get_browser_cache() -> BrowserCache:
    return BrowserCache()


@router.get("/demo/browser", response_class=HTMLResponse)
async def browser_demo(request: Request, cache: BrowserCache = Depends(get_browser_cache)) -> Any:
    key = "demo:browser:time"

    r: CacheResult[Any] = await cache.get(key)

    if not r.hit:
        # Simulate origin generation; browser caching depends on headers
        await asyncio.sleep(0.001)
        payload = {"time": asyncio.get_event_loop().time()}
        try:
            await cache.set(key, payload)
        except Exception:
            pass
        r = CacheResult(value=payload, hit=False, latency_ms=r.latency_ms)

    headers = {"X-Cache": "HIT" if r.hit else "MISS"}
    # Include browser headers in template context for demo
    bheaders = cache_headers.build_browser_headers()
    return templates.TemplateResponse(
        "demo/browser.html",
        {"request": request, "cache_result": r, "browser_headers": bheaders},
        headers=headers,
    )
