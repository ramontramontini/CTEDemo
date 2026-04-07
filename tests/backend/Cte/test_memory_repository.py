"""Cte memory repository tests."""

from src.domain.cte.entity import Cte
from src.domain.cte.enums import CteStatus
from src.infrastructure.database.repositories.memory.cte_repository import MemoryCteRepository
from src.infrastructure.database.repositories.memory.state import MemoryState


def _make_cte(**overrides) -> Cte:
    defaults = {
        "access_key": "26251010758386000159570200000000011000000060",
        "freight_order_number": "12345678901234",
        "status": CteStatus.GERADO,
        "xml": "<xml/>",
        "original_payload": {"FreightOrder": "12345678901234"},
    }
    defaults.update(overrides)
    return Cte._create_raw(**defaults)


class TestMemoryCteRepository:
    def setup_method(self):
        self.state = MemoryState()
        self.state.clear()
        self.repo = MemoryCteRepository(self.state)

    def test_save_and_find_by_id(self):
        entity = _make_cte()
        self.repo.save(entity)
        found = self.repo.find_by_id(entity.id)
        assert found is not None
        assert found.access_key == entity.access_key

    def test_find_all_returns_saved_entities(self):
        e1 = _make_cte(freight_order_number="11111111111111")
        e2 = _make_cte(freight_order_number="22222222222222")
        self.repo.save(e1)
        self.repo.save(e2)
        all_entities = self.repo.find_all()
        assert len(all_entities) == 2

    def test_delete_removes_entity(self):
        entity = _make_cte()
        self.repo.save(entity)
        assert self.repo.delete(entity.id) is True
        assert self.repo.find_by_id(entity.id) is None

    def test_find_by_id_returns_none_for_missing(self):
        from uuid import uuid4
        assert self.repo.find_by_id(uuid4()) is None
