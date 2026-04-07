"""Destinatario entity tests."""

import pytest
from src.domain.destinatario.home import DestinatarioHome
from src.domain.destinatario.enums import DestinatarioStatus


class TestCreateDestinatario:
    def test_create_destinatario_has_correct_name(self):
        entity = DestinatarioHome.create(name="Test Destinatario")
        assert entity.name == "Test Destinatario"

    def test_create_destinatario_has_active_status(self):
        entity = DestinatarioHome.create(name="Test")
        assert entity.status == DestinatarioStatus.ACTIVE

    def test_create_destinatario_has_uuid_id(self):
        entity = DestinatarioHome.create(name="Test")
        assert entity.id is not None


class TestUpdateDestinatario:
    def test_update_name_changes_name(self):
        entity = DestinatarioHome.create(name="Original")
        entity.update_name("Updated")
        assert entity.name == "Updated"

    def test_update_name_sets_updated_at(self):
        entity = DestinatarioHome.create(name="Original")
        assert entity.updated_at is None
        entity.update_name("Updated")
        assert entity.updated_at is not None

    def test_update_name_empty_raises_error(self):
        entity = DestinatarioHome.create(name="Original")
        with pytest.raises(ValueError):
            entity.update_name("")
