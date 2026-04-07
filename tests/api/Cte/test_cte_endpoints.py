"""Cte API endpoint tests."""

import uuid

import pytest
from httpx import AsyncClient


VALID_PAYLOAD = {
    "FreightOrder": "12345678901234",
    "ERP": "SAP",
    "Carrier": "10758386000159",
    "CNPJ_Origin": "10758386000159",
    "Incoterms": "CIF",
    "OperationType": "0",
    "Folder": [
        {
            "FolderNumber": "001",
            "ReferenceNumber": "REF001",
            "NetValue": 1500.00,
            "VehiclePlate": "ABC1D23",
            "TrailerPlate": [],
            "VehicleAxles": "2",
            "EquipmentType": "TRUCK",
            "Weight": 5000.00,
            "CFOP": "6352",
            "DriverID": "12345678909",
            "Cancel": False,
            "Tax": [
                {
                    "TaxType": "ICMS",
                    "Base": 1500.00,
                    "Rate": 12.00,
                    "Value": 180.00,
                    "TaxCode": "00",
                    "ReducedBase": 0,
                }
            ],
            "RelatedNFE": ["12345678901234567890123456789012345678901234"],
        }
    ],
}


@pytest.mark.asyncio
class TestGenerateCte:
    async def test_generate_valid_returns_201(self, client: AsyncClient):
        response = await client.post("/api/v1/ctes/generate", json=VALID_PAYLOAD)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert len(data["access_key"]) == 44
        assert " " in data["formatted_access_key"]
        assert data["status"] == "gerado"
        assert data["freight_order_number"] == "12345678901234"
        assert "<?xml" in data["xml"]
        assert "created_at" in data

    async def test_generate_invalid_cnpj_returns_422(self, client: AsyncClient):
        payload = {**VALID_PAYLOAD, "Carrier": "11111111111111"}
        response = await client.post("/api/v1/ctes/generate", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert any("Carrier" in e["field"] for e in data["detail"])

    async def test_generate_missing_fields_returns_422(self, client: AsyncClient):
        payload = {"FreightOrder": "", "Folder": []}
        response = await client.post("/api/v1/ctes/generate", json=payload)
        assert response.status_code == 422

    async def test_generate_invalid_cpf_returns_422(self, client: AsyncClient):
        payload = {**VALID_PAYLOAD}
        payload["Folder"] = [{**VALID_PAYLOAD["Folder"][0], "DriverID": "11111111111"}]
        response = await client.post("/api/v1/ctes/generate", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert any("DriverID" in e["field"] for e in data["detail"])

    async def test_generate_invalid_plate_returns_422(self, client: AsyncClient):
        payload = {**VALID_PAYLOAD}
        payload["Folder"] = [{**VALID_PAYLOAD["Folder"][0], "VehiclePlate": "INVALID"}]
        response = await client.post("/api/v1/ctes/generate", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert any("VehiclePlate" in e["field"] for e in data["detail"])

    async def test_generate_multiple_errors_in_single_request(self, client: AsyncClient):
        payload = {
            **VALID_PAYLOAD,
            "Carrier": "11111111111111",
            "CNPJ_Origin": "99999999999999",
        }
        response = await client.post("/api/v1/ctes/generate", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert len(data["detail"]) >= 2


@pytest.mark.asyncio
class TestListAndGetCte:
    async def test_list_ctes_returns_empty(self, client: AsyncClient):
        response = await client.get("/api/v1/ctes")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_ctes_returns_generated(self, client: AsyncClient):
        await client.post("/api/v1/ctes/generate", json=VALID_PAYLOAD)
        response = await client.get("/api/v1/ctes")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert "access_key" in data[0]
        assert "status" in data[0]
        assert "freight_order_number" in data[0]

    async def test_get_cte_returns_detail(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/ctes/generate", json=VALID_PAYLOAD)
        entity_id = create_resp.json()["id"]
        response = await client.get(f"/api/v1/ctes/{entity_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["access_key"] is not None
        assert "xml" in data

    async def test_get_cte_not_found_returns_404(self, client: AsyncClient):
        response = await client.get(f"/api/v1/ctes/{uuid.uuid4()}")
        assert response.status_code == 404
