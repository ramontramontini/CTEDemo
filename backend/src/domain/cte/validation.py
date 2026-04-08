"""Post-generation CT-e validation — defense-in-depth checks."""

import xml.etree.ElementTree as ET

from src.domain.cte.value_objects import AccessKey

REQUIRED_XML_ELEMENTS = (
    "cteProc", "CTe", "infCte", "ide", "emit", "rem", "vPrest", "imp", "infCTeNorm"
)


def validate_generated_cte(access_key: str, xml: str) -> list[str]:
    """Validate a generated CT-e for spec compliance.

    Returns a list of error strings. Empty list means validation passed.

    Checks:
    - access_key is exactly 44 numeric digits
    - DV (digit 44) passes mod11 verification
    - XML contains all required root elements per spec S5.3/S7
    """
    errors: list[str] = []

    _validate_access_key(access_key, errors)
    _validate_xml_elements(xml, errors)

    return errors


def _validate_access_key(access_key: str, errors: list[str]) -> None:
    if len(access_key) != 44 or not access_key.isdigit():
        errors.append(
            f"Chave de acesso deve ter 44 dígitos numéricos (recebido: {len(access_key)} chars)"
        )
        return

    base_43 = access_key[:43]
    expected_dv = AccessKey.calc_dv(base_43)
    actual_dv = int(access_key[43])
    if actual_dv != expected_dv:
        errors.append(
            f"Dígito verificador (DV) inválido: esperado {expected_dv}, recebido {actual_dv}"
        )


def _validate_xml_elements(xml: str, errors: list[str]) -> None:
    try:
        root = ET.fromstring(xml.encode("utf-8"))
    except ET.ParseError as e:
        errors.append(f"XML malformado: {e}")
        return

    # Strip namespace prefixes for tag matching
    all_tags = set()
    for elem in root.iter():
        tag = elem.tag
        if "}" in tag:
            tag = tag.split("}", 1)[1]
        all_tags.add(tag)

    missing = [tag for tag in REQUIRED_XML_ELEMENTS if tag not in all_tags]
    if missing:
        errors.append(
            f"Elementos obrigatórios ausentes no XML: {', '.join(missing)}"
        )
