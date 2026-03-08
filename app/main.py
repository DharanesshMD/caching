from __future__ import annotations
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

try:
    from redis.asyncio import Redis
except Exception:  # pragma: no cover - if redis isn't installed, tests still run with DummyRedis
    Redis = None  # type: ignore


class _DummyRedis:
    """Simple async dict-backed Redis-like object used when a real Redis isn't available.

    This mirrors the minimal async interface used in the project: get, set, delete.
    """

    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None):
        self.store[key] = value

    async def delete(self, key: str):
        self.store.pop(key, None)


templates = Jinja2Templates(directory="app/templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create a Redis client if available and reachable, otherwise fall back to DummyRedis.

    The real redis.asyncio.Redis client opens connections lazily; we attempt a ping to
    verify availability and otherwise use a dummy in-memory store so the demo still works
    in development and in CI where Redis may not be running.
    """
    redis_client: Any = None
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    if Redis is not None:
        try:
            redis_client = Redis.from_url(redis_url, decode_responses=True)
            # Try a quick ping: if it fails, we'll use DummyRedis instead
            await redis_client.ping()
            app.state.redis = redis_client
        except Exception:
            # Cannot reach a real Redis instance — use dummy
            if redis_client is not None:
                try:
                    await redis_client.close()
                except Exception:
                    pass
            app.state.redis = _DummyRedis()
    else:
        app.state.redis = _DummyRedis()

    try:
        yield
    finally:
        # Close real redis client if we created one
        client = getattr(app.state, "redis", None)
        if client is not None and Redis is not None and isinstance(client, Redis):
            try:
                await client.close()
            except Exception:
                pass


def create_app() -> FastAPI:
    from app.routers import server_demo, browser_demo, cdn_demo, db_demo, in_memory_demo

    app = FastAPI(lifespan=lifespan)
    app.include_router(server_demo.router)
    # Register new demo routers
    app.include_router(browser_demo.router)
    app.include_router(cdn_demo.router)
    app.include_router(db_demo.router)
    app.include_router(in_memory_demo.router)
    return app


# Expose a module-level app for uvicorn convenience
app = create_app()
