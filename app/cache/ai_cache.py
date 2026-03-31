"""AI Semantic Cache — simulates semantic/embedding-based caching for LLM prompts.

Uses token normalization and SHA-256 fingerprinting to match exact and semantically
similar prompts without any ML dependencies.
"""
from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .base import AsyncCache, CacheResult


# Common English stopwords to strip during normalization
_STOPWORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "about", "it", "its",
    "this", "that", "these", "those", "i", "me", "my", "we", "our", "you",
    "your", "he", "she", "they", "them", "what", "which", "who", "whom",
})


@dataclass
class _CacheEntry:
    value: Any
    fingerprint: str
    normalized: str
    expires_at: Optional[float]


@dataclass
class AISemanticCacheStats:
    exact_hits: int = 0
    semantic_hits: int = 0
    misses: int = 0
    estimated_cost_saved: float = 0.0


class AISemanticCache(AsyncCache[Any]):
    """Simulates semantic caching for LLM prompts.

    Normalization pipeline:
      1. Lowercase
      2. Remove punctuation
      3. Strip stopwords
      4. Sort remaining tokens alphabetically

    Fingerprinting:
      - SHA-256 of the normalized token string

    Semantic matching:
      - Generate n-1 gram variants (drop each token once)
      - Each variant gets its own fingerprint
      - Stored in an index for O(1) lookup
    """

    def __init__(self, default_ttl: int = 600) -> None:
        self._store: Dict[str, _CacheEntry] = {}  # fingerprint -> entry
        self._variant_index: Dict[str, str] = {}  # variant_fp -> canonical_fp
        self._default_ttl = default_ttl
        self.stats = AISemanticCacheStats()

    # ── Normalization pipeline ──

    @staticmethod
    def normalize(text: str) -> str:
        """Normalize text: lowercase, remove punctuation, strip stopwords, sort tokens."""
        text = text.lower()
        text = re.sub(r"[^\w\s]", "", text)
        tokens = text.split()
        tokens = [t for t in tokens if t not in _STOPWORDS]
        tokens.sort()
        return " ".join(tokens)

    @staticmethod
    def fingerprint(normalized: str) -> str:
        """SHA-256 hash of the normalized text."""
        return hashlib.sha256(normalized.encode()).hexdigest()

    @staticmethod
    def _generate_variants(normalized: str) -> List[str]:
        """Generate n-1 gram variants for fuzzy matching.

        For a normalized string with N tokens, generate N variants each
        missing one token. This allows matching prompts that are similar
        but have one word different or missing.
        """
        tokens = normalized.split()
        if len(tokens) <= 1:
            return []
        variants = []
        for i in range(len(tokens)):
            variant = " ".join(tokens[:i] + tokens[i + 1:])
            variants.append(variant)
        return variants

    # ── Cleanup ──

    async def _cleanup(self) -> None:
        now = time.time()
        expired = [
            fp for fp, entry in self._store.items()
            if entry.expires_at is not None and entry.expires_at < now
        ]
        for fp in expired:
            # Remove variant index entries pointing to this fingerprint
            to_remove = [k for k, v in self._variant_index.items() if v == fp]
            for k in to_remove:
                del self._variant_index[k]
            del self._store[fp]

    # ── AsyncCache protocol ──

    async def get(self, key: str) -> CacheResult[Any]:
        """Look up a prompt. Key is the raw prompt text."""
        start = time.perf_counter()
        await self._cleanup()

        normalized = self.normalize(key)
        fp = self.fingerprint(normalized)

        # Exact match
        entry = self._store.get(fp)
        if entry is not None:
            latency_ms = (time.perf_counter() - start) * 1000.0
            self.stats.exact_hits += 1
            self.stats.estimated_cost_saved += 0.03  # ~$0.03 per LLM call
            return CacheResult(value=entry.value, hit=True, latency_ms=latency_ms)

        # Semantic match via variant index
        variants = self._generate_variants(normalized)
        for variant in variants:
            variant_fp = self.fingerprint(variant)
            canonical_fp = self._variant_index.get(variant_fp)
            if canonical_fp and canonical_fp in self._store:
                latency_ms = (time.perf_counter() - start) * 1000.0
                self.stats.semantic_hits += 1
                self.stats.estimated_cost_saved += 0.03
                return CacheResult(
                    value=self._store[canonical_fp].value,
                    hit=True,
                    latency_ms=latency_ms,
                )

        latency_ms = (time.perf_counter() - start) * 1000.0
        self.stats.misses += 1
        return CacheResult(value=None, hit=False, latency_ms=latency_ms)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store a prompt-response pair with semantic indexing."""
        ttl = ttl or self._default_ttl
        normalized = self.normalize(key)
        fp = self.fingerprint(normalized)
        expires_at = time.time() + ttl if ttl else None

        entry = _CacheEntry(
            value=value,
            fingerprint=fp,
            normalized=normalized,
            expires_at=expires_at,
        )
        self._store[fp] = entry

        # Index variants for semantic matching
        variants = self._generate_variants(normalized)
        for variant in variants:
            variant_fp = self.fingerprint(variant)
            self._variant_index[variant_fp] = fp

    async def delete(self, key: str) -> None:
        """Remove a prompt and its variant index entries."""
        normalized = self.normalize(key)
        fp = self.fingerprint(normalized)

        if fp in self._store:
            # Clean up variant index
            to_remove = [k for k, v in self._variant_index.items() if v == fp]
            for k in to_remove:
                del self._variant_index[k]
            del self._store[fp]

    def get_match_type(self, key: str) -> str:
        """Return the match type for a prompt without modifying stats.

        Returns 'exact', 'semantic', or 'miss'.
        """
        normalized = self.normalize(key)
        fp = self.fingerprint(normalized)

        if fp in self._store:
            return "exact"

        variants = self._generate_variants(normalized)
        for variant in variants:
            variant_fp = self.fingerprint(variant)
            canonical_fp = self._variant_index.get(variant_fp)
            if canonical_fp and canonical_fp in self._store:
                return "semantic"

        return "miss"
