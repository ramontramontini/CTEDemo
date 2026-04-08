"""Cte API endpoint tests — RFC 9110 Problem Details + Postman field names."""

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
    async def test_generate_valid_returns_201_with_postman_fields(self, client: AsyncClient):
        response = await client.post("/api/v1/ctes/generate", json=VALID_PAYLOAD)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert len(data["cTeKey"]) == 44
        assert " " in data["formattedAccessKey"]
        assert data["status"] == "Generated"
        assert data["freightOrderNumber"] == "12345678901234"
        assert "<?xml" in data["xml"]
        assert "createdAt" in data

    async def test_generate_valid_has_erp_and_metadata(self, client: AsyncClient):
        response = await client.post("/api/v1/ctes/generate", json=VALID_PAYLOAD)
        data = response.json()
        assert data["erp"] == "SAP"
        assert data["documentType"] == "CT-e"
        assert data["totalFolders"] == 1
        assert "updatedAt" in data

    async def test_generate_invalid_cnpj_returns_problem_details(self, client: AsyncClient):
        payload = {**VALID_PAYLOAD, "Carrier": "11111111111111"}
        response = await client.post("/api/v1/ctes/generate", json=payload)
        assert response.status_code == 422
        assert response.headers["content-type"] == "application/problem+json"
        data = response.json()
        assert data["type"] == "https://tools.ietf.org/html/rfc9110#section-15.5.1"
        assert data["title"] == "Unprocessable Entity"
        assert data["status"] == 422
        assert isinstance(data["detail"], str)
        assert "errors" in data
        assert any("Carrier" in k for k in data["errors"])

    async def test_generate_missing_fields_returns_problem_details(self, client: AsyncClient):
        payload = {"FreightOrder": "", "Folder": []}
        response = await client.post("/api/v1/ctes/generate", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert "type" in data
        assert "status" in data

    async def test_generate_invalid_cpf_returns_problem_details(self, client: AsyncClient):
        payload = {**VALID_PAYLOAD}
        payload["Folder"] = [{**VALID_PAYLOAD["Folder"][0], "DriverID": "11111111111"}]
        response = await client.post("/api/v1/ctes/generate", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert response.headers["content-type"] == "application/problem+json"
        assert "errors" in data
        assert any("DriverID" in k for k in data["errors"])

    async def test_generate_invalid_plate_returns_problem_details(self, client: AsyncClient):
        payload = {**VALID_PAYLOAD}
        payload["Folder"] = [{**VALID_PAYLOAD["Folder"][0], "VehiclePlate": "INVALID"}]
        response = await client.post("/api/v1/ctes/generate", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert "errors" in data
        assert any("VehiclePlate" in k for k in data["errors"])

    async def test_generate_multiple_errors(self, client: AsyncClient):
        payload = {
            **VALID_PAYLOAD,
            "Carrier": "11111111111111",
            "CNPJ_Origin": "99999999999999",
        }
        response = await client.post("/api/v1/ctes/generate", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert len(data["errors"]) >= 2


@pytest.mark.asyncio
class TestListAndGetCte:
    async def test_list_ctes_returns_empty(self, client: AsyncClient):
        response = await client.get("/api/v1/ctes")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_ctes_returns_postman_fields(self, client: AsyncClient):
        await client.post("/api/v1/ctes/generate", json=VALID_PAYLOAD)
        response = await client.get("/api/v1/ctes")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        item = data[0]
        assert "cTeKey" in item
        assert item["status"] == "Generated"
        assert "freightOrderNumber" in item

    async def test_get_cte_returns_full_postman_shape(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/ctes/generate", json=VALID_PAYLOAD)
        entity_id = create_resp.json()["id"]
        response = await client.get(f"/api/v1/ctes/{entity_id}")
        assert response.status_code == 200
        data = response.json()
        assert "cTeKey" in data
        assert "formattedAccessKey" in data
        assert "freightOrderNumber" in data
        assert data["erp"] == "SAP"
        assert data["documentType"] == "CT-e"
        assert data["totalFolders"] == 1
        assert "createdAt" in data
        assert "updatedAt" in data
        assert "xml" in data

    async def test_get_cte_not_found_returns_problem_details(self, client: AsyncClient):
        response = await client.get(f"/api/v1/ctes/{uuid.uuid4()}")
        assert response.status_code == 404
        assert response.headers["content-type"] == "application/problem+json"
        data = response.json()
        assert data["type"] == "https://tools.ietf.org/html/rfc9110#section-15.5.1"
        assert data["title"] == "Not Found"
        assert data["status"] == 404
        assert isinstance(data["detail"], str)
