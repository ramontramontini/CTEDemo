"""Remetente entity tests."""

import pytest
from src.domain.remetente.home import RemetenteHome
from src.domain.remetente.enums import RemetenteStatus


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


class TestCreateRemetente:
    def test_create_has_cnpj(self):
        entity = _create_remetente()
        assert entity.cnpj == VALID_CNPJ

    def test_create_has_razao_social(self):
        entity = _create_remetente()
        assert entity.razao_social == "Empresa ABC Ltda"

    def test_create_has_nome_fantasia(self):
        entity = _create_remetente()
        assert entity.nome_fantasia == "ABC"

    def test_create_has_ie(self):
        entity = _create_remetente()
        assert entity.ie == "123456789"

    def test_create_has_uf(self):
        entity = _create_remetente()
        assert entity.uf == "SP"

    def test_create_has_cidade(self):
        entity = _create_remetente()
        assert entity.cidade == "São Paulo"

    def test_create_has_logradouro(self):
        entity = _create_remetente()
        assert entity.logradouro == "Rua das Flores"

    def test_create_has_numero(self):
        entity = _create_remetente()
        assert entity.numero == "100"

    def test_create_has_bairro(self):
        entity = _create_remetente()
        assert entity.bairro == "Centro"

    def test_create_has_cep(self):
        entity = _create_remetente()
        assert entity.cep == "01001000"

    def test_create_has_active_status(self):
        entity = _create_remetente()
        assert entity.status == RemetenteStatus.ACTIVE

    def test_create_has_uuid_id(self):
        entity = _create_remetente()
        assert entity.id is not None

    def test_create_strips_cnpj_formatting(self):
        entity = _create_remetente(cnpj="11.222.333/0001-81")
        assert entity.cnpj == VALID_CNPJ

    def test_create_strips_cep_formatting(self):
        entity = _create_remetente(cep="01001-000")
        assert entity.cep == "01001000"

    def test_create_empty_ie_allowed(self):
        entity = _create_remetente(ie="")
        assert entity.ie == ""

    def test_create_nome_fantasia_defaults_empty(self):
        entity = _create_remetente(nome_fantasia="")
        assert entity.nome_fantasia == ""


class TestRemetenteValidation:
    def test_invalid_cnpj_raises_error(self):
        with pytest.raises(ValueError):
            _create_remetente(cnpj="12345678901234")

    def test_empty_cnpj_raises_error(self):
        with pytest.raises(ValueError):
            _create_remetente(cnpj="")

    def test_empty_razao_social_raises_error(self):
        with pytest.raises(ValueError):
            _create_remetente(razao_social="")

    def test_whitespace_razao_social_raises_error(self):
        with pytest.raises(ValueError):
            _create_remetente(razao_social="   ")

    def test_invalid_uf_raises_error(self):
        with pytest.raises(ValueError):
            _create_remetente(uf="SPP")

    def test_invalid_cep_raises_error(self):
        with pytest.raises(ValueError):
            _create_remetente(cep="1234")


class TestUpdateRemetente:
    def test_update_razao_social(self):
        entity = _create_remetente()
        entity.update_razao_social("Nova Razão")
        assert entity.razao_social == "Nova Razão"

    def test_update_razao_social_sets_updated_at(self):
        entity = _create_remetente()
        assert entity.updated_at is None
        entity.update_razao_social("Nova Razão")
        assert entity.updated_at is not None

    def test_update_razao_social_empty_raises_error(self):
        entity = _create_remetente()
        with pytest.raises(ValueError):
            entity.update_razao_social("")

    def test_update_nome_fantasia(self):
        entity = _create_remetente()
        entity.update_nome_fantasia("New Fantasy")
        assert entity.nome_fantasia == "New Fantasy"
        assert entity.updated_at is not None

    def test_update_ie(self):
        entity = _create_remetente()
        entity.update_ie("999888777")
        assert entity.ie == "999888777"
        assert entity.updated_at is not None

    def test_update_endereco(self):
        entity = _create_remetente()
        entity.update_endereco(
            uf="RJ",
            cidade="Rio de Janeiro",
            logradouro="Av. Brasil",
            numero="200",
            bairro="Copacabana",
            cep="22041080",
        )
        assert entity.uf == "RJ"
        assert entity.cidade == "Rio de Janeiro"
        assert entity.cep == "22041080"
