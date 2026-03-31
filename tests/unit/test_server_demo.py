import pytest

from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    # Ensure app lifespan events run so app.state.redis is initialized
    with TestClient(app) as client:
        yield client


def test_demo_page_renders(client):
    resp = client.get("/demo/server")
    assert resp.status_code == 200
    text = resp.text
    assert "Server / Redis Cache" in text
    # Should include either HIT or MISS badge text
    assert "CACHE HIT" in text or "CACHE MISS" in text
    # X-Cache header should be present
    assert "X-Cache" in resp.headers


def test_demo_page_has_educational_content(client):
    resp = client.get("/demo/server")
    text = resp.text
    # Educational sections should be present
    assert "What is Server-Side Caching?" in text
    assert "How It Works" in text
    assert "Pros" in text
    assert "Cons" in text
    assert "Real-World Use Cases" in text
    assert "Key Concepts" in text
    assert "Code Inspector" in text
    # Key terms
    assert "TTL" in text
    assert "Serialization" in text
    assert "Cache Stampede" in text
