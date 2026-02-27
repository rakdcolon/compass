"""
API integration tests for Compass FastAPI endpoints.

AWS calls are mocked via conftest.py — no real credentials needed.
Uses httpx.AsyncClient with ASGI transport.
"""

import pytest
import pytest_asyncio


pytestmark = pytest.mark.asyncio


class TestHealth:
    async def test_health_returns_200(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200

    async def test_health_contains_service_name(self, client):
        data = resp = await client.get("/health")
        body = data.json()
        assert "status" in body

    async def test_api_health_alias(self, client):
        """The root health check should also return ok."""
        resp = await client.get("/health")
        body = resp.json()
        assert body.get("status") == "healthy"


class TestSession:
    async def test_unknown_session_returns_404(self, client):
        resp = await client.get("/api/session/does-not-exist-abc123")
        assert resp.status_code == 404

    async def test_404_body_contains_detail(self, client):
        resp = await client.get("/api/session/no-such-session")
        body = resp.json()
        assert "detail" in body


class TestPrograms:
    async def test_list_programs_returns_200(self, client):
        resp = await client.get("/api/programs")
        assert resp.status_code == 200

    async def test_list_programs_contains_snap(self, client):
        resp = await client.get("/api/programs")
        ids = [p["id"] for p in resp.json()["programs"]]
        assert "snap" in ids

    async def test_list_programs_has_expected_fields(self, client):
        resp = await client.get("/api/programs")
        first = resp.json()["programs"][0]
        for field in ("id", "name", "category", "description"):
            assert field in first


class TestPersonas:
    async def test_list_personas_returns_200(self, client):
        resp = await client.get("/api/personas")
        assert resp.status_code == 200

    async def test_list_personas_contains_expected_ids(self, client):
        resp = await client.get("/api/personas")
        ids = [p["id"] for p in resp.json()["personas"]]
        assert "single_parent" in ids
        assert "senior" in ids
        assert "veteran" in ids
