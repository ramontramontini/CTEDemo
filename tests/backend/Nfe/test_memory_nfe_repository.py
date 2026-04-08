"""Tests for MemoryNfeRepository."""

from src.domain.nfe.repository import NfeRepository
from src.infrastructure.database.repositories.memory.nfe_repository import MemoryNfeRepository
from src.infrastructure.database.repositories.memory.state import MemoryState


class TestMemoryNfeRepository:
    def _make_repo(self) -> NfeRepository:
        state = MemoryState()
        state.clear()
        return MemoryNfeRepository(state)

    def test_seed_data_contains_min_3_records(self):
        repo = self._make_repo()
        all_nfes = repo.find_all()
        assert len(all_nfes) >= 3

    def test_find_by_key_returns_nfe(self):
        repo = self._make_repo()
        all_nfes = repo.find_all()
        first = all_nfes[0]
        found = repo.find_by_key(first.key)
        assert found is not None
        assert found.key == first.key

    def test_find_by_key_returns_none_for_unknown(self):
        repo = self._make_repo()
        assert repo.find_by_key("9" * 44) is None

    def test_seed_contains_authorized_nfe(self):
        repo = self._make_repo()
        authorized = [n for n in repo.find_all() if n.status == "authorized"]
        assert len(authorized) >= 1

    def test_seed_contains_canceled_nfe(self):
        repo = self._make_repo()
        canceled = [n for n in repo.find_all() if n.status == "canceled"]
        assert len(canceled) >= 1

    def test_seed_contains_divergent_emitter(self):
        repo = self._make_repo()
        all_nfes = repo.find_all()
        emitter_cnpjs = {n.emitter_cnpj for n in all_nfes}
        assert len(emitter_cnpjs) >= 2, "Seed must have at least 2 different emitter CNPJs"
