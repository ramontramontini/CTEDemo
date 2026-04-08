"""Destinatario entity tests."""

import pytest
from src.domain.destinatario.home import DestinatarioHome
from src.domain.destinatario.enums import DestinatarioStatus


VALID_CNPJ = "11222333000181"
VALID_CPF = "12345678909"


def _create_destinatario_pj(**overrides):
    defaults = {
        "cnpj": VALID_CNPJ,
        "razao_social": "Comercio Recife Ltda",
        "nome_fantasia": "Recife Com",
        "ie": "123456789",
        "uf": "PE",
        "cidade": "Recife",
        "logradouro": "Rua do Sol",
        "numero": "50",
        "bairro": "Boa Vista",
        "cep": "50060000",
    }
    defaults.update(overrides)
    return DestinatarioHome.create(**defaults)


def _create_destinatario_pf(**overrides):
    defaults = {
        "cpf": VALID_CPF,
        "razao_social": "Maria Silva",
        "uf": "SP",
        "cidade": "São Paulo",
        "logradouro": "Av Paulista",
        "numero": "1000",
        "bairro": "Bela Vista",
        "cep": "01310100",
    }
    defaults.update(overrides)
    return DestinatarioHome.create(**defaults)


class TestCreateDestinatarioPJ:
    def test_create_has_cnpj(self):
        entity = _create_destinatario_pj()
        assert entity.cnpj == VALID_CNPJ

    def test_create_has_null_cpf(self):
        entity = _create_destinatario_pj()
        assert entity.cpf is None

    def test_create_has_razao_social(self):
        entity = _create_destinatario_pj()
        assert entity.razao_social == "Comercio Recife Ltda"

    def test_create_has_nome_fantasia(self):
        entity = _create_destinatario_pj()
        assert entity.nome_fantasia == "Recife Com"

    def test_create_has_ie(self):
        entity = _create_destinatario_pj()
        assert entity.ie == "123456789"

    def test_create_has_uf(self):
        entity = _create_destinatario_pj()
        assert entity.uf == "PE"

    def test_create_has_cidade(self):
        entity = _create_destinatario_pj()
        assert entity.cidade == "Recife"

    def test_create_has_logradouro(self):
        entity = _create_destinatario_pj()
        assert entity.logradouro == "Rua do Sol"

    def test_create_has_numero(self):
        entity = _create_destinatario_pj()
        assert entity.numero == "50"

    def test_create_has_bairro(self):
        entity = _create_destinatario_pj()
        assert entity.bairro == "Boa Vista"

    def test_create_has_cep(self):
        entity = _create_destinatario_pj()
        assert entity.cep == "50060000"

    def test_create_has_active_status(self):
        entity = _create_destinatario_pj()
        assert entity.status == DestinatarioStatus.ACTIVE

    def test_create_has_uuid_id(self):
        entity = _create_destinatario_pj()
        assert entity.id is not None

    def test_create_strips_cnpj_formatting(self):
        entity = _create_destinatario_pj(cnpj="11.222.333/0001-81")
        assert entity.cnpj == VALID_CNPJ

    def test_create_strips_cep_formatting(self):
        entity = _create_destinatario_pj(cep="50060-000")
        assert entity.cep == "50060000"

    def test_create_empty_ie_allowed(self):
        entity = _create_destinatario_pj(ie="")
        assert entity.ie == ""

    def test_create_nome_fantasia_defaults_empty(self):
        entity = _create_destinatario_pj(nome_fantasia="")
        assert entity.nome_fantasia == ""


class TestCreateDestinatarioPF:
    def test_create_has_cpf(self):
        entity = _create_destinatario_pf()
        assert entity.cpf == VALID_CPF

    def test_create_has_null_cnpj(self):
        entity = _create_destinatario_pf()
        assert entity.cnpj is None

    def test_create_has_razao_social(self):
        entity = _create_destinatario_pf()
        assert entity.razao_social == "Maria Silva"

    def test_create_has_empty_nome_fantasia(self):
        entity = _create_destinatario_pf()
        assert entity.nome_fantasia == ""

    def test_create_has_empty_ie(self):
        entity = _create_destinatario_pf()
        assert entity.ie == ""

    def test_create_has_uf(self):
        entity = _create_destinatario_pf()
        assert entity.uf == "SP"


class TestDestinatarioValidation:
    def test_invalid_cnpj_raises_error(self):
        with pytest.raises(ValueError):
            _create_destinatario_pj(cnpj="12345678901234")

    def test_empty_cnpj_and_cpf_raises_error(self):
        with pytest.raises(ValueError, match="CNPJ ou CPF"):
            DestinatarioHome.create(
                razao_social="Test", uf="SP", cidade="SP",
                logradouro="Rua X", numero="1", bairro="B", cep="01001000",
            )

    def test_both_cnpj_and_cpf_raises_error(self):
        with pytest.raises(ValueError, match="CNPJ ou CPF"):
            DestinatarioHome.create(
                cnpj=VALID_CNPJ, cpf=VALID_CPF,
                razao_social="Test", uf="SP", cidade="SP",
                logradouro="Rua X", numero="1", bairro="B", cep="01001000",
            )

    def test_invalid_cpf_raises_error(self):
        with pytest.raises(ValueError):
            _create_destinatario_pf(cpf="00000000000")

    def test_empty_razao_social_raises_error(self):
        with pytest.raises(ValueError):
            _create_destinatario_pj(razao_social="")

    def test_whitespace_razao_social_raises_error(self):
        with pytest.raises(ValueError):
            _create_destinatario_pj(razao_social="   ")

    def test_invalid_uf_raises_error(self):
        with pytest.raises(ValueError):
            _create_destinatario_pj(uf="SPP")

    def test_invalid_cep_raises_error(self):
        with pytest.raises(ValueError):
            _create_destinatario_pj(cep="1234")


class TestUpdateDestinatario:
    def test_update_razao_social(self):
        entity = _create_destinatario_pj()
        entity.update_razao_social("Nova Razão")
        assert entity.razao_social == "Nova Razão"

    def test_update_razao_social_sets_updated_at(self):
        entity = _create_destinatario_pj()
        assert entity.updated_at is None
        entity.update_razao_social("Nova Razão")
        assert entity.updated_at is not None

    def test_update_razao_social_empty_raises_error(self):
        entity = _create_destinatario_pj()
        with pytest.raises(ValueError):
            entity.update_razao_social("")

    def test_update_nome_fantasia(self):
        entity = _create_destinatario_pj()
        entity.update_nome_fantasia("New Fantasy")
        assert entity.nome_fantasia == "New Fantasy"
        assert entity.updated_at is not None

    def test_update_ie(self):
        entity = _create_destinatario_pj()
        entity.update_ie("999888777")
        assert entity.ie == "999888777"
        assert entity.updated_at is not None

    def test_update_endereco(self):
        entity = _create_destinatario_pj()
        entity.update_endereco(
            uf="RJ", cidade="Rio de Janeiro",
            logradouro="Av Brasil", numero="200",
            bairro="Copacabana", cep="22041080",
        )
        assert entity.uf == "RJ"
        assert entity.cidade == "Rio de Janeiro"
        assert entity.cep == "22041080"

    def test_private_fields_not_directly_accessible(self):
        entity = _create_destinatario_pj()
        with pytest.raises(AttributeError):
            _ = entity._cnpj_direct_access

    def test_update_endereco_invalid_cep_raises(self):
        entity = _create_destinatario_pj()
        with pytest.raises(ValueError):
            entity.update_endereco(
                uf="RJ", cidade="Rio", logradouro="Rua",
                numero="1", bairro="B", cep="123",
            )
