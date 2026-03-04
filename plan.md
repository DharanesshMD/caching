# CacheWise — plan.md

> Project memory for Claude Code. Loaded automatically at every session start.
> Run `/init` to regenerate · Run `/memory` to edit in-session · Keep under 500 lines.

---

## Project Overview

**CacheWise** is a FastAPI-based educational platform that demonstrates all five caching types
(Browser, Server, CDN, Database, In-Memory) with live HIT/MISS badges, latency comparisons,
and self-explanatory UI annotations.

```
Stack: FastAPI · Redis · Memcached · PostgreSQL · NGINX · Docker Compose
Python: 3.12+    Node: 20+ (frontend tooling only)
```

---

## Essential Commands

```bash
# Start all services
docker-compose up --build

# Start only backend (requires Redis + PG already running)
uvicorn app.main:app --reload --port 8000

# Run tests
pytest                          # all tests
pytest tests/unit/              # unit only
pytest tests/integration/       # integration (needs Docker)
pytest -k "browser_cache"       # filter by name

# Load test (500 concurrent users)
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Lint + type-check
ruff check .
mypy app/

# Format
ruff format .

# Apply DB migrations
alembic upgrade head

# Flush all Redis cache (dev only)
redis-cli FLUSHALL
```

---

## Project Structure

```
cachewise/
├── CLAUDE.md                   ← you are here
├── .claude/
│   ├── commands/               ← custom slash commands
│   │   ├── cache-flush.md
│   │   ├── add-endpoint.md
│   │   └── run-demo.md
│   └── settings.json           ← hooks + permissions
├── app/
│   ├── main.py                 ← FastAPI app factory
│   ├── cache/                  ← ONE FILE PER CACHE LAYER
│   │   ├── browser_cache.py    ← Cache-Control / ETag headers
│   │   ├── server_cache.py     ← Redis server-side cache
│   │   ├── cdn_cache.py        ← CDN header simulation
│   │   ├── db_cache.py         ← SQLAlchemy query cache
│   │   └── in_memory.py        ← Redis/Memcached in-memory
│   ├── middleware/
│   │   ├── cache_headers.py    ← global Cache-Control middleware
│   │   └── metrics.py          ← Prometheus hit/miss counters
│   ├── routers/                ← one router per demo page
│   │   ├── browser_demo.py     ← /demo/browser
│   │   ├── server_demo.py      ← /demo/server
│   │   ├── cdn_demo.py         ← /demo/cdn
│   │   ├── db_demo.py          ← /demo/database
│   │   └── memory_demo.py      ← /demo/in-memory
│   ├── models/                 ← SQLAlchemy models
│   ├── templates/              ← Jinja2 HTML templates
│   └── config.py               ← settings via pydantic-settings
├── infra/
│   ├── nginx/cdn_sim.conf      ← local CDN simulation
│   └── aws/cloudfront.tf       ← Terraform CloudFront config
├── tests/
│   ├── unit/
│   ├── integration/
│   └── load/locustfile.py
├── docker-compose.yml
├── pyproject.toml
└── alembic/
```

---

## Coding Standards

### Python
- **Python 3.12+** — use `match`, `TypeAlias`, `Self` where appropriate
- **Type hints everywhere** — all function signatures must be fully typed
- **async/await** — all route handlers and cache methods must be async
- **Pydantic v2** for request/response schemas
- **ruff** for linting and formatting (line length 100)
- **mypy strict** — no `Any` unless justified with a comment
- **Docstrings** on all public classes and functions (Google style)

### FastAPI conventions
```python
# ✅ Correct: async handler, typed response model, dependency injection
@router.get("/products", response_model=list[ProductSchema])
async def list_products(
    db: AsyncSession = Depends(get_db),
    cache: RedisServerCache = Depends(get_cache),
) -> list[ProductSchema]:
    ...

# ❌ Wrong: sync handler, untyped, no DI
@router.get("/products")
def list_products():
    ...
```

### Cache layer conventions
- Every cache method returns `CacheResult(value, hit: bool, latency_ms: float)`
- Always log HIT/MISS via the `metrics` module — never `print()`
- TTL defaults: Browser=31536000s · Server=300s · CDN=3600s · DB=600s · Memory=60s
- Cache keys use the pattern `{layer}:{resource}:{id}` e.g. `server:products:list`

### Git
- Branch naming: `feature/`, `fix/`, `chore/`
- Commit style: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`)
- Every PR must include: updated tests + updated `docs/` if behaviour changes
- Run `ruff check . && mypy app/ && pytest tests/unit/` before committing

---

## Environment Variables

```bash
# Required (copy .env.example → .env)
DATABASE_URL=postgresql+asyncpg://cachewise:password@localhost:5432/cachewise
REDIS_URL=redis://localhost:6379/0
MEMCACHED_HOST=localhost
MEMCACHED_PORT=11211

