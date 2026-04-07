"""Remetente entity tests."""

import pytest
from src.domain.remetente.home import RemetenteHome
from src.domain.remetente.enums import RemetenteStatus


class TestCreateRemetente:
    def test_create_remetente_has_correct_name(self):
        entity = RemetenteHome.create(name="Test Remetente")
        assert entity.name == "Test Remetente"

    def test_create_remetente_has_active_status(self):
        entity = RemetenteHome.create(name="Test")
        assert entity.status == RemetenteStatus.ACTIVE

    def test_create_remetente_has_uuid_id(self):
        entity = RemetenteHome.create(name="Test")
        assert entity.id is not None


class TestUpdateRemetente:
    def test_update_name_changes_name(self):
        entity = RemetenteHome.create(name="Original")
        entity.update_name("Updated")
        assert entity.name == "Updated"

    def test_update_name_sets_updated_at(self):
        entity = RemetenteHome.create(name="Original")
        assert entity.updated_at is None
        entity.update_name("Updated")
        assert entity.updated_at is not None

    def test_update_name_empty_raises_error(self):
        entity = RemetenteHome.create(name="Original")
        with pytest.raises(ValueError):
            entity.update_name("")
