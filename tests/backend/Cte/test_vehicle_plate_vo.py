"""Tests for VehiclePlate value object — old + Mercosul format."""

import pytest

from src.domain.shared.vehicle_plate import VehiclePlate


class TestVehiclePlate:
    """VehiclePlate VO validation tests."""

    def test_old_format_accepted(self):
        plate = VehiclePlate("ABC1234")
        assert plate.value == "ABC1234"

    def test_mercosul_format_accepted(self):
        plate = VehiclePlate("ABC1D23")
        assert plate.value == "ABC1D23"

    def test_lowercase_converted_to_upper(self):
        plate = VehiclePlate("abc1d23")
        assert plate.value == "ABC1D23"

    def test_invalid_format_rejected(self):
        with pytest.raises(ValueError, match="formato"):
            VehiclePlate("1234ABC")

    def test_too_short_rejected(self):
        with pytest.raises(ValueError, match="formato"):
            VehiclePlate("ABC12")

    def test_too_long_rejected(self):
        with pytest.raises(ValueError, match="formato"):
            VehiclePlate("ABC12345")

    def test_all_letters_rejected(self):
        with pytest.raises(ValueError, match="formato"):
            VehiclePlate("ABCDEFG")

    def test_all_numbers_rejected(self):
        with pytest.raises(ValueError, match="formato"):
            VehiclePlate("1234567")

    def test_empty_rejected(self):
        with pytest.raises(ValueError):
            VehiclePlate("")

    def test_str_returns_value(self):
        plate = VehiclePlate("ABC1234")
        assert str(plate) == "ABC1234"

    def test_equality(self):
        assert VehiclePlate("ABC1234") == VehiclePlate("ABC1234")

    def test_immutable(self):
        plate = VehiclePlate("ABC1234")
        with pytest.raises(AttributeError):
            plate.value = "XYZ9999"
