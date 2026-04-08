"""Tests for seed data — Destinatario startup + CNPJ uniqueness."""

from src.infrastructure.database.repositories.memory.state import MemoryState
from src.infrastructure.database.repositories.memory.destinatario_repository import (
    MemoryDestinatarioRepository,
)
from src.infrastructure.database.repositories.memory.transportadora_repository import (
    MemoryTransportadoraRepository,
)
from src.infrastructure.database.repositories.memory.remetente_repository import (
    MemoryRemetenteRepository,
)


class TestSeedData:
    """Seed data integrity tests."""

    def test_destinatario_seed_populated(self):
        """Destinatario seed_if_empty creates entries."""
        state = MemoryState()
        state.clear()
        repo = MemoryDestinatarioRepository(state)
        repo.seed_if_empty()
        entities = repo.find_all()
        assert len(entities) >= 1

    def test_seed_cnpjs_unique_across_aggregates(self):
        """No CNPJ collision between Transportadora, Remetente, Destinatario seeds."""
        state = MemoryState()
        state.clear()
        t_repo = MemoryTransportadoraRepository(state)
        r_repo = MemoryRemetenteRepository(state)
        d_repo = MemoryDestinatarioRepository(state)
        d_repo.seed_if_empty()

        t_cnpjs = {e.cnpj for e in t_repo.find_all() if hasattr(e, "cnpj") and e.cnpj}
        r_cnpjs = {e.cnpj for e in r_repo.find_all() if hasattr(e, "cnpj") and e.cnpj}
        d_cnpjs = {e.cnpj for e in d_repo.find_all() if hasattr(e, "cnpj") and e.cnpj}

        # No shared CNPJs across the three aggregates
        assert not (t_cnpjs & r_cnpjs), f"Transportadora/Remetente CNPJ collision: {t_cnpjs & r_cnpjs}"
        assert not (t_cnpjs & d_cnpjs), f"Transportadora/Destinatario CNPJ collision: {t_cnpjs & d_cnpjs}"
        assert not (r_cnpjs & d_cnpjs), f"Remetente/Destinatario CNPJ collision: {r_cnpjs & d_cnpjs}"
