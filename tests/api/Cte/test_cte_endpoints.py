"""Cte API endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestCteEndpoints:
    async def test_list_ctes_returns_empty(self, client: AsyncClient):
        response = await client.get("/api/v1/ctes")
        assert response.status_code == 200
        assert response.json() == []

    async def test_create_cte_returns_201(self, client: AsyncClient):
        response = await client.post("/api/v1/ctes", json={"name": "Test"})
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test"
        assert "id" in data

    async def test_get_cte_returns_created(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/ctes", json={"name": "Find Me"})
        entity_id = create_resp.json()["id"]
        response = await client.get(f"/api/v1/ctes/{entity_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Find Me"

    async def test_get_cte_not_found_returns_404(self, client: AsyncClient):
        import uuid
        response = await client.get(f"/api/v1/ctes/{uuid.uuid4()}")
        assert response.status_code == 404
