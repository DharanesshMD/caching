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
    assert "Server cache demo" in text
    # Should include either HIT or MISS badge text
    assert "CACHE HIT" in text or "CACHE MISS" in text
    # X-Cache header should be present
    assert "X-Cache" in resp.headers
