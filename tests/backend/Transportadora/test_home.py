"""Transportadora Home tests — enriched with CT-e XML fields."""

import pytest
import re

from src.domain.transportadora.home import TransportadoraHome
from src.domain.transportadora.enums import TransportadoraStatus
from src.domain.transportadora.errors import TransportadoraValidationError


VALID_CNPJ = "11222333000181"


def _valid_kwargs(**overrides):
    defaults = dict(
        cnpj=VALID_CNPJ,
        razao_social="Transportadora ABC Ltda",
        nome_fantasia="ABC Transportes",
        ie="123456789",
        uf="SP",
        cidade="Sao Paulo",
        logradouro="Rua das Flores",
        numero="100",
        bairro="Centro",
        cep="01001000",
    )
    defaults.update(overrides)
    return defaults


class TestTransportadoraHomeCreate:
    def test_create_with_valid_data(self):
        entity = TransportadoraHome.create(**_valid_kwargs())
        assert entity.cnpj == VALID_CNPJ
        assert entity.razao_social == "Transportadora ABC Ltda"
        assert entity.status == TransportadoraStatus.ACTIVE
        assert entity.id is not None
        assert entity.created_at is not None

    def test_create_rejects_invalid_cnpj(self):
        with pytest.raises(TransportadoraValidationError, match="CNPJ"):
            TransportadoraHome.create(**_valid_kwargs(cnpj="00000000000000"))

    def test_create_rejects_empty_razao_social(self):
        with pytest.raises(TransportadoraValidationError, match="razao_social"):
            TransportadoraHome.create(**_valid_kwargs(razao_social=""))

    def test_create_strips_cnpj_formatting(self):
        entity = TransportadoraHome.create(**_valid_kwargs(cnpj="11.222.333/0001-81"))
        assert entity.cnpj == VALID_CNPJ

    def test_create_rejects_empty_required_fields(self):
        for field in ["uf", "cidade", "logradouro", "numero", "bairro", "cep"]:
            with pytest.raises(TransportadoraValidationError):
                TransportadoraHome.create(**_valid_kwargs(**{field: ""}))

    def test_create_accepts_empty_optional_fields(self):
        entity = TransportadoraHome.create(**_valid_kwargs(nome_fantasia="", ie=""))
        assert entity.nome_fantasia == ""
        assert entity.ie == ""
