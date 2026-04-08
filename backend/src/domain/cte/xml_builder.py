"""CT-e XML v4.00 builder."""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional

from src.domain.cte.value_objects import AccessKey, FreightOrder, FreightOrderTax
from src.domain.destinatario.entity import Destinatario
from src.domain.remetente.entity import Remetente
from src.domain.transportadora.entity import Transportadora


def build_cte_xml(
    fo: FreightOrder,
    key: AccessKey,
    timestamp: datetime,
    transportadora: Transportadora,
    remetente: Optional[Remetente] = None,
    destinatario: Optional[Destinatario] = None,
) -> str:
    """Build CT-e XML v4.00 structure."""
    cte_proc = ET.Element("cteProc", xmlns="http://www.portalfiscal.inf.br/cte", versao="4.00")
    cte = ET.SubElement(cte_proc, "CTe")
    inf_cte = ET.SubElement(cte, "infCte", versao="4.00", Id=f"CTe{key.value}")

    _build_identification(inf_cte, fo, key, timestamp)
    _build_complemento(inf_cte, fo)
    _build_parties(inf_cte, fo, transportadora, remetente)
    if destinatario is not None:
        _build_destinatario(inf_cte, destinatario)
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


def _build_complemento(parent: ET.Element, fo: FreightOrder) -> None:
    compl = ET.SubElement(parent, "compl")
    obs_text = fo.operation_type if fo.operation_type else "Prestação de serviço de transporte"
    ET.SubElement(compl, "xObs").text = obs_text


def _build_address(parent: ET.Element, tag: str, entity: object) -> None:
    """Build address sub-element from any entity with address properties."""
    ender = ET.SubElement(parent, tag)
    ET.SubElement(ender, "xLgr").text = entity.logradouro
    ET.SubElement(ender, "nro").text = entity.numero
    ET.SubElement(ender, "xBairro").text = entity.bairro
    ET.SubElement(ender, "xMun").text = entity.cidade
    ET.SubElement(ender, "UF").text = entity.uf
    ET.SubElement(ender, "CEP").text = entity.cep


def _build_parties(
    parent: ET.Element,
    fo: FreightOrder,
    transportadora: Transportadora,
    remetente: Optional[Remetente] = None,
) -> None:
    # <emit> from Transportadora
    emit = ET.SubElement(parent, "emit")
    ET.SubElement(emit, "CNPJ").text = fo.carrier
    ET.SubElement(emit, "IE").text = transportadora.ie
    ET.SubElement(emit, "xNome").text = transportadora.razao_social
    _build_address(emit, "enderEmit", transportadora)

    # <rem> from Remetente entity or CNPJ fallback
    rem = ET.SubElement(parent, "rem")
    ET.SubElement(rem, "CNPJ").text = fo.cnpj_origin
    if remetente is not None:
        ET.SubElement(rem, "xNome").text = remetente.razao_social
        ET.SubElement(rem, "IE").text = remetente.ie
        _build_address(rem, "enderRem", remetente)


def _build_destinatario(parent: ET.Element, destinatario: Destinatario) -> None:
    dest = ET.SubElement(parent, "dest")
    if destinatario.cnpj:
        ET.SubElement(dest, "CNPJ").text = destinatario.cnpj
    elif destinatario.cpf:
        ET.SubElement(dest, "CPF").text = destinatario.cpf
    ET.SubElement(dest, "xNome").text = destinatario.razao_social
    if destinatario.ie:
        ET.SubElement(dest, "IE").text = destinatario.ie
    _build_address(dest, "enderDest", destinatario)


def _build_values(parent: ET.Element, fo: FreightOrder) -> None:
    v_prest = ET.SubElement(parent, "vPrest")
    total_value = sum(f.net_value for f in fo.folders)
    ET.SubElement(v_prest, "vTPrest").text = f"{total_value:.2f}"
    ET.SubElement(v_prest, "vRec").text = f"{total_value:.2f}"


def _build_taxes(parent: ET.Element, fo: FreightOrder) -> None:
    imp = ET.SubElement(parent, "imp")
    total_tax = 0.0

    for folder in fo.folders:
        for tax in folder.taxes:
            total_tax += tax.value
            _build_single_tax(imp, tax)

    ET.SubElement(imp, "vTotTrib").text = f"{total_tax:.2f}"


def _build_single_tax(imp: ET.Element, tax: FreightOrderTax) -> None:
    tax_type_upper = tax.tax_type.upper()

    if tax_type_upper == "ICMS":
        _build_icms_tax(imp, tax)
    elif tax_type_upper == "COFINS":
        _build_cofins_tax(imp, tax)
    elif tax_type_upper == "PIS":
        _build_pis_tax(imp, tax)
    else:
        _build_generic_tax(imp, tax)


def _build_icms_tax(imp: ET.Element, tax: FreightOrderTax) -> None:
    icms = ET.SubElement(imp, "ICMS")
    cst_code = tax.tax_code if tax.tax_code else "00"
    inner = ET.SubElement(icms, f"ICMS{cst_code}")
    ET.SubElement(inner, "CST").text = cst_code
    ET.SubElement(inner, "vBC").text = f"{tax.base:.2f}"
    ET.SubElement(inner, "pICMS").text = f"{tax.rate:.2f}"
    ET.SubElement(inner, "vICMS").text = f"{tax.value:.2f}"
    if tax.reduced_base > 0:
        ET.SubElement(inner, "vBCRed").text = f"{tax.reduced_base:.2f}"


def _build_cofins_tax(imp: ET.Element, tax: FreightOrderTax) -> None:
    cofins = ET.SubElement(imp, "COFINS")
    ET.SubElement(cofins, "vBC").text = f"{tax.base:.2f}"
    ET.SubElement(cofins, "pCOFINS").text = f"{tax.rate:.2f}"
    ET.SubElement(cofins, "vCOFINS").text = f"{tax.value:.2f}"


def _build_pis_tax(imp: ET.Element, tax: FreightOrderTax) -> None:
    pis = ET.SubElement(imp, "PIS")
    ET.SubElement(pis, "vBC").text = f"{tax.base:.2f}"
    ET.SubElement(pis, "pPIS").text = f"{tax.rate:.2f}"
    ET.SubElement(pis, "vPIS").text = f"{tax.value:.2f}"


def _build_generic_tax(imp: ET.Element, tax: FreightOrderTax) -> None:
    tax_elem = ET.SubElement(imp, tax.tax_type)
    ET.SubElement(tax_elem, "vBC").text = f"{tax.base:.2f}"
    ET.SubElement(tax_elem, "pRate").text = f"{tax.rate:.2f}"
    ET.SubElement(tax_elem, "vValue").text = f"{tax.value:.2f}"


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
        for trailer_plate in folder.trailer_plates:
            if trailer_plate and trailer_plate.strip():
                reboque = ET.SubElement(rodo, "veicReboque")
                ET.SubElement(reboque, "placa").text = trailer_plate.strip()
