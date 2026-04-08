"""Tests for CteHome — factory + CT-e generation."""

import xml.etree.ElementTree as ET
from unittest.mock import patch

import pytest

from src.domain.cte.enums import CteStatus
from src.domain.cte.errors import CteXmlBuildError, DuplicateFreightOrderError
from src.domain.cte.home import CteHome
from src.domain.transportadora.home import TransportadoraHome
from src.infrastructure.database.repositories.memory.cte_repository import MemoryCteRepository
from src.infrastructure.database.repositories.memory.state import MemoryState


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


@pytest.fixture()
def repo():
    """Fresh empty memory repository for each test."""
    state = MemoryState()
    state.clear()
    return MemoryCteRepository(state)


class TestCteHome:
    """CteHome generation tests."""

    def test_generate_produces_valid_cte(self, repo):
        transportadora = _make_transportadora()
        cte = CteHome.generate(VALID_PAYLOAD, transportadora, repo)
        assert cte.id is not None
        assert len(cte.access_key) == 44
        assert cte.status == CteStatus.GERADO
        assert cte.freight_order_number == "12345678901234"
        assert cte.original_payload == VALID_PAYLOAD

    def test_generate_produces_xml(self, repo):
        transportadora = _make_transportadora()
        cte = CteHome.generate(VALID_PAYLOAD, transportadora, repo)
        assert cte.xml is not None
        assert "<?xml" in cte.xml
        assert "CTe" in cte.xml

    def test_generate_access_key_has_carrier_cnpj(self, repo):
        transportadora = _make_transportadora()
        cte = CteHome.generate(VALID_PAYLOAD, transportadora, repo)
        assert "10758386000159" in cte.access_key

    def test_generate_sequential_numbering(self, repo):
        transportadora = _make_transportadora()
        cte1 = CteHome.generate(VALID_PAYLOAD, transportadora, repo)
        repo.save(cte1)
        payload2 = {**VALID_PAYLOAD, "FreightOrder": "99999999999999"}
        cte2 = CteHome.generate(payload2, transportadora, repo)
        assert cte1.access_key != cte2.access_key

    def test_generate_with_invalid_payload_raises(self, repo):
        transportadora = _make_transportadora()
        payload = {**VALID_PAYLOAD, "Carrier": "11111111111111"}
        with pytest.raises(ValueError, match="Carrier"):
            CteHome.generate(payload, transportadora, repo)

    def test_generate_raises_on_duplicate_freight_order(self, repo):
        """Domain enforcement — duplicate check in Home."""
        transportadora = _make_transportadora()
        cte = CteHome.generate(VALID_PAYLOAD, transportadora, repo)
        repo.save(cte)
        with pytest.raises(DuplicateFreightOrderError, match="12345678901234"):
            CteHome.generate(VALID_PAYLOAD, transportadora, repo)

    def test_generate_produces_well_formed_xml(self, repo):
        """XML output is parseable by ET.fromstring."""
        transportadora = _make_transportadora()
        cte = CteHome.generate(VALID_PAYLOAD, transportadora, repo)
        ET.fromstring(cte.xml.encode("utf-8"))

    def test_generate_raises_xml_build_error_on_malformed_xml(self, repo):
        """Monkeypatched xml_builder returning invalid XML -> CteXmlBuildError."""
        transportadora = _make_transportadora()
        with patch("src.domain.cte.home.build_cte_xml", return_value="<broken"):
            with pytest.raises(CteXmlBuildError):
                CteHome.generate(VALID_PAYLOAD, transportadora, repo)
