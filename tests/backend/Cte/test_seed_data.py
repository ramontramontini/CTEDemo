"""Tests for seed data alignment with Postman payload."""

from src.infrastructure.database.repositories.memory.state import MemoryState
from src.infrastructure.database.repositories.memory.transportadora_repository import (
    MemoryTransportadoraRepository,
)
from src.infrastructure.database.repositories.memory.remetente_repository import (
    MemoryRemetenteRepository,
)
from src.infrastructure.database.repositories.memory.nfe_repository import (
    MemoryNfeRepository,
)


POSTMAN_CARRIER_CNPJ = "16003754000135"
POSTMAN_ORIGIN_CNPJ = "03026527000183"
POSTMAN_NFE_KEYS = [
    "35251003026527000183550010013119001683587366",
    "35251003026527000183550010013119001683587367",
    "35251003026527000183550010013119001683587368",
    "35251003026527000183550010013119001683587369",
]


class TestTransportadoraSeed:
    """Transportadora seed includes Postman carrier CNPJ."""

    def test_seed_has_postman_cnpj(self):
        state = MemoryState()
        repo = MemoryTransportadoraRepository(state)
        entity = repo.find_by_cnpj(POSTMAN_CARRIER_CNPJ)
        assert entity is not None
        cnpj = entity.cnpj
        assert (cnpj.value if hasattr(cnpj, "value") else str(cnpj)) == POSTMAN_CARRIER_CNPJ


class TestRemetenteSeed:
    """Remetente seed includes Postman origin CNPJ."""

    def test_seed_has_postman_cnpj(self):
        state = MemoryState()
        repo = MemoryRemetenteRepository(state)
        repo.seed_if_empty()
        entity = repo.find_by_cnpj(POSTMAN_ORIGIN_CNPJ)
        assert entity is not None
        cnpj = entity.cnpj
        assert (cnpj.value if hasattr(cnpj, "value") else str(cnpj)) == POSTMAN_ORIGIN_CNPJ


class TestNfeSeed:
    """NF-e seed includes Postman keys."""

    def test_seed_has_postman_keys(self):
        state = MemoryState()
        repo = MemoryNfeRepository(state)
        for key in POSTMAN_NFE_KEYS:
            nfe = repo.find_by_key(key)
            assert nfe is not None, f"NF-e key {key} not seeded"

    def test_postman_nfe_keys_are_authorized(self):
        state = MemoryState()
        repo = MemoryNfeRepository(state)
        for key in POSTMAN_NFE_KEYS:
            nfe = repo.find_by_key(key)
            assert nfe is not None, f"NF-e key {key} not seeded"
            assert nfe.status == "authorized", f"NF-e {key} status is {nfe.status}"

    def test_postman_nfe_emitter_cnpj(self):
        state = MemoryState()
        repo = MemoryNfeRepository(state)
        for key in POSTMAN_NFE_KEYS:
            nfe = repo.find_by_key(key)
            assert nfe is not None
            assert nfe.emitter_cnpj == POSTMAN_ORIGIN_CNPJ

    def test_seed_idempotency(self):
        state = MemoryState()
        repo = MemoryNfeRepository(state)
        count_before = len(repo.find_all())
        # Trigger seed again via new repo on same state
        MemoryNfeRepository(state)
        count_after = len(repo.find_all())
        assert count_after == count_before
