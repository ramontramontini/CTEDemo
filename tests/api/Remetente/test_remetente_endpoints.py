"""Remetente API endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestRemetenteEndpoints:
    async def test_list_remetentes_returns_empty(self, client: AsyncClient):
        response = await client.get("/api/v1/remetentes")
        assert response.status_code == 200
        assert response.json() == []

    async def test_create_remetente_returns_201(self, client: AsyncClient):
        response = await client.post("/api/v1/remetentes", json={"name": "Test"})
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test"
        assert "id" in data

    async def test_get_remetente_returns_created(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/remetentes", json={"name": "Find Me"})
        entity_id = create_resp.json()["id"]
        response = await client.get(f"/api/v1/remetentes/{entity_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Find Me"

    async def test_get_remetente_not_found_returns_404(self, client: AsyncClient):
        import uuid
        response = await client.get(f"/api/v1/remetentes/{uuid.uuid4()}")
        assert response.status_code == 404
