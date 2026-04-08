"""Destinatario memory repository tests."""

from uuid import uuid4

from src.domain.destinatario.home import DestinatarioHome
from src.infrastructure.database.repositories.memory.destinatario_repository import MemoryDestinatarioRepository
from src.infrastructure.database.repositories.memory.state import MemoryState


VALID_CNPJ = "11222333000181"
VALID_CNPJ_2 = "11444777000161"
VALID_CPF = "12345678909"


def _create_pj(**overrides):
    defaults = {
        "cnpj": VALID_CNPJ,
        "razao_social": "Empresa Teste",
        "uf": "PE",
        "cidade": "Recife",
        "logradouro": "Rua X",
        "numero": "1",
        "bairro": "Centro",
        "cep": "50060000",
    }
    defaults.update(overrides)
    return DestinatarioHome.create(**defaults)


def _create_pf(**overrides):
    defaults = {
        "cpf": VALID_CPF,
        "razao_social": "Maria Silva",
        "uf": "SP",
        "cidade": "São Paulo",
        "logradouro": "Av Paulista",
        "numero": "100",
        "bairro": "Bela Vista",
        "cep": "01310100",
    }
    defaults.update(overrides)
    return DestinatarioHome.create(**defaults)


class TestMemoryDestinatarioRepository:
    def setup_method(self):
        self.state = MemoryState()
        self.state.clear()
        self.repo = MemoryDestinatarioRepository(self.state)

    def test_save_and_find_by_id(self):
        entity = _create_pj()
        self.repo.save(entity)
        found = self.repo.find_by_id(entity.id)
        assert found is not None
        assert found.cnpj == VALID_CNPJ
        assert found.razao_social == "Empresa Teste"

    def test_save_pf_and_find_by_id(self):
        entity = _create_pf()
        self.repo.save(entity)
        found = self.repo.find_by_id(entity.id)
        assert found is not None
        assert found.cpf == VALID_CPF
        assert found.cnpj is None

    def test_find_by_cnpj(self):
        entity = _create_pj()
        self.repo.save(entity)
        found = self.repo.find_by_cnpj(VALID_CNPJ)
        assert found is not None
        assert found.id == entity.id

    def test_find_by_cnpj_returns_none_for_missing(self):
        assert self.repo.find_by_cnpj("99999999999999") is None

    def test_find_all_returns_saved_entities(self):
        e1 = _create_pj()
        e2 = _create_pf()
        self.repo.save(e1)
        self.repo.save(e2)
        all_entities = self.repo.find_all()
        assert len(all_entities) == 2

    def test_delete_removes_entity(self):
        entity = _create_pj()
        self.repo.save(entity)
        assert self.repo.delete(entity.id) is True
        assert self.repo.find_by_id(entity.id) is None

    def test_find_by_id_returns_none_for_missing(self):
        assert self.repo.find_by_id(uuid4()) is None

    def test_seed_if_empty_creates_two_records(self):
        self.repo.seed_if_empty()
        all_entities = self.repo.find_all()
        assert len(all_entities) >= 2

    def test_seed_if_empty_has_geo_diversity(self):
        self.repo.seed_if_empty()
        all_entities = self.repo.find_all()
        ufs = {e.uf for e in all_entities}
        assert "PE" in ufs
        assert "SP" in ufs

    def test_seed_if_empty_skips_when_not_empty(self):
        entity = _create_pj()
        self.repo.save(entity)
        self.repo.seed_if_empty()
        assert len(self.repo.find_all()) == 1
