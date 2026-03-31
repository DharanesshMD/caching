"""Tests for the home page."""
import pytest

from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def test_home_page_renders(client):
    resp = client.get("/")
    assert resp.status_code == 200
    text = resp.text
    assert "Welcome to CacheWise" in text


def test_home_page_has_all_layer_names(client):
    resp = client.get("/")
    text = resp.text
    assert "Browser Cache" in text
    assert "CDN Cache" in text
    assert "Server / Redis Cache" in text
    assert "In-Memory Cache" in text
    assert "Database Cache" in text
    assert "AI Semantic Cache" in text


def test_home_page_has_demo_links(client):
    resp = client.get("/")
    text = resp.text
    assert "/demo/browser" in text
    assert "/demo/cdn" in text
    assert "/demo/server" in text
    assert "/demo/in-memory" in text
    assert "/demo/database" in text
    assert "/demo/ai-cache" in text
