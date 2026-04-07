"""Tests for Cnpj value object — mod11 validation."""

import pytest

from src.domain.shared.cnpj import Cnpj


class TestCnpj:
    """Cnpj VO validation tests."""

    def test_valid_cnpj_accepted(self):
        cnpj = Cnpj("11222333000181")
        assert cnpj.value == "11222333000181"

    def test_valid_cnpj_another(self):
        cnpj = Cnpj("10758386000159")
        assert cnpj.value == "10758386000159"

    def test_wrong_length_rejected(self):
        with pytest.raises(ValueError, match="14 dígitos"):
            Cnpj("1234567890")

    def test_non_digits_rejected(self):
        with pytest.raises(ValueError, match="14 dígitos"):
            Cnpj("1175838600015A")

    def test_all_same_digits_rejected(self):
        with pytest.raises(ValueError, match="sequência repetida"):
            Cnpj("11111111111111")

    def test_all_zeros_rejected(self):
        with pytest.raises(ValueError, match="sequência repetida"):
            Cnpj("00000000000000")

    def test_invalid_dv_rejected(self):
        with pytest.raises(ValueError, match="dígito verificador"):
            Cnpj("11222333000182")

    def test_str_returns_value(self):
        cnpj = Cnpj("11222333000181")
        assert str(cnpj) == "11222333000181"

    def test_equality(self):
        assert Cnpj("11222333000181") == Cnpj("11222333000181")

    def test_immutable(self):
        cnpj = Cnpj("11222333000181")
        with pytest.raises(AttributeError):
            cnpj.value = "99999999999999"
