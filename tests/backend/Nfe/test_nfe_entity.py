"""Tests for Nfe entity."""

import pytest

from src.domain.nfe.entity import Nfe


class TestNfeEntity:
    def test_nfe_is_frozen(self):
        nfe = Nfe(key="1" * 44, status="authorized", emitter_cnpj="10758386000159")
        with pytest.raises(AttributeError):
            nfe.key = "changed"

    def test_nfe_fields_accessible(self):
        nfe = Nfe(key="1" * 44, status="authorized", emitter_cnpj="10758386000159")
        assert nfe.key == "1" * 44
        assert nfe.status == "authorized"
        assert nfe.emitter_cnpj == "10758386000159"

    def test_nfe_statuses(self):
        for status in ("authorized", "canceled", "draft"):
            nfe = Nfe(key="1" * 44, status=status, emitter_cnpj="10758386000159")
            assert nfe.status == status
