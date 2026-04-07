"""Destinatario API endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestDestinatarioEndpoints:
    async def test_list_destinatarios_returns_empty(self, client: AsyncClient):
        response = await client.get("/api/v1/destinatarios")
        assert response.status_code == 200
        assert response.json() == []

    async def test_create_destinatario_returns_201(self, client: AsyncClient):
        response = await client.post("/api/v1/destinatarios", json={"name": "Test"})
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test"
        assert "id" in data

    async def test_get_destinatario_returns_created(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/destinatarios", json={"name": "Find Me"})
        entity_id = create_resp.json()["id"]
        response = await client.get(f"/api/v1/destinatarios/{entity_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Find Me"

    async def test_get_destinatario_not_found_returns_404(self, client: AsyncClient):
        import uuid
        response = await client.get(f"/api/v1/destinatarios/{uuid.uuid4()}")
        assert response.status_code == 404
