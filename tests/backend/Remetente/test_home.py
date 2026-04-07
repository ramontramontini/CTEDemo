"""Remetente Home tests."""

import pytest
from src.domain.remetente.home import RemetenteHome
from src.domain.remetente.enums import RemetenteStatus


VALID_CNPJ = "11222333000181"


def _valid_kwargs(**overrides):
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
    return defaults


class TestRemetenteHome:
    def test_create_returns_entity(self):
        entity = RemetenteHome.create(**_valid_kwargs())
        assert entity.cnpj == VALID_CNPJ
        assert entity.status == RemetenteStatus.ACTIVE

    def test_create_empty_cnpj_raises(self):
        with pytest.raises(ValueError):
            RemetenteHome.create(**_valid_kwargs(cnpj=""))

    def test_create_invalid_cnpj_raises(self):
        with pytest.raises(ValueError):
            RemetenteHome.create(**_valid_kwargs(cnpj="00000000000000"))

    def test_create_strips_cnpj_formatting(self):
        entity = RemetenteHome.create(**_valid_kwargs(cnpj="11.222.333/0001-81"))
        assert entity.cnpj == VALID_CNPJ

    def test_create_empty_razao_social_raises(self):
        with pytest.raises(ValueError):
            RemetenteHome.create(**_valid_kwargs(razao_social=""))

    def test_create_whitespace_razao_social_raises(self):
        with pytest.raises(ValueError):
            RemetenteHome.create(**_valid_kwargs(razao_social="   "))

    def test_create_strips_razao_social(self):
        entity = RemetenteHome.create(**_valid_kwargs(razao_social="  ABC  "))
        assert entity.razao_social == "ABC"

    def test_create_invalid_uf_raises(self):
        with pytest.raises(ValueError):
            RemetenteHome.create(**_valid_kwargs(uf="ABC"))

    def test_create_invalid_cep_raises(self):
        with pytest.raises(ValueError):
            RemetenteHome.create(**_valid_kwargs(cep="123"))

    def test_create_optional_ie_empty(self):
        entity = RemetenteHome.create(**_valid_kwargs(ie=""))
        assert entity.ie == ""

    def test_create_optional_nome_fantasia_empty(self):
        entity = RemetenteHome.create(**_valid_kwargs(nome_fantasia=""))
        assert entity.nome_fantasia == ""
