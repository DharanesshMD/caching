"""Unit tests for AISemanticCache."""
import pytest

from app.cache.ai_cache import AISemanticCache


@pytest.fixture
def cache():
    return AISemanticCache(default_ttl=300)


@pytest.mark.asyncio
async def test_exact_set_get(cache):
    """Exact same prompt should return a HIT."""
    await cache.set("What is Python?", "Python is a programming language.")
    result = await cache.get("What is Python?")
    assert result.hit is True
    assert result.value == "Python is a programming language."


@pytest.mark.asyncio
async def test_empty_cache_miss(cache):
    """Empty cache should return a MISS."""
    result = await cache.get("What is Python?")
    assert result.hit is False
    assert result.value is None


@pytest.mark.asyncio
async def test_semantic_match_reordered_words(cache):
    """Prompts with reordered words should match semantically."""
    await cache.set("What is Python?", "Python is a language.")
    # "what python" normalizes the same tokens; reordering doesn't matter since we sort
    result = await cache.get("Python what is?")
    assert result.hit is True
    assert result.value == "Python is a language."


@pytest.mark.asyncio
async def test_semantic_match_stopwords(cache):
    """Prompts differing only by stopwords should match."""
    await cache.set("explain the Python language", "Python explanation.")
    # "Explain Python language" — "the" is a stopword, should still match
    result = await cache.get("explain Python language")
    assert result.hit is True
    assert result.value == "Python explanation."


@pytest.mark.asyncio
async def test_delete(cache):
    """Deleting a key should remove it from cache."""
    await cache.set("What is Python?", "Python info.")
    await cache.delete("What is Python?")
    result = await cache.get("What is Python?")
    assert result.hit is False


@pytest.mark.asyncio
async def test_stats_tracking(cache):
    """Stats should track exact hits, semantic hits, and misses."""
    await cache.set("What is Python?", "Python info.")

    # Miss
    await cache.get("What is JavaScript?")
    assert cache.stats.misses == 1

    # Exact hit
    await cache.get("What is Python?")
    assert cache.stats.exact_hits == 1

    # Semantic hit (different word order, stopwords differ)
    await cache.get("Python what?")
    assert cache.stats.semantic_hits == 1


@pytest.mark.asyncio
async def test_normalization():
    """Test the normalization pipeline."""
    assert AISemanticCache.normalize("What is Python?") == "python"
    assert AISemanticCache.normalize("THE Quick BROWN Fox!") == "brown fox quick"
    assert AISemanticCache.normalize("  hello   world  ") == "hello world"


@pytest.mark.asyncio
async def test_no_false_matches(cache):
    """Completely different prompts should not match."""
    await cache.set("What is Python?", "Python info.")
    result = await cache.get("How do airplanes fly?")
    assert result.hit is False


@pytest.mark.asyncio
async def test_fingerprint_deterministic():
    """Same input should always produce the same fingerprint."""
    fp1 = AISemanticCache.fingerprint("python")
    fp2 = AISemanticCache.fingerprint("python")
    assert fp1 == fp2
    assert len(fp1) == 64  # SHA-256 hex digest length
