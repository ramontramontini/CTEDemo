"""Tests for NfeValidationService."""

import pytest

from src.domain.nfe.entity import Nfe
from src.domain.nfe.repository import NfeRepository
from src.domain.services.nfe_validation_service import NfeValidationService
from src.infrastructure.database.repositories.memory.nfe_repository import MemoryNfeRepository
from src.infrastructure.database.repositories.memory.state import MemoryState


CNPJ_ORIGIN = "10758386000159"


class _TestRepo:
    """Minimal in-memory repo for controlled test scenarios."""

    def __init__(self, nfes: list[Nfe]):
        self._nfes = {n.key: n for n in nfes}

    def find_by_key(self, key: str) -> Nfe | None:
        return self._nfes.get(key)

    def find_all(self) -> list[Nfe]:
        return list(self._nfes.values())


class TestNfeValidationService:
    def test_validate_authorized_nfe_passes(self):
        nfe = Nfe(key="A" * 44, status="authorized", emitter_cnpj=CNPJ_ORIGIN)
        repo = _TestRepo([nfe])
        service = NfeValidationService(repo)
        warnings = service.validate_keys(["A" * 44], CNPJ_ORIGIN)
        assert warnings == []

    def test_validate_unknown_nfe_raises(self):
        repo = _TestRepo([])
        service = NfeValidationService(repo)
        with pytest.raises(ValueError, match="NF-e not found"):
            service.validate_keys(["X" * 44], CNPJ_ORIGIN)

    def test_validate_canceled_nfe_raises(self):
        nfe = Nfe(key="C" * 44, status="canceled", emitter_cnpj=CNPJ_ORIGIN)
        repo = _TestRepo([nfe])
        service = NfeValidationService(repo)
        with pytest.raises(ValueError, match="NF-e canceled"):
            service.validate_keys(["C" * 44], CNPJ_ORIGIN)

    def test_validate_multiple_keys_first_invalid_raises(self):
        nfe_ok = Nfe(key="A" * 44, status="authorized", emitter_cnpj=CNPJ_ORIGIN)
        repo = _TestRepo([nfe_ok])
        service = NfeValidationService(repo)
        with pytest.raises(ValueError, match="NF-e not found"):
            service.validate_keys(["A" * 44, "B" * 44], CNPJ_ORIGIN)

    def test_validate_divergent_emitter_returns_warning(self):
        nfe = Nfe(key="D" * 44, status="authorized", emitter_cnpj="99888777000166")
        repo = _TestRepo([nfe])
        service = NfeValidationService(repo)
        warnings = service.validate_keys(["D" * 44], CNPJ_ORIGIN)
        assert len(warnings) == 1
        assert "differs from CNPJ_Origin" in warnings[0]

    def test_validate_multiple_divergences_returns_all_warnings(self):
        nfe1 = Nfe(key="D" * 44, status="authorized", emitter_cnpj="99888777000166")
        nfe2 = Nfe(key="E" * 44, status="authorized", emitter_cnpj="88777666000155")
        repo = _TestRepo([nfe1, nfe2])
        service = NfeValidationService(repo)
        warnings = service.validate_keys(["D" * 44, "E" * 44], CNPJ_ORIGIN)
        assert len(warnings) == 2
