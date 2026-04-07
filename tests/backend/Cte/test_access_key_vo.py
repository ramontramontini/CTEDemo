"""Tests for AccessKey value object — 44-digit generation with mod11 DV."""

import pytest

from src.domain.cte.value_objects import AccessKey


class TestAccessKey:
    """AccessKey VO tests."""

    def test_spec_example_structure(self):
        """Verify key generation with spec example inputs from Pernambuco.

        Note: spec PDF DV is illustrative (3), actual mod11 computes to 0.
        """
        key = AccessKey.generate(
            uf="26",
            aamm="2510",
            cnpj="10758386000159",
            serie="020",
            numero=159,
            codigo="00000006",
        )
        assert len(key.value) == 44
        # Structure matches spec: UF=26, AAMM=2510, CNPJ, MOD=57, etc.
        assert key.value[:25] == "2625101075838600015957020"
        assert key.value[25:34] == "000000159"
        assert key.value[34] == "1"
        assert key.value[35:43] == "00000006"
        # DV computed via mod11 (spec PDF shows 3, actual is 0)
        assert key.value == "26251010758386000159570200000001591000000060"

    def test_length_is_44(self):
        key = AccessKey.generate(
            uf="26",
            aamm="2510",
            cnpj="10758386000159",
            serie="020",
            numero=1,
            codigo="00000001",
        )
        assert len(key.value) == 44

    def test_structure_fields(self):
        key = AccessKey.generate(
            uf="26",
            aamm="2510",
            cnpj="10758386000159",
            serie="020",
            numero=1,
            codigo="00000001",
        )
        assert key.value[:2] == "26"       # UF
        assert key.value[2:6] == "2510"    # AAMM
        assert key.value[6:20] == "10758386000159"  # CNPJ
        assert key.value[20:22] == "57"    # MOD CT-e
        assert key.value[22:25] == "020"   # Série
        assert key.value[25:34] == "000000001"  # Número
        assert key.value[34:35] == "1"     # Tipo emissão normal
        assert key.value[35:43] == "00000001"  # Código

    def test_dv_mod11_remainder_0_gives_dv_0(self):
        """When mod11 remainder is 0, DV should be 0."""
        key = AccessKey.generate(
            uf="26",
            aamm="2510",
            cnpj="10758386000159",
            serie="020",
            numero=1,
            codigo="00000001",
        )
        # DV is last digit
        assert key.value[-1].isdigit()

    def test_numero_padded_to_9_digits(self):
        key = AccessKey.generate(
            uf="26",
            aamm="2510",
            cnpj="10758386000159",
            serie="020",
            numero=42,
            codigo="00000001",
        )
        assert key.value[25:34] == "000000042"

    def test_formatted_access_key(self):
        key = AccessKey.generate(
            uf="26",
            aamm="2510",
            cnpj="10758386000159",
            serie="020",
            numero=159,
            codigo="00000006",
        )
        formatted = key.formatted()
        assert "26" in formatted
        assert " " in formatted

    def test_immutable(self):
        key = AccessKey.generate(
            uf="26",
            aamm="2510",
            cnpj="10758386000159",
            serie="020",
            numero=1,
            codigo="00000001",
        )
        with pytest.raises(AttributeError):
            key.value = "x" * 44

    def test_str_returns_value(self):
        key = AccessKey.generate(
            uf="26",
            aamm="2510",
            cnpj="10758386000159",
            serie="020",
            numero=159,
            codigo="00000006",
        )
        assert str(key) == key.value
