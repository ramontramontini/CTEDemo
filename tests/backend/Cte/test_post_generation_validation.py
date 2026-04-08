"""Tests for post-generation CT-e validation."""

import pytest

from src.domain.cte.validation import validate_generated_cte
from src.domain.cte.value_objects import AccessKey


# Generate a valid access key for test fixtures
_VALID_KEY = AccessKey.generate(
    uf="26", aamm="2604", cnpj="16003754000135", serie="020", numero=1, codigo="00000001"
)

_REQUIRED_ELEMENTS = [
    "cteProc", "CTe", "infCte", "ide", "emit", "rem", "vPrest", "imp", "infCTeNorm"
]


def _build_valid_xml() -> str:
    """Build minimal valid XML with all required CT-e elements."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<cteProc><CTe><infCte>"
        "<ide/><emit/><rem/><vPrest/><imp/><infCTeNorm/>"
        "</infCte></CTe></cteProc>"
    )


def _build_xml_missing(element: str) -> str:
    """Build XML with a specific required element removed."""
    parts = {
        "cteProc": True, "CTe": True, "infCte": True,
        "ide": True, "emit": True, "rem": True,
        "vPrest": True, "imp": True, "infCTeNorm": True,
    }
    parts[element] = False

    inner = ""
    for tag in ["ide", "emit", "rem", "vPrest", "imp", "infCTeNorm"]:
        if parts[tag]:
            inner += f"<{tag}/>"

    xml = '<?xml version="1.0" encoding="UTF-8"?>'
    if not parts["cteProc"]:
        xml += f"<root><CTe><infCte>{inner}</infCte></CTe></root>"
    elif not parts["CTe"]:
        xml += f"<cteProc><infCte>{inner}</infCte></cteProc>"
    elif not parts["infCte"]:
        xml += f"<cteProc><CTe>{inner}</CTe></cteProc>"
    else:
        xml += f"<cteProc><CTe><infCte>{inner}</infCte></CTe></cteProc>"

    return xml


class TestPostGenValidation:
    """Post-generation CT-e validation tests."""

    def test_valid_cte_passes(self):
        errors = validate_generated_cte(_VALID_KEY.value, _build_valid_xml())
        assert errors == []

    def test_access_key_not_44_digits_fails(self):
        short_key = "1234567890"
        errors = validate_generated_cte(short_key, _build_valid_xml())
        assert any("44 dígitos" in e for e in errors)

    def test_access_key_non_numeric_fails(self):
        bad_key = "A" * 44
        errors = validate_generated_cte(bad_key, _build_valid_xml())
        assert any("44 dígitos" in e for e in errors)

    def test_invalid_dv_fails(self):
        # Corrupt the DV (last digit) by incrementing it
        key = _VALID_KEY.value
        bad_dv = str((int(key[-1]) + 1) % 10)
        bad_key = key[:-1] + bad_dv
        errors = validate_generated_cte(bad_key, _build_valid_xml())
        assert any("DV" in e or "dígito verificador" in e.lower() for e in errors)

    def test_missing_xml_element_flags_which(self):
        xml = _build_xml_missing("rem")
        errors = validate_generated_cte(_VALID_KEY.value, xml)
        assert any("rem" in e for e in errors)

    def test_multiple_missing_elements_all_reported(self):
        # XML missing both rem and vPrest
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<cteProc><CTe><infCte>"
            "<ide/><emit/><imp/><infCTeNorm/>"
            "</infCte></CTe></cteProc>"
        )
        errors = validate_generated_cte(_VALID_KEY.value, xml)
        error_text = "\n".join(errors)
        assert "rem" in error_text
        assert "vPrest" in error_text
