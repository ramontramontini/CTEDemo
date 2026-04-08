"""Tests for CteHome — factory + CT-e generation."""

import pytest

from src.domain.cte.home import CteHome
from src.domain.cte.enums import CteStatus
from src.domain.transportadora.home import TransportadoraHome


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


def _make_transportadora():
    """Create a Transportadora entity matching the Carrier CNPJ in VALID_PAYLOAD."""
    return TransportadoraHome.create(
        cnpj="10758386000159",
        razao_social="Transportes Teste Ltda",
        uf="PE",
        cidade="Recife",
        logradouro="Rua Teste",
        numero="100",
        bairro="Centro",
        cep="50000000",
        ie="123456789",
    )


class TestCteHome:
    """CteHome generation tests."""

    def test_generate_produces_valid_cte(self):
        transportadora = _make_transportadora()
        cte = CteHome.generate(VALID_PAYLOAD, transportadora)
        assert cte.id is not None
        assert len(cte.access_key) == 44
        assert cte.status == CteStatus.GERADO
        assert cte.freight_order_number == "12345678901234"
        assert cte.original_payload == VALID_PAYLOAD

    def test_generate_produces_xml(self):
        transportadora = _make_transportadora()
        cte = CteHome.generate(VALID_PAYLOAD, transportadora)
        assert cte.xml is not None
        assert "<?xml" in cte.xml
        assert "CTe" in cte.xml

    def test_generate_access_key_has_carrier_cnpj(self):
        transportadora = _make_transportadora()
        cte = CteHome.generate(VALID_PAYLOAD, transportadora)
        assert "10758386000159" in cte.access_key

    def test_generate_sequential_numbering(self):
        transportadora = _make_transportadora()
        cte1 = CteHome.generate(VALID_PAYLOAD, transportadora)
        cte2 = CteHome.generate(VALID_PAYLOAD, transportadora)
        assert cte1.access_key != cte2.access_key

    def test_generate_with_invalid_payload_raises(self):
        transportadora = _make_transportadora()
        payload = {**VALID_PAYLOAD, "Carrier": "11111111111111"}
        with pytest.raises(ValueError, match="Carrier"):
            CteHome.generate(payload, transportadora)
