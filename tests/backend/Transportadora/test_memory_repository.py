"""Transportadora memory repository tests."""

from src.domain.transportadora.home import TransportadoraHome
from src.infrastructure.database.repositories.memory.transportadora_repository import MemoryTransportadoraRepository
from src.infrastructure.database.repositories.memory.state import MemoryState


VALID_CNPJ = "61198164000160"


def _create(**overrides):
    defaults = dict(
        cnpj=VALID_CNPJ,
        razao_social="Test Transportadora",
        uf="SP",
        cidade="Sao Paulo",
        logradouro="Rua A",
        numero="1",
        bairro="Centro",
        cep="01001000",
    )
    defaults.update(overrides)
    return TransportadoraHome.create(**defaults)


class TestMemoryTransportadoraRepository:
    def setup_method(self):
        self.state = MemoryState()
        self.state.clear()
        self.repo = MemoryTransportadoraRepository(self.state)

    def test_save_and_find_by_id(self):
        entity = _create()
        self.repo.save(entity)
        found = self.repo.find_by_id(entity.id)
        assert found is not None
        assert found.razao_social == "Test Transportadora"
        assert found.cnpj == VALID_CNPJ

    def test_find_by_cnpj(self):
        entity = _create()
        self.repo.save(entity)
        found = self.repo.find_by_cnpj(VALID_CNPJ)
        assert found is not None
        assert found.id == entity.id

    def test_find_by_cnpj_returns_none_for_missing(self):
        assert self.repo.find_by_cnpj("99999999999999") is None

    def test_find_all_returns_saved_entities(self):
        e1 = _create(cnpj="61198164000160")
        e2 = _create(cnpj="45997418000153", razao_social="Second")
        self.repo.save(e1)
        self.repo.save(e2)
        all_entities = self.repo.find_all()
        # 2 seed + 2 saved = 4
        assert len(all_entities) == 4

    def test_delete_removes_entity(self):
        entity = _create()
        self.repo.save(entity)
        assert self.repo.delete(entity.id) is True
        assert self.repo.find_by_id(entity.id) is None

    def test_find_by_id_returns_none_for_missing(self):
        from uuid import uuid4
        assert self.repo.find_by_id(uuid4()) is None
