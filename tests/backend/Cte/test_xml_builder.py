"""Tests for CT-e XML builder — all XML sections."""

import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from src.domain.cte.value_objects import AccessKey, FreightOrder
from src.domain.cte.xml_builder import build_cte_xml
from src.domain.destinatario.home import DestinatarioHome
from src.domain.remetente.home import RemetenteHome
from src.domain.transportadora.home import TransportadoraHome

NS = "http://www.portalfiscal.inf.br/cte"


VALID_PAYLOAD = {
    "FreightOrder": "12345678901234",
    "ERP": "SAP",
    "Carrier": "10758386000159",
    "CNPJ_Origin": "10758386000159",
    "Incoterms": "CIF",
    "OperationType": "0",
    "Folder": [
        {
            "FolderNumber": "001",
            "ReferenceNumber": "REF001",
            "NetValue": 1500.00,
            "VehiclePlate": "ABC1D23",
            "TrailerPlate": [],
            "VehicleAxles": "2",
            "EquipmentType": "TRUCK",
            "Weight": 5000.00,
            "CFOP": "6352",
            "DriverID": "12345678909",
            "Cancel": False,
            "Tax": [
                {
                    "TaxType": "ICMS",
                    "Base": 1500.00,
                    "Rate": 12.00,
                    "Value": 180.00,
                    "TaxCode": "00",
                    "ReducedBase": 0,
                }
            ],
            "RelatedNFE": ["12345678901234567890123456789012345678901234"],
        }
    ],
}


def _find(parent: ET.Element, tag: str) -> ET.Element:
    """Find child element handling namespace."""
    elem = parent.find(f"{{{NS}}}{tag}")
    if elem is None:
        elem = parent.find(tag)
    return elem


def _find_all(parent: ET.Element, tag: str) -> list[ET.Element]:
    """Find all child elements handling namespace."""
    elems = parent.findall(f"{{{NS}}}{tag}")
    if not elems:
        elems = parent.findall(tag)
    return elems


def _make_transportadora():
    return TransportadoraHome.create(
        cnpj="10758386000159",
        razao_social="Transportes PE Ltda",
        ie="987654321",
        uf="PE",
        cidade="Recife",
        logradouro="Rua da Aurora",
        numero="100",
        bairro="Boa Vista",
        cep="50060010",
    )


def _make_remetente():
    return RemetenteHome.create(
        cnpj="10758386000159",
        razao_social="Remetente SP Ltda",
        ie="123456789",
        uf="SP",
        cidade="São Paulo",
        logradouro="Av Paulista",
        numero="1000",
        bairro="Bela Vista",
        cep="01310100",
    )


def _make_destinatario_pj():
    return DestinatarioHome.create(
        cnpj="11222333000181",
        razao_social="Destinatario RJ Ltda",
        ie="111222333",
        uf="RJ",
        cidade="Rio de Janeiro",
        logradouro="Rua Primeiro de Março",
        numero="20",
        bairro="Centro",
        cep="20010000",
    )


def _make_destinatario_pf():
    return DestinatarioHome.create(
        cpf="12345678909",
        razao_social="Maria da Silva",
        uf="MG",
        cidade="Belo Horizonte",
        logradouro="Rua da Bahia",
        numero="50",
        bairro="Savassi",
        cep="30160011",
    )


def _build_xml(payload=None, remetente=None, destinatario=None):
    """Helper to build XML with default fixtures."""
    payload = payload or VALID_PAYLOAD
    fo = FreightOrder.from_dict(payload)
    key = AccessKey.generate(
        uf="26", aamm="2604", cnpj=fo.carrier, serie="020", numero=1, codigo="00000001"
    )
    transportadora = _make_transportadora()
    return build_cte_xml(fo, key, datetime.now(timezone.utc), transportadora, remetente, destinatario)


def _parse_inf_cte(xml_str: str) -> ET.Element:
    """Parse XML and return infCte element."""
    root = ET.fromstring(xml_str.replace('<?xml version="1.0" encoding="UTF-8"?>', ""))
    inf_cte = root.find(f".//{{{NS}}}infCte")
    if inf_cte is None:
        inf_cte = root.find(".//infCte")
    return inf_cte


