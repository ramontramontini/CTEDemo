"""Cte entity tests."""

import pytest
from src.domain.cte.home import CteHome
from src.domain.cte.enums import CteStatus


class TestCreateCte:
    def test_create_cte_has_correct_name(self):
        entity = CteHome.create(name="Test Cte")
        assert entity.name == "Test Cte"

    def test_create_cte_has_active_status(self):
        entity = CteHome.create(name="Test")
        assert entity.status == CteStatus.ACTIVE

    def test_create_cte_has_uuid_id(self):
        entity = CteHome.create(name="Test")
        assert entity.id is not None


class TestUpdateCte:
    def test_update_name_changes_name(self):
        entity = CteHome.create(name="Original")
        entity.update_name("Updated")
        assert entity.name == "Updated"

    def test_update_name_sets_updated_at(self):
        entity = CteHome.create(name="Original")
        assert entity.updated_at is None
        entity.update_name("Updated")
        assert entity.updated_at is not None

    def test_update_name_empty_raises_error(self):
        entity = CteHome.create(name="Original")
        with pytest.raises(ValueError):
            entity.update_name("")
