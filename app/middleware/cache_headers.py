from __future__ import annotations
from typing import Dict

# Lightweight helper for demo templates. In production this would construct
# Cache-Control and ETag headers. Here we return a dict for template rendering.

def build_browser_headers(ttl: int = 31536000, etag: str | None = None) -> Dict[str, str]:
    headers = {"Cache-Control": f"public, max-age={ttl}"}
    if etag:
        headers["ETag"] = etag
    return headers
