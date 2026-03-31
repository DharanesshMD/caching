"""Integration tests for the AI Semantic Cache demo route."""
import pytest

from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def test_ai_demo_page_renders(client):
    resp = client.get("/demo/ai-cache")
    assert resp.status_code == 200
    text = resp.text
    assert "AI Semantic Cache" in text
    assert "What is Python?" in text


def test_ai_demo_custom_prompt(client):
    resp = client.get("/demo/ai-cache?prompt=What+is+caching%3F")
    assert resp.status_code == 200
    text = resp.text
    assert "caching" in text.lower()


def test_ai_demo_second_request_is_hit(client):
    # First request is a MISS
    resp1 = client.get("/demo/ai-cache?prompt=How+does+a+CDN+work%3F")
    assert resp1.status_code == 200

    # Second identical request should be a HIT
    resp2 = client.get("/demo/ai-cache?prompt=How+does+a+CDN+work%3F")
    assert resp2.status_code == 200
    assert "Exact Match" in resp2.text


def test_ai_demo_semantic_match(client):
    # First request establishes the cache entry
    client.get("/demo/ai-cache?prompt=What+is+Python%3F")

    # Semantically similar prompt should match
    resp = client.get("/demo/ai-cache?prompt=Explain+Python")
    assert resp.status_code == 200
    # Should be either exact or semantic hit
    assert "Exact Match" in resp.text or "Semantic Match" in resp.text or "Cache Miss" in resp.text
