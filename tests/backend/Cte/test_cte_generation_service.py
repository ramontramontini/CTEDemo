"""Tests for CteGenerationService — cross-aggregate orchestration."""

import pytest

from src.domain.cte.enums import CteStatus
from src.domain.services.cte_generation_service import CteGenerationService
from src.infrastructure.database.repositories.memory.cte_repository import MemoryCteRepository
from src.infrastructure.database.repositories.memory.state import MemoryState
from src.infrastructure.database.repositories.memory.transportadora_repository import (
    MemoryTransportadoraRepository,
)


VALID_PAYLOAD = {
    "FreightOrder": "12345678901234",
    "ERP": "SAP",
    "Carrier": "16003754000135",
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


class TestCteGenerationService:
    """CteGenerationService orchestration tests."""

    def _make_repos(self):
        state = MemoryState()
        state.clear()
        transportadora_repo = MemoryTransportadoraRepository(state)
        cte_repo = MemoryCteRepository(state)
        return transportadora_repo, cte_repo

    def test_generate_with_registered_carrier(self):
        """Service looks up Transportadora by CNPJ and generates CT-e."""
        transportadora_repo, cte_repo = self._make_repos()
        # Seed repo has CNPJ 16003754000135
        service = CteGenerationService(transportadora_repo)
        cte = service.generate(VALID_PAYLOAD, cte_repo)
        assert cte.status == CteStatus.GERADO
        assert cte.freight_order_number == "12345678901234"

    def test_generate_with_unknown_carrier_raises(self):
        """Service raises ValueError when carrier CNPJ is not registered."""
        transportadora_repo, cte_repo = self._make_repos()
        payload = {**VALID_PAYLOAD, "Carrier": "33444555000199"}
        service = CteGenerationService(transportadora_repo)
        with pytest.raises(ValueError, match="Transportadora not found"):
            service.generate(payload, cte_repo)

    def test_service_passes_transportadora_entity_to_home(self):
        """CteHome.generate() receives Transportadora entity, not repo."""
        transportadora_repo, cte_repo = self._make_repos()
        service = CteGenerationService(transportadora_repo)
        cte = service.generate(VALID_PAYLOAD, cte_repo)
        # Verify XML contains Transportadora data (xNome from entity)
        assert "Transportadora Postman Ltda" in cte.xml

    def test_service_orchestrates_lookup_then_generate(self):
        """Service coordinates: lookup Transportadora -> generate CT-e."""
        transportadora_repo, cte_repo = self._make_repos()
        service = CteGenerationService(transportadora_repo)
        # First call succeeds (carrier exists)
        cte = service.generate(VALID_PAYLOAD, cte_repo)
        assert cte is not None
        # Delete the carrier, next call fails
        transportadora = transportadora_repo.find_by_cnpj("16003754000135")
        transportadora_repo.delete(transportadora.id)
        with pytest.raises(ValueError, match="Transportadora not found"):
            service.generate(VALID_PAYLOAD, cte_repo)
