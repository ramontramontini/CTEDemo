"""Transportadora API endpoint tests — full CRUD with CT-e fields."""

import uuid

import pytest
from httpx import AsyncClient


VALID_PAYLOAD = {
    "cnpj": "61198164000160",
    "razao_social": "Nova Transportadora Ltda",
    "nome_fantasia": "Nova Trans",
    "ie": "987654321",
    "uf": "MG",
    "cidade": "Belo Horizonte",
    "logradouro": "Av Afonso Pena",
    "numero": "500",
    "bairro": "Funcionarios",
    "cep": "30130005",
}


@pytest.mark.asyncio
class TestTransportadoraEndpoints:
    async def test_list_transportadoras(self, client: AsyncClient):
        response = await client.get("/api/v1/transportadoras")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_create_transportadora_with_all_fields(self, client: AsyncClient):
        response = await client.post("/api/v1/transportadoras", json=VALID_PAYLOAD)
        assert response.status_code == 201
        data = response.json()
        assert data["cnpj"] == "61198164000160"
        assert data["razao_social"] == "Nova Transportadora Ltda"
        assert data["uf"] == "MG"
        assert data["status"] == "active"
        assert "id" in data

    async def test_get_transportadora_returns_created(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/transportadoras", json=VALID_PAYLOAD)
        entity_id = create_resp.json()["id"]
        response = await client.get(f"/api/v1/transportadoras/{entity_id}")
        assert response.status_code == 200
        assert response.json()["cnpj"] == "61198164000160"

    async def test_get_transportadora_not_found_returns_404(self, client: AsyncClient):
        response = await client.get(f"/api/v1/transportadoras/{uuid.uuid4()}")
        assert response.status_code == 404

    async def test_create_rejects_invalid_cnpj(self, client: AsyncClient):
        payload = {**VALID_PAYLOAD, "cnpj": "00000000000000"}
        response = await client.post("/api/v1/transportadoras", json=payload)
        assert response.status_code == 422

    async def test_create_rejects_duplicate_cnpj(self, client: AsyncClient):
        await client.post("/api/v1/transportadoras", json=VALID_PAYLOAD)
        response = await client.post("/api/v1/transportadoras", json=VALID_PAYLOAD)
        assert response.status_code == 422

    async def test_update_transportadora(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/transportadoras", json=VALID_PAYLOAD)
        entity_id = create_resp.json()["id"]
        response = await client.patch(
            f"/api/v1/transportadoras/{entity_id}",
            json={"razao_social": "Updated Name"},
        )
        assert response.status_code == 200
        assert response.json()["razao_social"] == "Updated Name"

    async def test_update_not_found(self, client: AsyncClient):
        response = await client.patch(
            f"/api/v1/transportadoras/{uuid.uuid4()}",
            json={"razao_social": "Nope"},
        )
        assert response.status_code == 404

    async def test_delete_transportadora(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/transportadoras", json=VALID_PAYLOAD)
        entity_id = create_resp.json()["id"]
        response = await client.delete(f"/api/v1/transportadoras/{entity_id}")
        assert response.status_code == 204

    async def test_delete_not_found(self, client: AsyncClient):
        response = await client.delete(f"/api/v1/transportadoras/{uuid.uuid4()}")
        assert response.status_code == 404

    async def test_list_returns_seeded_data(self, client: AsyncClient):
        """Seed data: at least 2 transportadoras with valid CNPJs pre-loaded."""
        response = await client.get("/api/v1/transportadoras")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        for item in data[:2]:
            assert len(item["cnpj"]) == 14
            assert item["razao_social"]
            assert item["uf"]
