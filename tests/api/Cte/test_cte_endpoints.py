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
            "RelatedNFE": ["35230410758386000159550010000000011000000015"],
        }
    ],
}

CARRIER_TRANSPORTADORA = {
    "cnpj": "10758386000159",
    "razao_social": "Carrier Teste Ltda",
    "nome_fantasia": "CarrierTest",
    "ie": "123456789",
    "uf": "PE",
    "cidade": "Recife",
    "logradouro": "Rua do Teste",
    "numero": "100",
    "bairro": "Centro",
    "cep": "50000000",
}


async def _register_carrier(client: AsyncClient) -> None:
    """Register the Transportadora matching VALID_PAYLOAD Carrier CNPJ."""
    await client.post("/api/v1/transportadoras", json=CARRIER_TRANSPORTADORA)


@pytest.mark.asyncio
class TestGenerateCte:
    async def test_generate_valid_returns_201(self, client: AsyncClient):
        await _register_carrier(client)
        response = await client.post("/api/v1/cte", json=VALID_PAYLOAD)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert len(data["access_key"]) == 44
        assert " " in data["formatted_access_key"]
        assert data["status"] == "gerado"
        assert data["freight_order_number"] == "12345678901234"
        assert "<?xml" in data["xml"]
        assert "created_at" in data

    async def test_generate_unknown_carrier_returns_400(self, client: AsyncClient):
        """Carrier CNPJ valid format but not registered -> 400."""
        payload = {**VALID_PAYLOAD, "Carrier": "33444555000199"}
        response = await client.post("/api/v1/cte", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert "Transportadora not found" in data["detail"]

    async def test_generate_invalid_cnpj_returns_400(self, client: AsyncClient):
        """Invalid CNPJ format -> 400 (carrier lookup fails before payload validation)."""
        payload = {**VALID_PAYLOAD, "Carrier": "11111111111111"}
        response = await client.post("/api/v1/cte", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert "Transportadora not found" in data["detail"]

    async def test_generate_missing_fields_returns_422(self, client: AsyncClient):
        await _register_carrier(client)
        payload = {**VALID_PAYLOAD, "FreightOrder": "", "Folder": []}
        response = await client.post("/api/v1/cte", json=payload)
        assert response.status_code == 422

    async def test_generate_invalid_cpf_returns_422(self, client: AsyncClient):
        await _register_carrier(client)
        payload = {**VALID_PAYLOAD}
        payload["Folder"] = [{**VALID_PAYLOAD["Folder"][0], "DriverID": "11111111111"}]
        response = await client.post("/api/v1/cte", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert any("DriverID" in e["field"] for e in data["detail"])

    async def test_generate_invalid_plate_returns_422(self, client: AsyncClient):
        await _register_carrier(client)
        payload = {**VALID_PAYLOAD}
        payload["Folder"] = [{**VALID_PAYLOAD["Folder"][0], "VehiclePlate": "INVALID"}]
        response = await client.post("/api/v1/cte", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert any("VehiclePlate" in e["field"] for e in data["detail"])


@pytest.mark.asyncio
class TestListAndGetCte:
    async def test_list_ctes_returns_empty(self, client: AsyncClient):
        response = await client.get("/api/v1/cte")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_ctes_returns_generated(self, client: AsyncClient):
        await _register_carrier(client)
        await client.post("/api/v1/cte", json=VALID_PAYLOAD)
        response = await client.get("/api/v1/cte")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert "access_key" in data[0]
        assert "status" in data[0]
        assert "freight_order_number" in data[0]

    async def test_get_cte_returns_detail(self, client: AsyncClient):
        await _register_carrier(client)
        create_resp = await client.post("/api/v1/cte", json=VALID_PAYLOAD)
        entity_id = create_resp.json()["id"]
        response = await client.get(f"/api/v1/cte/{entity_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["access_key"] is not None
        assert "xml" in data

    async def test_get_cte_not_found_returns_404(self, client: AsyncClient):
        response = await client.get(f"/api/v1/cte/{uuid.uuid4()}")
        assert response.status_code == 404

    async def test_get_cte_by_freight_order_number(self, client: AsyncClient):
        await _register_carrier(client)
        create_resp = await client.post("/api/v1/cte", json=VALID_PAYLOAD)
        assert create_resp.status_code == 201
        created = create_resp.json()
        response = await client.get("/api/v1/cte/12345678901234")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created["id"]
        assert data["freight_order_number"] == "12345678901234"
        assert data["access_key"] is not None
        assert "xml" in data

    async def test_get_cte_by_freight_order_not_found(self, client: AsyncClient):
        response = await client.get("/api/v1/cte/9999999999")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestDuplicateFreightOrder:
    async def test_duplicate_freight_order_returns_400(self, client: AsyncClient):
        response1 = await client.post("/api/v1/cte", json=VALID_PAYLOAD)
        assert response1.status_code == 201
        response2 = await client.post("/api/v1/cte", json=VALID_PAYLOAD)
        assert response2.status_code == 400
        data = response2.json()
        assert data["detail"] == "Freight order '12345678901234' already exists"

    async def test_duplicate_does_not_block_different_freight_order(self, client: AsyncClient):
        response1 = await client.post("/api/v1/cte", json=VALID_PAYLOAD)
        assert response1.status_code == 201
        response2 = await client.post("/api/v1/cte", json=VALID_PAYLOAD)
        assert response2.status_code == 400
        different_payload = {**VALID_PAYLOAD, "FreightOrder": "99999999999999"}
        response3 = await client.post("/api/v1/cte", json=different_payload)
        assert response3.status_code == 201


@pytest.mark.asyncio
class TestExtraPostmanFields:
    async def test_extra_postman_fields_stored_in_payload(self, client: AsyncClient):
        await _register_carrier(client)
        payload = {
            **VALID_PAYLOAD,
            "BusinessTransactionDocument": "DOC123",
            "BusinessTransactionDocType": "TYPE_A",
            "Issuer": "ISSUER_CO",
            "DocumentType": "CT-e",
            "FleetType": "OWN",
            "TransportType": "ROAD",
        }
        create_resp = await client.post("/api/v1/cte", json=payload)
        assert create_resp.status_code == 201
        entity_id = create_resp.json()["id"]
        detail_resp = await client.get(f"/api/v1/cte/{entity_id}")
        assert detail_resp.status_code == 200
        data = detail_resp.json()
        assert "original_payload" in data
        op = data["original_payload"]
        assert op["BusinessTransactionDocument"] == "DOC123"
        assert op["BusinessTransactionDocType"] == "TYPE_A"
        assert op["Issuer"] == "ISSUER_CO"
        assert op["DocumentType"] == "CT-e"
        assert op["FleetType"] == "OWN"
        assert op["TransportType"] == "ROAD"


CARRIER_CNPJ = "10758386000159"

TRANSPORTADORA_PE = {
    "cnpj": CARRIER_CNPJ,
    "razao_social": "Transportes PE Ltda",
    "nome_fantasia": "TransPE",
    "ie": "123456789",
    "uf": "PE",
    "cidade": "Recife",
    "logradouro": "Rua da Aurora",
    "numero": "100",
    "bairro": "Boa Vista",
    "cep": "50060010",
}

DESTINATARIO_PE = {
    "cnpj": "44555666000181",
    "razao_social": "Dest PE Ltda",
    "nome_fantasia": "DestPE",
    "ie": "987654321",
    "uf": "PE",
    "cidade": "Recife",
    "logradouro": "Av Boa Viagem",
    "numero": "200",
    "bairro": "Boa Viagem",
    "cep": "51030300",
}

DESTINATARIO_SP = {
    "cnpj": "55666777000181",
    "razao_social": "Dest SP Ltda",
    "nome_fantasia": "DestSP",
    "ie": "111222333",
    "uf": "SP",
    "cidade": "Sao Paulo",
    "logradouro": "Av Paulista",
    "numero": "500",
    "bairro": "Bela Vista",
    "cep": "01310100",
}


@pytest.mark.asyncio
class TestCfopGeographicValidation:
    """CFOP geographic validation — AC1-AC4."""

    async def test_cfop_geographic_same_state_6xxx_returns_422(self, client: AsyncClient):
        """Same-state origin/dest with interstate CFOP 6352 -> 422."""
        await client.post("/api/v1/transportadoras", json=TRANSPORTADORA_PE)
        await client.post("/api/v1/destinatarios", json=DESTINATARIO_PE)
        payload = {
            **VALID_PAYLOAD,
            "CNPJ_Dest": DESTINATARIO_PE["cnpj"],
            "Folder": [{**VALID_PAYLOAD["Folder"][0], "CFOP": "6352"}],
        }
        response = await client.post("/api/v1/cte", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert any("requer estados diferentes" in e["message"] for e in data["detail"])

    async def test_cfop_geographic_cross_state_5xxx_returns_422(self, client: AsyncClient):
        """Cross-state origin/dest with intrastate CFOP 5352 -> 422."""
        await client.post("/api/v1/transportadoras", json=TRANSPORTADORA_PE)
        await client.post("/api/v1/destinatarios", json=DESTINATARIO_SP)
        payload = {
            **VALID_PAYLOAD,
            "CNPJ_Dest": DESTINATARIO_SP["cnpj"],
            "Folder": [{**VALID_PAYLOAD["Folder"][0], "CFOP": "5352"}],
        }
        response = await client.post("/api/v1/cte", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert any("requer mesmo estado" in e["message"] for e in data["detail"])

    async def test_cfop_geographic_valid_passes(self, client: AsyncClient):
        """Cross-state with interstate CFOP 6352 -> 201."""
        await client.post("/api/v1/transportadoras", json=TRANSPORTADORA_PE)
        await client.post("/api/v1/destinatarios", json=DESTINATARIO_SP)
        payload = {
            **VALID_PAYLOAD,
            "CNPJ_Dest": DESTINATARIO_SP["cnpj"],
            "Folder": [{**VALID_PAYLOAD["Folder"][0], "CFOP": "6352"}],
        }
        response = await client.post("/api/v1/cte", json=payload)
        assert response.status_code == 201

    async def test_cfop_geographic_skipped_when_no_cnpj_dest(self, client: AsyncClient):
        """No CNPJ_Dest in payload -> geographic validation skipped, 201."""
        await _register_carrier(client)
        response = await client.post("/api/v1/cte", json=VALID_PAYLOAD)
        assert response.status_code == 201

    async def test_cfop_geographic_carrier_not_found_returns_400(self, client: AsyncClient):
        """Carrier not registered as Transportadora -> 400 (carrier validation)."""
        payload = {
            **VALID_PAYLOAD,
            "CNPJ_Dest": DESTINATARIO_PE["cnpj"],
        }
        response = await client.post("/api/v1/cte", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert "Transportadora not found" in data["detail"]


# Seed NF-e keys from MemoryNfeRepository
AUTHORIZED_NFE_KEY = "35230410758386000159550010000000011000000015"
CANCELED_NFE_KEY = "35230410758386000159550010000000021000000022"
DIVERGENT_NFE_KEY = "31230499888777000166550010000000031000000039"


@pytest.mark.asyncio
class TestNfeValidation:
    """NF-e validation — AC2, AC3, AC4."""

    async def test_generate_with_valid_nfe_succeeds(self, client: AsyncClient):
        """Authorized NF-e key -> 201."""
        await _register_carrier(client)
        payload = {
            **VALID_PAYLOAD,
            "Folder": [{**VALID_PAYLOAD["Folder"][0], "RelatedNFE": [AUTHORIZED_NFE_KEY]}],
        }
        response = await client.post("/api/v1/cte", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["warnings"] == []

    async def test_generate_with_unknown_nfe_returns_400(self, client: AsyncClient):
        """Unknown NF-e key -> 400."""
        await _register_carrier(client)
        unknown_key = "9" * 44
        payload = {
            **VALID_PAYLOAD,
            "Folder": [{**VALID_PAYLOAD["Folder"][0], "RelatedNFE": [unknown_key]}],
        }
        response = await client.post("/api/v1/cte", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert "NF-e not found" in data["detail"]
        assert unknown_key in data["detail"]

    async def test_generate_with_canceled_nfe_returns_400(self, client: AsyncClient):
        """Canceled NF-e key -> 400."""
        await _register_carrier(client)
        payload = {
            **VALID_PAYLOAD,
            "Folder": [{**VALID_PAYLOAD["Folder"][0], "RelatedNFE": [CANCELED_NFE_KEY]}],
        }
        response = await client.post("/api/v1/cte", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert "NF-e canceled" in data["detail"]

    async def test_generate_with_divergent_emitter_returns_warning(self, client: AsyncClient):
        """NF-e emitter != CNPJ_Origin -> 201 with warning."""
        await _register_carrier(client)
        payload = {
            **VALID_PAYLOAD,
            "Folder": [{**VALID_PAYLOAD["Folder"][0], "RelatedNFE": [DIVERGENT_NFE_KEY]}],
        }
        response = await client.post("/api/v1/cte", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert len(data["warnings"]) == 1
        assert "differs from CNPJ_Origin" in data["warnings"][0]