# ─── AC1: Dest section ──────────────────────────────────────────


class TestXmlDestSection:
    """XML <dest> section from Destinatario entity."""

    def test_dest_section_contains_cnpj_and_address(self):
        dest_entity = _make_destinatario_pj()
        xml = _build_xml(destinatario=dest_entity)
        inf_cte = _parse_inf_cte(xml)
        dest = _find(inf_cte, "dest")
        assert dest is not None
        assert _find(dest, "CNPJ").text == "11222333000181"
        assert _find(dest, "xNome").text == "Destinatario RJ Ltda"
        assert _find(dest, "IE").text == "111222333"
        ender = _find(dest, "enderDest")
        assert ender is not None
        assert _find(ender, "xLgr").text == "Rua Primeiro de Março"
        assert _find(ender, "nro").text == "20"
        assert _find(ender, "xBairro").text == "Centro"
        assert _find(ender, "xMun").text == "Rio de Janeiro"
        assert _find(ender, "UF").text == "RJ"
        assert _find(ender, "CEP").text == "20010000"

    def test_dest_section_uses_cpf_when_no_cnpj(self):
        dest_entity = _make_destinatario_pf()
        xml = _build_xml(destinatario=dest_entity)
        inf_cte = _parse_inf_cte(xml)
        dest = _find(inf_cte, "dest")
        assert dest is not None
        assert _find(dest, "CNPJ") is None
        assert _find(dest, "CPF").text == "12345678909"
        assert _find(dest, "xNome").text == "Maria da Silva"

    def test_dest_section_omitted_when_no_destinatario(self):
        xml = _build_xml(destinatario=None)
        inf_cte = _parse_inf_cte(xml)
        dest = _find(inf_cte, "dest")
        assert dest is None


# ─── AC1 bonus: Rem enrichment ──────────────────────────────────


class TestXmlRemEnrichment:
    """XML <rem> section enriched with Remetente entity data."""

    def test_rem_enriched_with_remetente_entity(self):
        rem_entity = _make_remetente()
        xml = _build_xml(remetente=rem_entity)
        inf_cte = _parse_inf_cte(xml)
        rem = _find(inf_cte, "rem")
        assert _find(rem, "CNPJ").text == "10758386000159"
        assert _find(rem, "xNome").text == "Remetente SP Ltda"
        assert _find(rem, "IE").text == "123456789"
        ender = _find(rem, "enderRem")
        assert ender is not None
        assert _find(ender, "xLgr").text == "Av Paulista"
        assert _find(ender, "UF").text == "SP"

    def test_rem_fallback_cnpj_only_when_no_remetente(self):
        xml = _build_xml(remetente=None)
        inf_cte = _parse_inf_cte(xml)
        rem = _find(inf_cte, "rem")
        assert _find(rem, "CNPJ").text == "10758386000159"
        assert _find(rem, "xNome") is None


# ─── AC1 preserved: Emit section ────────────────────────────────


class TestXmlEmitEnrichment:
    """XML <emit> section must contain full Transportadora data."""

    def test_emit_contains_cnpj(self):
        xml = _build_xml()
        inf_cte = _parse_inf_cte(xml)
        emit = _find(inf_cte, "emit")
        assert _find(emit, "CNPJ").text == "10758386000159"

    def test_emit_contains_xnome(self):
        xml = _build_xml()
        inf_cte = _parse_inf_cte(xml)
        emit = _find(inf_cte, "emit")
        assert _find(emit, "xNome").text == "Transportes PE Ltda"

    def test_emit_contains_ie(self):
        xml = _build_xml()
        inf_cte = _parse_inf_cte(xml)
        emit = _find(inf_cte, "emit")
        assert _find(emit, "IE").text == "987654321"

    def test_emit_contains_ender_emit_with_all_fields(self):
        xml = _build_xml()
        inf_cte = _parse_inf_cte(xml)
        emit = _find(inf_cte, "emit")
        ender = _find(emit, "enderEmit")
        assert ender is not None
        assert _find(ender, "xLgr").text == "Rua da Aurora"
        assert _find(ender, "nro").text == "100"
        assert _find(ender, "xBairro").text == "Boa Vista"
        assert _find(ender, "xMun").text == "Recife"
        assert _find(ender, "UF").text == "PE"
        assert _find(ender, "CEP").text == "50060010"


