"""Transportadora entity tests — enriched with CT-e XML fields."""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from src.domain.transportadora.entity import Transportadora
from src.domain.transportadora.enums import TransportadoraStatus
from src.domain.shared.cnpj import Cnpj


VALID_CNPJ = "11222333000181"


class TestTransportadoraEntity:
    def _make_entity(self, **overrides):
        defaults = dict(
            id=uuid4(),
            cnpj=Cnpj(VALID_CNPJ),
            razao_social="Transportadora ABC Ltda",
            nome_fantasia="ABC Transportes",
            ie="123456789",
            uf="SP",
            cidade="Sao Paulo",
            logradouro="Rua das Flores",
            numero="100",
            bairro="Centro",
            cep="01001000",
            status=TransportadoraStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
        )
        defaults.update(overrides)
        return Transportadora(**defaults)

    def test_create_entity_has_all_fields(self):
        entity = self._make_entity()
        assert entity.cnpj == VALID_CNPJ
        assert entity.razao_social == "Transportadora ABC Ltda"
        assert entity.nome_fantasia == "ABC Transportes"
        assert entity.ie == "123456789"
        assert entity.uf == "SP"
        assert entity.cidade == "Sao Paulo"
        assert entity.logradouro == "Rua das Flores"
        assert entity.numero == "100"
        assert entity.bairro == "Centro"
        assert entity.cep == "01001000"
        assert entity.status == TransportadoraStatus.ACTIVE
        assert entity.id is not None
        assert entity.created_at is not None
        assert entity.updated_at is None

    def test_cnpj_property_returns_string(self):
        entity = self._make_entity()
        assert isinstance(entity.cnpj, str)
        assert entity.cnpj == VALID_CNPJ

    def test_update_sets_updated_at(self):
        entity = self._make_entity()
        assert entity.updated_at is None
        entity.update(razao_social="New Name")
        assert entity.updated_at is not None

    def test_update_razao_social(self):
        entity = self._make_entity()
        entity.update(razao_social="Updated Name")
        assert entity.razao_social == "Updated Name"

    def test_update_empty_razao_social_raises(self):
        entity = self._make_entity()
        with pytest.raises(ValueError, match="razao_social"):
            entity.update(razao_social="")

    def test_update_cnpj_validates(self):
        entity = self._make_entity()
        with pytest.raises(ValueError, match="CNPJ"):
            entity.update(cnpj="00000000000000")

    def test_repr_includes_cnpj(self):
        entity = self._make_entity()
        r = repr(entity)
        assert VALID_CNPJ in r

    def test_optional_fields_accept_empty_string(self):
        entity = self._make_entity(nome_fantasia="", ie="")
        assert entity.nome_fantasia == ""
        assert entity.ie == ""
