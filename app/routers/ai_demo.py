from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.cache.ai_cache import AISemanticCache

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Module-level instance so the semantic index persists across requests
_ai_cache = AISemanticCache(default_ttl=600)

# Pre-defined sample prompts for the UI
SAMPLE_PROMPTS = [
    "What is Python?",
    "Explain Python",
    "What is caching?",
    "How does a CDN work?",
    "Tell me about Python programming",
]


def _generate_response(prompt: str) -> str:
    """Simulate an LLM response based on topic detection."""
    lower = prompt.lower()

    if "python" in lower:
        return (
            "Python is a high-level, interpreted programming language known for its "
            "clear syntax and readability. Created by Guido van Rossum in 1991, it "
            "supports multiple paradigms including procedural, object-oriented, and "
            "functional programming. Python is widely used in web development, data "
            "science, AI/ML, automation, and scientific computing."
        )
    elif "cach" in lower:
        return (
            "Caching is a technique that stores copies of data in a faster storage "
            "layer so future requests can be served more quickly. Caches exist at "
            "every layer of the stack: browser, CDN, server (Redis), in-memory, and "
            "database query caches. The key trade-off is freshness vs. speed."
        )
    elif "cdn" in lower:
        return (
            "A Content Delivery Network (CDN) is a geographically distributed network "
            "of servers that caches content close to end users. When a user requests "
            "content, the CDN serves it from the nearest edge node, dramatically "
            "reducing latency. Popular CDNs include Cloudflare, CloudFront, and Fastly."
        )
    else:
        return (
            "That's a great question! In a production system, this response would come "
            "from an LLM like GPT-4 or Claude. The semantic cache would store this "
            "response and match it against future similar prompts to save cost and latency."
        )


@router.get("/demo/ai-cache", response_class=HTMLResponse)
async def ai_cache_demo(request: Request, prompt: str = "What is Python?") -> Any:
    """AI Semantic Cache demo route.

    Accepts a ?prompt= query parameter, runs it through the semantic cache,
    and shows the normalization pipeline + match results.
    """
    # Check cache first (to determine match type before get modifies stats)
    match_type = _ai_cache.get_match_type(prompt)

    # Run through the cache
    result = await _ai_cache.get(prompt)

    if not result.hit:
        # Generate a simulated LLM response
        response_text = _generate_response(prompt)
        await _ai_cache.set(prompt, response_text)
        result = result.__class__(
            value=response_text, hit=False, latency_ms=result.latency_ms
        )
        match_type = "miss"

    # Build normalization pipeline display
    normalized = AISemanticCache.normalize(prompt)
    fingerprint = AISemanticCache.fingerprint(normalized)

    return templates.TemplateResponse(
        "demo/ai-cache.html",
        {
            "request": request,
            "cache_result": result,
            "prompt": prompt,
            "normalized": normalized,
            "fingerprint": fingerprint,
            "match_type": match_type,
            "stats": _ai_cache.stats,
            "sample_prompts": SAMPLE_PROMPTS,
        },
    )
