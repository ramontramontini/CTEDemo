"""Remetente API endpoint tests."""

import uuid

import pytest
from httpx import AsyncClient


VALID_CNPJ = "11222333000181"
VALID_CNPJ_2 = "11444777000161"


def _valid_payload(**overrides):
    defaults = {
        "cnpj": VALID_CNPJ,
        "razao_social": "Empresa ABC Ltda",
        "nome_fantasia": "ABC",
        "ie": "123456789",
        "uf": "SP",
        "cidade": "São Paulo",
        "logradouro": "Rua das Flores",
        "numero": "100",
        "bairro": "Centro",
        "cep": "01001000",
    }
    defaults.update(overrides)
    return defaults


@pytest.mark.asyncio
class TestRemetenteEndpoints:
    async def test_list_remetentes_returns_empty(self, client: AsyncClient):
        response = await client.get("/api/v1/remetentes")
        assert response.status_code == 200
        assert response.json() == []

    async def test_create_remetente_returns_201(self, client: AsyncClient):
        response = await client.post("/api/v1/remetentes", json=_valid_payload())
        assert response.status_code == 201
        data = response.json()
        assert data["cnpj"] == VALID_CNPJ
        assert data["razao_social"] == "Empresa ABC Ltda"
        assert data["uf"] == "SP"
        assert data["cep"] == "01001000"
        assert "id" in data

    async def test_get_remetente_returns_created(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/remetentes", json=_valid_payload())
        entity_id = create_resp.json()["id"]
        response = await client.get(f"/api/v1/remetentes/{entity_id}")
        assert response.status_code == 200
        assert response.json()["cnpj"] == VALID_CNPJ

    async def test_get_remetente_not_found_returns_404(self, client: AsyncClient):
        response = await client.get(f"/api/v1/remetentes/{uuid.uuid4()}")
        assert response.status_code == 404

    async def test_create_invalid_cnpj_returns_422(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/remetentes", json=_valid_payload(cnpj="12345678901234")
        )
        assert response.status_code == 422

    async def test_create_duplicate_cnpj_returns_409(self, client: AsyncClient):
        await client.post("/api/v1/remetentes", json=_valid_payload())
        response = await client.post("/api/v1/remetentes", json=_valid_payload())
        assert response.status_code == 409

    async def test_patch_remetente_updates_fields(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/remetentes", json=_valid_payload())
        entity_id = create_resp.json()["id"]
        response = await client.patch(
            f"/api/v1/remetentes/{entity_id}",
            json={"razao_social": "Updated Name", "cidade": "Campinas"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["razao_social"] == "Updated Name"
        assert data["cidade"] == "Campinas"
        assert data["cnpj"] == VALID_CNPJ  # immutable

    async def test_patch_not_found_returns_404(self, client: AsyncClient):
        response = await client.patch(
            f"/api/v1/remetentes/{uuid.uuid4()}",
            json={"razao_social": "X"},
        )
        assert response.status_code == 404

    async def test_delete_remetente_returns_204(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/remetentes", json=_valid_payload())
        entity_id = create_resp.json()["id"]
        response = await client.delete(f"/api/v1/remetentes/{entity_id}")
        assert response.status_code == 204

    async def test_get_after_delete_returns_404(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/remetentes", json=_valid_payload())
        entity_id = create_resp.json()["id"]
        await client.delete(f"/api/v1/remetentes/{entity_id}")
        response = await client.get(f"/api/v1/remetentes/{entity_id}")
        assert response.status_code == 404

    async def test_delete_not_found_returns_404(self, client: AsyncClient):
        response = await client.delete(f"/api/v1/remetentes/{uuid.uuid4()}")
        assert response.status_code == 404
