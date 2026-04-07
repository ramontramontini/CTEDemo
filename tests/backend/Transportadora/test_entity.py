"""Transportadora entity tests."""

import pytest
from src.domain.transportadora.home import TransportadoraHome
from src.domain.transportadora.enums import TransportadoraStatus


class TestCreateTransportadora:
    def test_create_transportadora_has_correct_name(self):
        entity = TransportadoraHome.create(name="Test Transportadora")
        assert entity.name == "Test Transportadora"

    def test_create_transportadora_has_active_status(self):
        entity = TransportadoraHome.create(name="Test")
        assert entity.status == TransportadoraStatus.ACTIVE

    def test_create_transportadora_has_uuid_id(self):
        entity = TransportadoraHome.create(name="Test")
        assert entity.id is not None


class TestUpdateTransportadora:
    def test_update_name_changes_name(self):
        entity = TransportadoraHome.create(name="Original")
        entity.update_name("Updated")
        assert entity.name == "Updated"

    def test_update_name_sets_updated_at(self):
        entity = TransportadoraHome.create(name="Original")
        assert entity.updated_at is None
        entity.update_name("Updated")
        assert entity.updated_at is not None

    def test_update_name_empty_raises_error(self):
        entity = TransportadoraHome.create(name="Original")
        with pytest.raises(ValueError):
            entity.update_name("")
