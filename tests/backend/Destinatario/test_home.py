"""Destinatario Home tests."""

import pytest
from src.domain.destinatario.home import DestinatarioHome


VALID_CNPJ = "11222333000181"
VALID_CPF = "12345678909"


def _valid_pj_kwargs(**overrides):
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
    return defaults


def _valid_pf_kwargs(**overrides):
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
    return defaults


class TestDestinatarioHome:
    def test_create_pj_returns_entity(self):
        entity = DestinatarioHome.create(**_valid_pj_kwargs())
        assert entity is not None
        assert entity.cnpj == VALID_CNPJ
        assert entity.cpf is None

    def test_create_pf_returns_entity(self):
        entity = DestinatarioHome.create(**_valid_pf_kwargs())
        assert entity is not None
        assert entity.cpf == VALID_CPF
        assert entity.cnpj is None

    def test_create_neither_raises_error(self):
        with pytest.raises(ValueError, match="CNPJ ou CPF"):
            DestinatarioHome.create(
                razao_social="Test", uf="SP", cidade="SP",
                logradouro="Rua", numero="1", bairro="B", cep="01001000",
            )

    def test_create_both_raises_error(self):
        with pytest.raises(ValueError, match="CNPJ ou CPF"):
            DestinatarioHome.create(
                cnpj=VALID_CNPJ, cpf=VALID_CPF,
                razao_social="Test", uf="SP", cidade="SP",
                logradouro="Rua", numero="1", bairro="B", cep="01001000",
            )

    def test_create_invalid_cnpj_raises_error(self):
        with pytest.raises(ValueError):
            DestinatarioHome.create(**_valid_pj_kwargs(cnpj="12345678901234"))

    def test_create_invalid_cpf_raises_error(self):
        with pytest.raises(ValueError):
            DestinatarioHome.create(**_valid_pf_kwargs(cpf="00000000000"))

    def test_create_empty_razao_social_raises_error(self):
        with pytest.raises(ValueError):
            DestinatarioHome.create(**_valid_pj_kwargs(razao_social=""))

    def test_create_whitespace_razao_social_raises_error(self):
        with pytest.raises(ValueError):
            DestinatarioHome.create(**_valid_pj_kwargs(razao_social="   "))

    def test_create_strips_razao_social(self):
        entity = DestinatarioHome.create(**_valid_pj_kwargs(razao_social="  Padded  "))
        assert entity.razao_social == "Padded"

    def test_create_invalid_uf_raises_error(self):
        with pytest.raises(ValueError):
            DestinatarioHome.create(**_valid_pj_kwargs(uf="SPP"))

    def test_create_invalid_cep_raises_error(self):
        with pytest.raises(ValueError):
            DestinatarioHome.create(**_valid_pj_kwargs(cep="1234"))

    def test_create_strips_cnpj_formatting(self):
        entity = DestinatarioHome.create(**_valid_pj_kwargs(cnpj="11.222.333/0001-81"))
        assert entity.cnpj == VALID_CNPJ