# Optional
CACHE_DEFAULT_TTL=300
LOG_LEVEL=INFO                  # DEBUG in dev
PROMETHEUS_ENABLED=true
CDN_SIM_ENABLED=true            # enables NGINX CDN simulation
```

---

## Custom Slash Commands

> Invoke with `/command-name` inside a Claude Code session.

| Command | File | What it does |
|---|---|---|
| `/cache-flush` | `.claude/commands/cache-flush.md` | Flushes Redis + Memcached, prints hit stats |
| `/add-endpoint` | `.claude/commands/add-endpoint.md` | Scaffolds a new demo route + template |
| `/run-demo` | `.claude/commands/run-demo.md` | Starts docker-compose and opens browser |

### Defining a new command
```bash
# Create in project scope (shared with team via git)
echo "Your prompt here. Use \$ARGUMENTS for parameters." \
  > .claude/commands/my-command.md

# Or personal scope (not committed)
echo "Prompt..." > ~/.claude/commands/my-command.md
```

---

## MCP Servers

```jsonc
// .mcp.json — committed to repo for team sharing
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}" }
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": { "DATABASE_URL": "${DATABASE_URL}" }
    }
  }
}
```

> To add an MCP server: `claude mcp install <package>`
> To list installed: `claude mcp list`

---

## Adding a New Cache Demo Page

Follow these steps in order — Claude should complete all of them:

1. Create `app/cache/<layer>_cache.py` — implement the cache layer class
2. Create `app/routers/<layer>_demo.py` — FastAPI router for `/demo/<layer>`
3. Create `app/templates/demo/<layer>.html` — Jinja2 template with HIT/MISS badge
4. Register the router in `app/main.py`
5. Add the layer to the sidebar nav in `app/templates/base.html`
6. Write unit tests in `tests/unit/test_<layer>_cache.py`
7. Update `docs/architecture.md` with the new layer description

---

## Self-Explanatory UI Rules

Every demo page **must** include:

- **HIT/MISS badge** — green = cache hit (show latency), red = miss (show origin fetch time)
- **Annotation tooltip** — `(?)` icon quoting the relevant tip from the performance guide
- **Toggle panel** — "Cache ON / OFF" switch for live comparison
- **Expandable code view** — "Show me the code" reveals the relevant Python snippet
- **Cache key inspector** — shows the exact Redis/header key used

```html
<!-- Required badge pattern in every template -->
{% if cache_result.hit %}
  <span class="badge badge-hit">✓ CACHE HIT — {{ cache_result.latency_ms }}ms</span>
{% else %}
  <span class="badge badge-miss">✗ CACHE MISS — fetched from origin ({{ cache_result.latency_ms }}ms)</span>
{% endif %}
```

---

## Testing Conventions

```python
# Unit test pattern — mock Redis, test cache logic in isolation
@pytest.mark.asyncio
async def test_server_cache_hit(mock_redis):
    cache = RedisServerCache(redis=mock_redis)
    await cache.set("server:products:list", sample_data, ttl=300)
    result = await cache.get("server:products:list")
    assert result.hit is True
    assert result.value == sample_data

# Integration test pattern — uses real Docker services
@pytest.mark.integration
async def test_product_endpoint_cache_header(async_client):
    r1 = await async_client.get("/products")
    assert r1.headers["x-cache"] == "MISS"
    r2 = await async_client.get("/products")
    assert r2.headers["x-cache"] == "HIT"
```

---

## Ports & Services

| Service | Port | Notes |
|---|---|---|
| FastAPI | 8000 | Main application |
| Redis | 6379 | Server cache + in-memory |
| Memcached | 11211 | In-memory alternative |
| PostgreSQL | 5432 | Primary database |
| NGINX (CDN sim) | 8080 | Proxies to FastAPI with cache zones |
| Prometheus | 9090 | Metrics scraping |
| Grafana | 3000 | Dashboards (admin/admin) |

---

## Known Issues & Workarounds

- **Memcached binary protocol** — use `aiomcache` not `pymemcache` for async support
- **NGINX X-Cache header** — requires `add_header X-Cache $upstream_cache_status` in nginx.conf
- **SQLAlchemy async sessions** — always use `AsyncSession`, never `Session` in async routes
- **Redis connection pool** — initialise once in `app/main.py` lifespan, inject via `Depends()`

---

## Claude Code Tips for This Project

- Use `/clear` between unrelated tasks to keep context focused
- Use `@app/cache/` to give Claude the full cache layer context at once
- Run `/cache-flush` after any Redis schema change during development
- For CDN questions, always check `infra/nginx/cdn_sim.conf` first
- Import docs on the fly: paste a library URL and Claude will fetch it

---

*Speed · Scalability · Efficiency*
