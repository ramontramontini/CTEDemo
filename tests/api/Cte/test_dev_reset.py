"""Tests for POST /api/v1/dev/reset-data endpoint."""

import pytest


@pytest.mark.asyncio
async def test_reset_data_returns_200(client):
    """Reset endpoint returns 200 with success message."""
    response = await client.post("/api/v1/dev/reset-data")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["message"] == "Dados resetados com sucesso"


@pytest.mark.asyncio
async def test_reset_clears_generated_ctes(client):
    """After generating a CT-e then resetting, CT-e list is empty."""
    from src.infrastructure.database.repositories.provider import get_repository_provider

    provider = get_repository_provider()
    provider.get_remetente_repository().seed_if_empty()
    provider.get_destinatario_repository().seed_if_empty()
    provider.get_transportadora_repository()
    provider.get_nfe_repository()

    payload = {
        "FreightOrder": "RESET_TEST_001",
        "ERP": "SAP",
        "Carrier": "16003754000135",
        "CNPJ_Origin": "03026527000183",
        "Incoterms": "CIF",
        "OperationType": "0",
        "Folder": [
            {
                "FolderNumber": "001",
                "ReferenceNumber": "REF001",
                "NetValue": 1500.0,
                "VehiclePlate": "ABC1D23",
                "TrailerPlate": [],
                "VehicleAxles": "2",
                "EquipmentType": "TRUCK",
                "Weight": 5000.0,
                "CFOP": "6352",
                "DriverID": "12345678909",
                "Cancel": False,
                "Tax": [
                    {
                        "TaxType": "ICMS",
                        "Base": 1500.0,
                        "Rate": 12.0,
                        "Value": 180.0,
                        "TaxCode": "00",
                        "ReducedBase": 0,
                    }
                ],
                "RelatedNFE": ["35251003026527000183550010013119001683587366"],
            }
        ],
    }
    gen_response = await client.post("/api/v1/cte", json=payload)
    assert gen_response.status_code == 201

    list_response = await client.get("/api/v1/cte")
    assert len(list_response.json()) > 0

    reset_response = await client.post("/api/v1/dev/reset-data")
    assert reset_response.status_code == 200

    list_after = await client.get("/api/v1/cte")
    assert len(list_after.json()) == 0


@pytest.mark.asyncio
async def test_reset_reseeds_all_entities(client):
    """After reset, seed data is restored for all entity types."""
    response = await client.post("/api/v1/dev/reset-data")
    assert response.status_code == 200

    rem = await client.get("/api/v1/remetentes")
    assert len(rem.json()) == 2

    dest = await client.get("/api/v1/destinatarios")
    assert len(dest.json()) == 2

    transp = await client.get("/api/v1/transportadoras")
    assert len(transp.json()) == 2
