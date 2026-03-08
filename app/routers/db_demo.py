from __future__ import annotations
import asyncio
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.cache.base import CacheResult
from app.cache.db_cache import DBCache

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


async def get_db_cache() -> DBCache:
    return DBCache()


@router.get("/demo/database", response_class=HTMLResponse)
async def db_demo(request: Request, cache: DBCache = Depends(get_db_cache)) -> Any:
    key = "demo:db:time"

    try:
        r: CacheResult[Any] = await cache.get(key)
    except Exception:
        r = CacheResult(value=None, hit=False, latency_ms=0.0)

    if not r.hit:
        await asyncio.sleep(0.002)
        # Simulate a DB query result
        payload = {"rows": [{"id": 1, "ts": asyncio.get_event_loop().time()}]}
        try:
            await cache.set(key, payload)
        except Exception:
            pass
        r = CacheResult(value=payload, hit=False, latency_ms=r.latency_ms)

    headers = {"X-Cache": "HIT" if r.hit else "MISS"}
    return templates.TemplateResponse(
        "demo/database.html", {"request": request, "cache_result": r}, headers=headers
    )
