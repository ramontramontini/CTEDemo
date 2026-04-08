"""Tests for CteGenerationService — cross-aggregate orchestration."""

import pytest

from src.domain.cte.enums import CteStatus
from src.domain.services.cte_generation_service import CteGenerationService
from src.infrastructure.database.repositories.memory.state import MemoryState
from src.infrastructure.database.repositories.memory.transportadora_repository import (
    MemoryTransportadoraRepository,
)


VALID_PAYLOAD = {
    "FreightOrder": "12345678901234",
    "ERP": "SAP",
    "Carrier": "11222333000181",
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

    def _make_repo_with_carrier(self) -> MemoryTransportadoraRepository:
        state = MemoryState()
        state.clear()
        repo = MemoryTransportadoraRepository(state)
        return repo

    def test_generate_with_registered_carrier(self):
        """Service looks up Transportadora by CNPJ and generates CT-e."""
        repo = self._make_repo_with_carrier()
        # Seed repo has CNPJ 11222333000181
        service = CteGenerationService(repo)
        cte = service.generate(VALID_PAYLOAD)
        assert cte.status == CteStatus.GERADO
        assert cte.freight_order_number == "12345678901234"

    def test_generate_with_unknown_carrier_raises(self):
        """Service raises ValueError when carrier CNPJ is not registered."""
        repo = self._make_repo_with_carrier()
        payload = {**VALID_PAYLOAD, "Carrier": "33444555000199"}
        service = CteGenerationService(repo)
        with pytest.raises(ValueError, match="Transportadora not found"):
            service.generate(payload)

    def test_service_passes_transportadora_entity_to_home(self):
        """CteHome.generate() receives Transportadora entity, not repo."""
        repo = self._make_repo_with_carrier()
        service = CteGenerationService(repo)
        cte = service.generate(VALID_PAYLOAD)
        # Verify XML contains Transportadora data (xNome from entity)
        assert "Transportadora ABC Ltda" in cte.xml

    def test_service_orchestrates_lookup_then_generate(self):
        """Service coordinates: lookup Transportadora -> generate CT-e."""
        repo = self._make_repo_with_carrier()
        service = CteGenerationService(repo)
        # First call succeeds (carrier exists)
        cte = service.generate(VALID_PAYLOAD)
        assert cte is not None
        # Delete the carrier, next call fails
        transportadora = repo.find_by_cnpj("11222333000181")
        repo.delete(transportadora.id)
        with pytest.raises(ValueError, match="Transportadora not found"):
            service.generate(VALID_PAYLOAD)
