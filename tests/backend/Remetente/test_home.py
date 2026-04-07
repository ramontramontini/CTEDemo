"""Remetente Home tests."""

import pytest
from src.domain.remetente.home import RemetenteHome


class TestRemetenteHome:
    def test_create_returns_entity(self):
        entity = RemetenteHome.create(name="Test")
        assert entity is not None
        assert entity.name == "Test"

    def test_create_empty_name_raises_error(self):
        with pytest.raises(ValueError):
            RemetenteHome.create(name="")

    def test_create_whitespace_name_raises_error(self):
        with pytest.raises(ValueError):
            RemetenteHome.create(name="   ")

    def test_create_strips_name_whitespace(self):
        entity = RemetenteHome.create(name="  Padded  ")
        assert entity.name == "Padded"
