"""Cte Home tests."""

import pytest
from src.domain.cte.home import CteHome


class TestCteHome:
    def test_create_returns_entity(self):
        entity = CteHome.create(name="Test")
        assert entity is not None
        assert entity.name == "Test"

    def test_create_empty_name_raises_error(self):
        with pytest.raises(ValueError):
            CteHome.create(name="")

    def test_create_whitespace_name_raises_error(self):
        with pytest.raises(ValueError):
            CteHome.create(name="   ")

    def test_create_strips_name_whitespace(self):
        entity = CteHome.create(name="  Padded  ")
        assert entity.name == "Padded"
