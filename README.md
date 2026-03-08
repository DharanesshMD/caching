# CacheWise

An educational platform demonstrating all five caching types (Browser, Server, CDN, Database, In-Memory) with live HIT/MISS badges, latency comparisons, and interactive UI.

## Overview

CacheWise is a FastAPI-based web application that teaches caching concepts through interactive demos. Each demo page shows how a specific caching layer works with real-time feedback on cache hits and misses.

### Features

- **5 Cache Types**: Browser, Server, CDN, Database, In-Memory
- **Live HIT/MISS Indicators**: Visual badges showing cache behavior
- **Latency Comparison**: Measure the time difference between cache hits and misses
- **Toggle Controls**: Turn caching on/off for live comparison
- **Code Inspector**: View the implementation code for each cache layer
- **Cache Key Inspector**: See the exact cache keys used

## Architecture

```
cachewise/
├── app/
│   ├── main.py                 # FastAPI app factory with Redis lifecycle
│   ├── cache/                  # One file per cache layer
│   │   ├── base.py             # AsyncCache protocol & CacheResult
│   │   ├── browser_cache.py    # Cache-Control / ETag headers
│   │   ├── server_cache.py     # Redis server-side cache
│   │   ├── cdn_cache.py        # CDN header simulation
│   │   ├── db_cache.py         # SQLAlchemy query cache
│   │   └── in_memory.py        # In-memory caching
│   ├── middleware/
│   │   ├── cache_headers.py    # Global Cache-Control middleware
│   │   └── metrics.py          # Prometheus hit/miss counters
│   ├── routers/                # Demo route handlers
│   │   ├── browser_demo.py
│   │   ├── server_demo.py
│   │   ├── cdn_demo.py
│   │   ├── db_demo.py
│   │   └── in_memory_demo.py
│   ├── templates/              # Jinja2 HTML templates
│   └── deps.py                 # Dependency injection helpers
├── tests/
│   └── unit/                   # Unit tests
├── plan.md                     # Project memory for Claude Code
└── requirements-dev.txt        # Development dependencies
```

### Cache Layer Patterns

Every cache layer follows the same pattern:

```python
# Each cache method returns CacheResult(value, hit: bool, latency_ms: float)
class RedisServerCache(AsyncCache[Any]):
    async def get(self, key: str) -> CacheResult[Any]: ...
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None: ...
    async def delete(self, key: str) -> None: ...
```

### Default TTL Values

| Layer    | TTL (seconds) |
|----------|---------------|
| Browser  | 31536000      |
| Server   | 300           |
| CDN      | 3600          |
| Database | 600           |
| In-Memory| 60            |

## Development Process

This project was developed using Claude Code (formerly Claude Dev) with an AI-first approach:

### 1. Planning Phase

The development started by creating a detailed plan in `plan.md`. This file serves as the "project memory" that Claude Code loads automatically at every session start.

**Key elements of the plan:**

- Project overview and tech stack
- Essential commands for development
- Project structure and conventions
- Coding standards (Python 3.12+, async/await, type hints)
- Cache layer conventions
- Environment variables
- Custom slash commands
- UI rules for self-explanatory demos

### 2. Execution with Claude Code

The development was executed through iterative conversations with Claude Code:

1. **Initial scaffolding**: Created the FastAPI app factory with Redis lifecycle management
2. **Cache base layer**: Implemented the `AsyncCache` protocol and `CacheResult` dataclass
3. **Server cache**: Built the Redis-backed server cache with JSON serialization
4. **Demo routes**: Created routers for each demo page
5. **UI templates**: Built interactive templates with HIT/MISS badges, toggles, and code panels
6. **Additional cache layers**: Added Browser, CDN, Database, and In-Memory demos

### 3. Commands Used

Claude Code was invoked using custom slash commands defined in `.claude/commands/`:

- `/cache-flush` - Flushes Redis cache and prints hit stats
- `/add-endpoint` - Scaffolds a new demo route and template
- `/run-demo` - Starts the application and opens browser

### 4. Testing

Unit tests were written following the pattern:

```python
@pytest.mark.asyncio
async def test_server_cache_hit(mock_redis):
    cache = RedisServerCache(redis=mock_redis)
    await cache.set("server:products:list", sample_data, ttl=300)
    result = await cache.get("server:products:list")
    assert result.hit is True
    assert result.value == sample_data
```

## Installation

### Prerequisites

- Python 3.12+
- Redis (for server and in-memory caching)

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd caching
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Set environment variables (optional):
   ```bash
   export REDIS_URL=redis://localhost:6379/0
   export DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/cachewise
   ```

## Running the Application

### Development Mode

Start the FastAPI development server:

```bash
uvicorn app.main:app --reload --port 8000
```

The application will be available at http://localhost:8000

### Demo Pages

- Server Cache: http://localhost:8000/demo/server
- Browser Cache: http://localhost:8000/demo/browser
- CDN Cache: http://localhost:8000/demo/cdn
- Database Cache: http://localhost:8000/demo/database
- In-Memory Cache: http://localhost:8000/demo/in-memory

## Testing

### Run All Tests

```bash
pytest
```

### Run Unit Tests Only

```bash
pytest tests/unit/
```

### Run Specific Test

```bash
pytest tests/unit/test_server_demo.py
pytest -k "browser_cache"
```

### Test with Coverage

```bash
pytest --cov=app tests/unit/
```

## Code Quality

### Linting

```bash
ruff check .
```

### Type Checking

```bash
mypy app/
```

### Formatting

```bash
ruff format .
```

### Pre-commit Check

Before committing, run:

```bash
ruff check . && mypy app/ && pytest tests/unit/
```

## Technology Stack

- **Framework**: FastAPI
- **Caching**: Redis, Memcached
- **Database**: PostgreSQL
- **Templates**: Jinja2
- **Testing**: pytest, pytest-asyncio
- **Linting**: ruff, mypy

## Contributing

1. Create a feature branch: `feature/your-feature-name`
2. Make your changes following the coding standards
3. Run tests and type checks
4. Commit using Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`
5. Submit a pull request

## System Design

This comprehensive caching system design was created by Dharanessh MD. The architecture, implementation patterns, and educational approach were designed specifically for teaching caching concepts through interactive demonstrations.