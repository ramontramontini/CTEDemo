"""Destinatario Home tests."""

import pytest
from src.domain.destinatario.home import DestinatarioHome


class TestDestinatarioHome:
    def test_create_returns_entity(self):
        entity = DestinatarioHome.create(name="Test")
        assert entity is not None
        assert entity.name == "Test"

    def test_create_empty_name_raises_error(self):
        with pytest.raises(ValueError):
            DestinatarioHome.create(name="")

    def test_create_whitespace_name_raises_error(self):
        with pytest.raises(ValueError):
            DestinatarioHome.create(name="   ")

    def test_create_strips_name_whitespace(self):
        entity = DestinatarioHome.create(name="  Padded  ")
        assert entity.name == "Padded"
