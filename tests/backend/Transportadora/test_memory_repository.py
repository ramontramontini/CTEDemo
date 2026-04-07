"""Transportadora memory repository tests."""

from src.domain.transportadora.home import TransportadoraHome
from src.infrastructure.database.repositories.memory.transportadora_repository import MemoryTransportadoraRepository
from src.infrastructure.database.repositories.memory.state import MemoryState


class TestMemoryTransportadoraRepository:
    def setup_method(self):
        self.state = MemoryState()
        self.state.clear()
        self.repo = MemoryTransportadoraRepository(self.state)

    def test_save_and_find_by_id(self):
        entity = TransportadoraHome.create(name="Test")
        self.repo.save(entity)
        found = self.repo.find_by_id(entity.id)
        assert found is not None
        assert found.name == "Test"

    def test_find_all_returns_saved_entities(self):
        e1 = TransportadoraHome.create(name="First")
        e2 = TransportadoraHome.create(name="Second")
        self.repo.save(e1)
        self.repo.save(e2)
        all_entities = self.repo.find_all()
        assert len(all_entities) == 2

    def test_delete_removes_entity(self):
        entity = TransportadoraHome.create(name="ToDelete")
        self.repo.save(entity)
        assert self.repo.delete(entity.id) is True
        assert self.repo.find_by_id(entity.id) is None

    def test_find_by_id_returns_none_for_missing(self):
        from uuid import uuid4
        assert self.repo.find_by_id(uuid4()) is None
