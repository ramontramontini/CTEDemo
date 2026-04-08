"""CfopGeographicValidator unit tests."""

import pytest

from src.domain.cte.cfop_validator import CfopGeographicValidator


class TestSameStateCfop:
    """AC1: Same-state CFOP accepted. AC2: Cross-state CFOP rejected."""

    def test_same_state_cfop_5xxx_accepted(self):
        folders = [{"CFOP": "5352"}]
        errors = CfopGeographicValidator.validate("PE", "PE", folders)
        assert errors == []

    def test_cross_state_cfop_6xxx_accepted(self):
        folders = [{"CFOP": "6352"}]
        errors = CfopGeographicValidator.validate("PE", "SP", folders)
        assert errors == []

    def test_same_state_cfop_6xxx_rejected(self):
        folders = [{"CFOP": "6352"}]
        errors = CfopGeographicValidator.validate("PE", "PE", folders)
        assert len(errors) == 1
        assert "requer estados diferentes" in errors[0]
        assert "PE" in errors[0]

    def test_cross_state_cfop_5xxx_rejected(self):
        folders = [{"CFOP": "5352"}]
        errors = CfopGeographicValidator.validate("PE", "SP", folders)
        assert len(errors) == 1
        assert "requer mesmo estado" in errors[0]
        assert "PE" in errors[0]
        assert "SP" in errors[0]


class TestInternationalBypass:
    """AC3: International CFOP 7xxx skips UF check."""

    def test_international_cfop_7xxx_skips_uf_check(self):
        folders = [{"CFOP": "7352"}]
        errors = CfopGeographicValidator.validate("PE", "PE", folders)
        assert errors == []

    def test_international_cfop_7xxx_skips_cross_state_check(self):
        folders = [{"CFOP": "7352"}]
        errors = CfopGeographicValidator.validate("PE", "SP", folders)
        assert errors == []


class TestPerFolderValidation:
    """AC4: Mixed folders validated independently."""

    def test_mixed_folders_validates_each_independently(self):
        folders = [
            {"CFOP": "6352"},  # folder 0: valid (PE != SP, 6xxx = interstate)
            {"CFOP": "6352"},  # folder 1: invalid (PE == PE, 6xxx requires different)
            {"CFOP": "5352"},  # folder 2: valid (PE == PE, 5xxx = same state)
        ]
        # origin PE, dest for folder 0 and 2 would need different UFs
        # but validator receives single origin/dest pair
        # test with same state — folder 0 and 1 have 6xxx (requires different), folder 2 has 5xxx (ok)
        errors = CfopGeographicValidator.validate("PE", "PE", folders)
        assert len(errors) == 2  # folders 0 and 1 have 6xxx with same state
        assert "Folder[0]" in errors[0]
        assert "Folder[1]" in errors[1]

    def test_all_folders_valid_returns_empty(self):
        folders = [
            {"CFOP": "5352"},
            {"CFOP": "5353"},
        ]
        errors = CfopGeographicValidator.validate("PE", "PE", folders)
        assert errors == []
