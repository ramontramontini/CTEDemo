"""Destinatario API endpoint tests."""

import uuid

import pytest
from httpx import AsyncClient


VALID_CNPJ = "11222333000181"
VALID_CNPJ_2 = "11444777000161"
VALID_CPF = "12345678909"


def _pj_payload(**overrides):
    defaults = {
        "cnpj": VALID_CNPJ,
        "razao_social": "Empresa Teste",
        "uf": "PE",
        "cidade": "Recife",
        "logradouro": "Rua X",
        "numero": "1",
        "bairro": "Centro",
        "cep": "50060000",
    }
    defaults.update(overrides)
    return defaults


def _pf_payload(**overrides):
    defaults = {
        "cpf": VALID_CPF,
        "razao_social": "Maria Silva",
        "uf": "SP",
        "cidade": "São Paulo",
        "logradouro": "Av Paulista",
        "numero": "100",
        "bairro": "Bela Vista",
        "cep": "01310100",
    }
    defaults.update(overrides)
    return defaults


@pytest.mark.asyncio
class TestDestinatarioEndpoints:
    async def test_list_returns_empty(self, client: AsyncClient):
        response = await client.get("/api/v1/destinatarios")
        assert response.status_code == 200
        assert response.json() == []

    async def test_create_pj_returns_201(self, client: AsyncClient):
        response = await client.post("/api/v1/destinatarios", json=_pj_payload())
        assert response.status_code == 201
        data = response.json()
        assert data["cnpj"] == VALID_CNPJ
        assert data["cpf"] is None
        assert data["razao_social"] == "Empresa Teste"
        assert data["uf"] == "PE"
        assert "id" in data

    async def test_create_pf_returns_201(self, client: AsyncClient):
        response = await client.post("/api/v1/destinatarios", json=_pf_payload())
        assert response.status_code == 201
        data = response.json()
        assert data["cpf"] == VALID_CPF
        assert data["cnpj"] is None
        assert data["razao_social"] == "Maria Silva"

    async def test_get_by_id_returns_200(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/destinatarios", json=_pj_payload())
        entity_id = create_resp.json()["id"]
        response = await client.get(f"/api/v1/destinatarios/{entity_id}")
        assert response.status_code == 200
        assert response.json()["cnpj"] == VALID_CNPJ

    async def test_get_not_found_returns_404(self, client: AsyncClient):
        response = await client.get(f"/api/v1/destinatarios/{uuid.uuid4()}")
        assert response.status_code == 404

    async def test_create_invalid_cnpj_returns_422(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/destinatarios", json=_pj_payload(cnpj="12345678901234"),
        )
        assert response.status_code == 422

    async def test_create_both_cnpj_and_cpf_returns_422(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/destinatarios",
            json=_pj_payload(cpf=VALID_CPF),
        )
        assert response.status_code == 422

    async def test_create_neither_cnpj_nor_cpf_returns_422(self, client: AsyncClient):
        payload = {
            "razao_social": "Test",
            "uf": "SP",
            "cidade": "SP",
            "logradouro": "Rua",
            "numero": "1",
            "bairro": "B",
            "cep": "01001000",
        }
        response = await client.post("/api/v1/destinatarios", json=payload)
        assert response.status_code == 422

    async def test_create_duplicate_cnpj_returns_409(self, client: AsyncClient):
        await client.post("/api/v1/destinatarios", json=_pj_payload())
        response = await client.post("/api/v1/destinatarios", json=_pj_payload())
        assert response.status_code == 409

    async def test_patch_returns_200(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/destinatarios", json=_pj_payload())
        entity_id = create_resp.json()["id"]
        response = await client.patch(
            f"/api/v1/destinatarios/{entity_id}",
            json={"razao_social": "Updated Name"},
        )
        assert response.status_code == 200
        assert response.json()["razao_social"] == "Updated Name"

    async def test_patch_not_found_returns_404(self, client: AsyncClient):
        response = await client.patch(
            f"/api/v1/destinatarios/{uuid.uuid4()}",
            json={"razao_social": "Nope"},
        )
        assert response.status_code == 404

    async def test_delete_returns_204(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/destinatarios", json=_pj_payload())
        entity_id = create_resp.json()["id"]
        response = await client.delete(f"/api/v1/destinatarios/{entity_id}")
        assert response.status_code == 204

    async def test_delete_not_found_returns_404(self, client: AsyncClient):
        response = await client.delete(f"/api/v1/destinatarios/{uuid.uuid4()}")
        assert response.status_code == 404

    async def test_list_returns_created_entities(self, client: AsyncClient):
        await client.post("/api/v1/destinatarios", json=_pj_payload())
        await client.post("/api/v1/destinatarios", json=_pf_payload())
        response = await client.get("/api/v1/destinatarios")
        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_create_pj_response_has_all_fields(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/destinatarios",
            json=_pj_payload(nome_fantasia="Teste ME", ie="123456789"),
        )
        data = response.json()
        assert data["nome_fantasia"] == "Teste ME"
        assert data["ie"] == "123456789"
        assert data["cidade"] == "Recife"
        assert data["logradouro"] == "Rua X"
        assert data["numero"] == "1"
        assert data["bairro"] == "Centro"
        assert data["cep"] == "50060000"
        assert data["status"] == "active"
        assert "created_at" in data