# ─── AC2: Compl section ─────────────────────────────────────────


class TestXmlComplSection:
    """XML <compl> section."""

    def test_compl_section_present(self):
        xml = _build_xml()
        inf_cte = _parse_inf_cte(xml)
        compl = _find(inf_cte, "compl")
        assert compl is not None
        x_obs = _find(compl, "xObs")
        assert x_obs is not None
        assert x_obs.text is not None and len(x_obs.text) > 0


# ─── AC3: Correct tax tags ──────────────────────────────────────


def _make_payload_with_taxes(*taxes):
    """Build payload with specific taxes in a single folder."""
    payload = dict(VALID_PAYLOAD)
    folder = dict(VALID_PAYLOAD["Folder"][0])
    folder["Tax"] = list(taxes)
    payload["Folder"] = [folder]
    return payload


class TestXmlTaxTags:
    """XML <imp> section with correct per-tax-type tags."""

    def test_icms_tax_uses_correct_structure(self):
        payload = _make_payload_with_taxes(
            {"TaxType": "ICMS", "Base": 1500.00, "Rate": 12.00, "Value": 180.00, "TaxCode": "00", "ReducedBase": 0}
        )
        xml = _build_xml(payload=payload)
        inf_cte = _parse_inf_cte(xml)
        imp = _find(inf_cte, "imp")
        icms = _find(imp, "ICMS")
        assert icms is not None
        icms00 = _find(icms, "ICMS00")
        assert icms00 is not None
        assert _find(icms00, "CST").text == "00"
        assert _find(icms00, "vBC").text == "1500.00"
        assert _find(icms00, "pICMS").text == "12.00"
        assert _find(icms00, "vICMS").text == "180.00"

    def test_cofins_tax_uses_pcofins_vcofins(self):
        payload = _make_payload_with_taxes(
            {"TaxType": "ICMS", "Base": 1000.00, "Rate": 12.00, "Value": 120.00, "TaxCode": "00", "ReducedBase": 0},
            {"TaxType": "COFINS", "Base": 1500.00, "Rate": 3.00, "Value": 45.00, "TaxCode": "01", "ReducedBase": 0}
        )
        xml = _build_xml(payload=payload)
        inf_cte = _parse_inf_cte(xml)
        imp = _find(inf_cte, "imp")
        cofins = _find(imp, "COFINS")
        assert cofins is not None
        assert _find(cofins, "vBC").text == "1500.00"
        assert _find(cofins, "pCOFINS").text == "3.00"
        assert _find(cofins, "vCOFINS").text == "45.00"

    def test_pis_tax_uses_ppis_vpis(self):
        payload = _make_payload_with_taxes(
            {"TaxType": "ICMS", "Base": 1000.00, "Rate": 12.00, "Value": 120.00, "TaxCode": "00", "ReducedBase": 0},
            {"TaxType": "PIS", "Base": 1500.00, "Rate": 0.65, "Value": 9.75, "TaxCode": "01", "ReducedBase": 0}
        )
        xml = _build_xml(payload=payload)
        inf_cte = _parse_inf_cte(xml)
        imp = _find(inf_cte, "imp")
        pis = _find(imp, "PIS")
        assert pis is not None
        assert _find(pis, "vBC").text == "1500.00"
        assert _find(pis, "pPIS").text == "0.65"
        assert _find(pis, "vPIS").text == "9.75"

    def test_reduced_base_included_when_nonzero(self):
        payload = _make_payload_with_taxes(
            {"TaxType": "ICMS", "Base": 1500.00, "Rate": 12.00, "Value": 180.00, "TaxCode": "20", "ReducedBase": 750.00}
        )
        xml = _build_xml(payload=payload)
        inf_cte = _parse_inf_cte(xml)
        imp = _find(inf_cte, "imp")
        icms = _find(imp, "ICMS")
        icms20 = _find(icms, "ICMS20")
        assert _find(icms20, "vBCRed") is not None
        assert _find(icms20, "vBCRed").text == "750.00"

    def test_reduced_base_omitted_when_zero(self):
        payload = _make_payload_with_taxes(
            {"TaxType": "ICMS", "Base": 1500.00, "Rate": 12.00, "Value": 180.00, "TaxCode": "00", "ReducedBase": 0}
        )
        xml = _build_xml(payload=payload)
        inf_cte = _parse_inf_cte(xml)
        imp = _find(inf_cte, "imp")
        icms = _find(imp, "ICMS")
        icms00 = _find(icms, "ICMS00")
        assert _find(icms00, "vBCRed") is None

    def test_vtottrib_aggregates_all_taxes(self):
        payload = _make_payload_with_taxes(
            {"TaxType": "ICMS", "Base": 1500.00, "Rate": 12.00, "Value": 180.00, "TaxCode": "00", "ReducedBase": 0},
            {"TaxType": "COFINS", "Base": 1500.00, "Rate": 3.00, "Value": 45.00, "TaxCode": "01", "ReducedBase": 0},
            {"TaxType": "PIS", "Base": 1500.00, "Rate": 0.65, "Value": 9.75, "TaxCode": "01", "ReducedBase": 0}
        )
        xml = _build_xml(payload=payload)
        inf_cte = _parse_inf_cte(xml)
        imp = _find(inf_cte, "imp")
        v_tot_trib = _find(imp, "vTotTrib")
        assert v_tot_trib is not None
        assert v_tot_trib.text == "234.75"


