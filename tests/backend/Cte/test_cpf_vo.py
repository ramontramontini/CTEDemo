"""Tests for Cpf value object — mod11 validation."""

import pytest

from src.domain.shared.cpf import Cpf


class TestCpf:
    """Cpf VO validation tests."""

    def test_valid_cpf_accepted(self):
        cpf = Cpf("12345678909")
        assert cpf.value == "12345678909"

    def test_valid_cpf_another(self):
        cpf = Cpf("52998224725")
        assert cpf.value == "52998224725"

    def test_wrong_length_rejected(self):
        with pytest.raises(ValueError, match="11 dígitos"):
            Cpf("123456789")

    def test_non_digits_rejected(self):
        with pytest.raises(ValueError, match="11 dígitos"):
            Cpf("1234567890A")

    def test_all_same_digits_rejected(self):
        with pytest.raises(ValueError, match="sequência repetida"):
            Cpf("11111111111")

    def test_all_zeros_rejected(self):
        with pytest.raises(ValueError, match="sequência repetida"):
            Cpf("00000000000")

    def test_invalid_dv_rejected(self):
        with pytest.raises(ValueError, match="dígito verificador"):
            Cpf("12345678900")

    def test_str_returns_value(self):
        cpf = Cpf("12345678909")
        assert str(cpf) == "12345678909"

    def test_equality(self):
        assert Cpf("12345678909") == Cpf("12345678909")

    def test_immutable(self):
        cpf = Cpf("12345678909")
        with pytest.raises(AttributeError):
            cpf.value = "99999999999"
