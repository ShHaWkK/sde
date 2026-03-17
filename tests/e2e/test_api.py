"""End-to-end tests for the FastAPI application."""
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture
async def client():
    from api.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_diff_endpoint(client):
    payload = {
        "text_a": "The contract shall be terminated with 30 days notice.",
        "text_b": "The contract may be terminated at any time.",
        "domain": "legal",
        "options": {"explain": True},
    }
    resp = await client.post("/diff", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "overall" in data
    assert "global_score" in data
    assert "chunks" in data
    assert "metadata" in data
    assert 0.0 <= data["global_score"] <= 1.0


@pytest.mark.asyncio
async def test_diff_identical(client):
    payload = {
        "text_a": "Hello world.",
        "text_b": "Hello world.",
    }
    resp = await client.post("/diff", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall"] == "identical"


@pytest.mark.asyncio
async def test_batch_endpoint(client):
    payload = {
        "items": [
            {"id": 1, "text_a": "Hello world.", "text_b": "Hello world."},
            {"id": 2, "text_a": "The sky is blue.", "text_b": "The ocean is green."},
        ]
    }
    resp = await client.post("/batch", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["results"]) == 2


@pytest.mark.asyncio
async def test_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "name" in data