# ─── AC4: Trailer plates ────────────────────────────────────────


class TestXmlTrailerPlates:
    """XML <rodo> trailer plates as <veicReboque>."""

    def test_trailer_plates_in_rodo(self):
        payload = dict(VALID_PAYLOAD)
        folder = dict(VALID_PAYLOAD["Folder"][0])
        folder["TrailerPlate"] = ["XYZ9876"]
        payload["Folder"] = [folder]
        xml = _build_xml(payload=payload)
        inf_cte = _parse_inf_cte(xml)
        rodo = inf_cte.find(f".//{{{NS}}}rodo")
        if rodo is None:
            rodo = inf_cte.find(".//rodo")
        reboque_list = _find_all(rodo, "veicReboque")
        assert len(reboque_list) == 1
        assert _find(reboque_list[0], "placa").text == "XYZ9876"

    def test_empty_trailer_plates_skipped(self):
        payload = dict(VALID_PAYLOAD)
        folder = dict(VALID_PAYLOAD["Folder"][0])
        folder["TrailerPlate"] = ["", "  "]
        payload["Folder"] = [folder]
        xml = _build_xml(payload=payload)
        inf_cte = _parse_inf_cte(xml)
        rodo = inf_cte.find(f".//{{{NS}}}rodo")
        if rodo is None:
            rodo = inf_cte.find(".//rodo")
        reboque_list = _find_all(rodo, "veicReboque")
        assert len(reboque_list) == 0

    def test_multiple_trailer_plates(self):
        payload = dict(VALID_PAYLOAD)
        folder = dict(VALID_PAYLOAD["Folder"][0])
        folder["TrailerPlate"] = ["ABC1234", "DEF5678"]
        payload["Folder"] = [folder]
        xml = _build_xml(payload=payload)
        inf_cte = _parse_inf_cte(xml)
        rodo = inf_cte.find(f".//{{{NS}}}rodo")
        if rodo is None:
            rodo = inf_cte.find(".//rodo")
        reboque_list = _find_all(rodo, "veicReboque")
        assert len(reboque_list) == 2
        assert _find(reboque_list[0], "placa").text == "ABC1234"
        assert _find(reboque_list[1], "placa").text == "DEF5678"
