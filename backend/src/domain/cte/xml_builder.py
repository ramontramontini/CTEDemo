"""CT-e XML v4.00 builder."""

import xml.etree.ElementTree as ET
from datetime import datetime

from src.domain.cte.value_objects import AccessKey, FreightOrder


def build_cte_xml(fo: FreightOrder, key: AccessKey, timestamp: datetime) -> str:
    """Build simplified CT-e XML v4.00 structure."""
    cte_proc = ET.Element("cteProc", xmlns="http://www.portalfiscal.inf.br/cte", versao="4.00")
    cte = ET.SubElement(cte_proc, "CTe")
    inf_cte = ET.SubElement(cte, "infCte", versao="4.00", Id=f"CTe{key.value}")

    _build_identification(inf_cte, fo, key, timestamp)
    _build_parties(inf_cte, fo)
    _build_values(inf_cte, fo)
    _build_taxes(inf_cte, fo)
    _build_cargo_and_modal(inf_cte, fo)

    return '<?xml version="1.0" encoding="UTF-8"?>' + ET.tostring(cte_proc, encoding="unicode")


def _build_identification(
    parent: ET.Element, fo: FreightOrder, key: AccessKey, timestamp: datetime
) -> None:
    ide = ET.SubElement(parent, "ide")
    ET.SubElement(ide, "cUF").text = key.value[:2]
    ET.SubElement(ide, "cCT").text = key.value[35:43]
    ET.SubElement(ide, "CFOP").text = fo.folders[0].cfop
    ET.SubElement(ide, "natOp").text = "Prestação de serviço de transporte"
    ET.SubElement(ide, "mod").text = "57"
    ET.SubElement(ide, "serie").text = key.value[22:25]
    ET.SubElement(ide, "nCT").text = str(int(key.value[25:34]))
    ET.SubElement(ide, "dhEmi").text = timestamp.isoformat()
    ET.SubElement(ide, "tpCTe").text = "0"
    ET.SubElement(ide, "tpEmis").text = "1"
    ET.SubElement(ide, "cDV").text = key.value[43]
    ET.SubElement(ide, "tpAmb").text = "2"


def _build_parties(parent: ET.Element, fo: FreightOrder) -> None:
    emit = ET.SubElement(parent, "emit")
    ET.SubElement(emit, "CNPJ").text = fo.carrier
    rem = ET.SubElement(parent, "rem")
    ET.SubElement(rem, "CNPJ").text = fo.cnpj_origin


def _build_values(parent: ET.Element, fo: FreightOrder) -> None:
    v_prest = ET.SubElement(parent, "vPrest")
    total_value = sum(f.net_value for f in fo.folders)
    ET.SubElement(v_prest, "vTPrest").text = f"{total_value:.2f}"
    ET.SubElement(v_prest, "vRec").text = f"{total_value:.2f}"


def _build_taxes(parent: ET.Element, fo: FreightOrder) -> None:
    imp = ET.SubElement(parent, "imp")
    for folder in fo.folders:
        for tax in folder.taxes:
            tax_elem = ET.SubElement(imp, tax.tax_type)
            ET.SubElement(tax_elem, "vBC").text = f"{tax.base:.2f}"
            ET.SubElement(tax_elem, "pICMS").text = f"{tax.rate:.2f}"
            ET.SubElement(tax_elem, "vICMS").text = f"{tax.value:.2f}"


def _build_cargo_and_modal(parent: ET.Element, fo: FreightOrder) -> None:
    total_value = sum(f.net_value for f in fo.folders)
    total_weight = sum(f.weight for f in fo.folders)

    inf_carga = ET.SubElement(parent, "infCTeNorm")
    inf_cargo_inner = ET.SubElement(inf_carga, "infCarga")
    ET.SubElement(inf_cargo_inner, "vCarga").text = f"{total_value:.2f}"
    ET.SubElement(inf_cargo_inner, "proPred").text = "Mercadorias em geral"
    ET.SubElement(inf_cargo_inner, "qCarga").text = f"{total_weight:.4f}"

    inf_doc = ET.SubElement(inf_carga, "infDoc")
    for folder in fo.folders:
        for nfe in folder.related_nfe:
            inf_nfe = ET.SubElement(inf_doc, "infNFe")
            ET.SubElement(inf_nfe, "chave").text = nfe

    inf_modal = ET.SubElement(inf_carga, "infModal", versaoModal="4.00")
    rodo = ET.SubElement(inf_modal, "rodo")
    for folder in fo.folders:
        veic = ET.SubElement(rodo, "veicTracao")
        ET.SubElement(veic, "placa").text = folder.vehicle_plate
