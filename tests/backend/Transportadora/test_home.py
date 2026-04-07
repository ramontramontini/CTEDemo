"""Transportadora Home tests."""

import pytest
from src.domain.transportadora.home import TransportadoraHome


class TestTransportadoraHome:
    def test_create_returns_entity(self):
        entity = TransportadoraHome.create(name="Test")
        assert entity is not None
        assert entity.name == "Test"

    def test_create_empty_name_raises_error(self):
        with pytest.raises(ValueError):
            TransportadoraHome.create(name="")

    def test_create_whitespace_name_raises_error(self):
        with pytest.raises(ValueError):
            TransportadoraHome.create(name="   ")

    def test_create_strips_name_whitespace(self):
        entity = TransportadoraHome.create(name="  Padded  ")
        assert entity.name == "Padded"
