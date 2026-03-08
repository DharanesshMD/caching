from __future__ import annotations
import threading
from collections import defaultdict
from typing import Dict

# Simple in-memory metrics counters. Thread-safe since some tests or servers
# may use threads alongside the async loop.
_lock = threading.Lock()
_counters: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))


def log_hit(layer: str, key: str) -> None:
    """Record a cache hit for the given layer and key."""
    with _lock:
        _counters[layer]["hit"] += 1


def log_miss(layer: str, key: str) -> None:
    """Record a cache miss for the given layer and key."""
    with _lock:
        _counters[layer]["miss"] += 1


def get_metrics() -> Dict[str, Dict[str, int]]:
    """Return a shallow copy of the current counters for inspection/testing."""
    with _lock:
        return {layer: dict(vals) for layer, vals in _counters.items()}
