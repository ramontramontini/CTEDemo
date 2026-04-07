"""Cte memory repository tests."""

from src.domain.cte.home import CteHome
from src.infrastructure.database.repositories.memory.cte_repository import MemoryCteRepository
from src.infrastructure.database.repositories.memory.state import MemoryState


class TestMemoryCteRepository:
    def setup_method(self):
        self.state = MemoryState()
        self.state.clear()
        self.repo = MemoryCteRepository(self.state)

    def test_save_and_find_by_id(self):
        entity = CteHome.create(name="Test")
        self.repo.save(entity)
        found = self.repo.find_by_id(entity.id)
        assert found is not None
        assert found.name == "Test"

    def test_find_all_returns_saved_entities(self):
        e1 = CteHome.create(name="First")
        e2 = CteHome.create(name="Second")
        self.repo.save(e1)
        self.repo.save(e2)
        all_entities = self.repo.find_all()
        assert len(all_entities) == 2

    def test_delete_removes_entity(self):
        entity = CteHome.create(name="ToDelete")
        self.repo.save(entity)
        assert self.repo.delete(entity.id) is True
        assert self.repo.find_by_id(entity.id) is None

    def test_find_by_id_returns_none_for_missing(self):
        from uuid import uuid4
        assert self.repo.find_by_id(uuid4()) is None
