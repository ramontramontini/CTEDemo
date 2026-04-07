"""Remetente memory repository tests."""

from src.domain.remetente.home import RemetenteHome
from src.infrastructure.database.repositories.memory.remetente_repository import MemoryRemetenteRepository
from src.infrastructure.database.repositories.memory.state import MemoryState


class TestMemoryRemetenteRepository:
    def setup_method(self):
        self.state = MemoryState()
        self.state.clear()
        self.repo = MemoryRemetenteRepository(self.state)

    def test_save_and_find_by_id(self):
        entity = RemetenteHome.create(name="Test")
        self.repo.save(entity)
        found = self.repo.find_by_id(entity.id)
        assert found is not None
        assert found.name == "Test"

    def test_find_all_returns_saved_entities(self):
        e1 = RemetenteHome.create(name="First")
        e2 = RemetenteHome.create(name="Second")
        self.repo.save(e1)
        self.repo.save(e2)
        all_entities = self.repo.find_all()
        assert len(all_entities) == 2

    def test_delete_removes_entity(self):
        entity = RemetenteHome.create(name="ToDelete")
        self.repo.save(entity)
        assert self.repo.delete(entity.id) is True
        assert self.repo.find_by_id(entity.id) is None

    def test_find_by_id_returns_none_for_missing(self):
        from uuid import uuid4
        assert self.repo.find_by_id(uuid4()) is None
