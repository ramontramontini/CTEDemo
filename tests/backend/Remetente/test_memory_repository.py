"""Remetente memory repository tests."""

from uuid import uuid4

from src.domain.remetente.home import RemetenteHome
from src.infrastructure.database.repositories.memory.remetente_repository import MemoryRemetenteRepository
from src.infrastructure.database.repositories.memory.state import MemoryState


VALID_CNPJ = "11222333000181"
VALID_CNPJ_2 = "11444777000161"


def _create_remetente(**overrides):
    defaults = {
        "cnpj": VALID_CNPJ,
        "razao_social": "Empresa ABC Ltda",
        "nome_fantasia": "ABC",
        "ie": "123456789",
        "uf": "SP",
        "cidade": "São Paulo",
        "logradouro": "Rua das Flores",
        "numero": "100",
        "bairro": "Centro",
        "cep": "01001000",
    }
    defaults.update(overrides)
    return RemetenteHome.create(**defaults)


class TestMemoryRemetenteRepository:
    def setup_method(self):
        self.state = MemoryState()
        self.state.clear()
        self.repo = MemoryRemetenteRepository(self.state)

    def test_save_and_find_by_id(self):
        entity = _create_remetente()
        self.repo.save(entity)
        found = self.repo.find_by_id(entity.id)
        assert found is not None
        assert found.cnpj == VALID_CNPJ
        assert found.razao_social == "Empresa ABC Ltda"
        assert found.uf == "SP"

    def test_find_all_returns_saved_entities(self):
        e1 = _create_remetente(cnpj=VALID_CNPJ)
        e2 = _create_remetente(cnpj=VALID_CNPJ_2, razao_social="Second")
        self.repo.save(e1)
        self.repo.save(e2)
        all_entities = self.repo.find_all()
        assert len(all_entities) == 2

    def test_delete_removes_entity(self):
        entity = _create_remetente()
        self.repo.save(entity)
        assert self.repo.delete(entity.id) is True
        assert self.repo.find_by_id(entity.id) is None

    def test_find_by_id_returns_none_for_missing(self):
        assert self.repo.find_by_id(uuid4()) is None

    def test_find_by_cnpj_returns_entity(self):
        entity = _create_remetente()
        self.repo.save(entity)
        found = self.repo.find_by_cnpj(VALID_CNPJ)
        assert found is not None
        assert found.id == entity.id

    def test_find_by_cnpj_returns_none_for_missing(self):
        assert self.repo.find_by_cnpj("99999999999999") is None

    def test_save_updates_existing(self):
        entity = _create_remetente()
        self.repo.save(entity)
        entity.update_razao_social("Updated")
        self.repo.save(entity)
        found = self.repo.find_by_id(entity.id)
        assert found.razao_social == "Updated"
        assert len(self.repo.find_all()) == 1

    def test_seed_if_empty_loads_two_remetentes(self):
        assert len(self.repo.find_all()) == 0
        self.repo.seed_if_empty()
        all_entities = self.repo.find_all()
        assert len(all_entities) == 2
        cnpjs = {e.cnpj for e in all_entities}
        assert "03026527000183" in cnpjs
        assert "11444777000161" in cnpjs

    def test_seed_if_empty_does_not_duplicate(self):
        self.repo.seed_if_empty()
        self.repo.seed_if_empty()
        assert len(self.repo.find_all()) == 2
