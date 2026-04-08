"""Tests for CT-e XML builder — emit section enrichment with Transportadora data."""

import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from src.domain.cte.value_objects import AccessKey, FreightOrder
from src.domain.cte.xml_builder import build_cte_xml
from src.domain.transportadora.home import TransportadoraHome


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


class TestXmlEmitEnrichment:
    """XML <emit> section must contain full Transportadora data."""

    def _parse_emit(self, xml_str: str) -> ET.Element:
        ns = {"ns": "http://www.portalfiscal.inf.br/cte"}
        root = ET.fromstring(xml_str.replace('<?xml version="1.0" encoding="UTF-8"?>', ""))
        emit = root.find(".//{http://www.portalfiscal.inf.br/cte}emit")
        if emit is None:
            emit = root.find(".//emit")
        return emit

    def _find(self, parent: ET.Element, tag: str) -> ET.Element:
        """Find child element handling namespace."""
        elem = parent.find(f"{{http://www.portalfiscal.inf.br/cte}}{tag}")
        if elem is None:
            elem = parent.find(tag)
        return elem

    def test_emit_contains_cnpj(self):
        fo = FreightOrder.from_dict(VALID_PAYLOAD)
        key = AccessKey.generate(uf="26", aamm="2604", cnpj=fo.carrier, serie="020", numero=1, codigo="00000001")
        transportadora = _make_transportadora()
        xml = build_cte_xml(fo, key, datetime.now(timezone.utc), transportadora)
        emit = self._parse_emit(xml)
        assert self._find(emit, "CNPJ").text == "10758386000159"

    def test_emit_contains_xnome(self):
        fo = FreightOrder.from_dict(VALID_PAYLOAD)
        key = AccessKey.generate(uf="26", aamm="2604", cnpj=fo.carrier, serie="020", numero=2, codigo="00000002")
        transportadora = _make_transportadora()
        xml = build_cte_xml(fo, key, datetime.now(timezone.utc), transportadora)
        emit = self._parse_emit(xml)
        assert self._find(emit, "xNome").text == "Transportes PE Ltda"

    def test_emit_contains_ie(self):
        fo = FreightOrder.from_dict(VALID_PAYLOAD)
        key = AccessKey.generate(uf="26", aamm="2604", cnpj=fo.carrier, serie="020", numero=3, codigo="00000003")
        transportadora = _make_transportadora()
        xml = build_cte_xml(fo, key, datetime.now(timezone.utc), transportadora)
        emit = self._parse_emit(xml)
        assert self._find(emit, "IE").text == "987654321"

    def test_emit_contains_ender_emit_with_all_fields(self):
        fo = FreightOrder.from_dict(VALID_PAYLOAD)
        key = AccessKey.generate(uf="26", aamm="2604", cnpj=fo.carrier, serie="020", numero=4, codigo="00000004")
        transportadora = _make_transportadora()
        xml = build_cte_xml(fo, key, datetime.now(timezone.utc), transportadora)
        emit = self._parse_emit(xml)
        ender = self._find(emit, "enderEmit")
        assert ender is not None
        assert self._find(ender, "xLgr").text == "Rua da Aurora"
        assert self._find(ender, "nro").text == "100"
        assert self._find(ender, "xBairro").text == "Boa Vista"
        assert self._find(ender, "xMun").text == "Recife"
        assert self._find(ender, "UF").text == "PE"
        assert self._find(ender, "CEP").text == "50060010"
