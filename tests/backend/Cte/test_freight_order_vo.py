"""Tests for FreightOrder value object — parsed input with validation."""

import pytest

from src.domain.cte.value_objects import FreightOrder, FreightOrderFolder, FreightOrderTax


VALID_FOLDER = {
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

VALID_PAYLOAD = {
    "FreightOrder": "12345678901234",
    "ERP": "SAP",
    "Carrier": "10758386000159",
    "CNPJ_Origin": "10758386000159",
    "Incoterms": "CIF",
    "OperationType": "0",
    "Folder": [VALID_FOLDER],
}


class TestFreightOrder:
    """FreightOrder VO tests."""

    def test_valid_payload_accepted(self):
        fo = FreightOrder.from_dict(VALID_PAYLOAD)
        assert fo.freight_order == "12345678901234"
        assert fo.carrier == "10758386000159"
        assert len(fo.folders) == 1

    def test_missing_freight_order_rejected(self):
        payload = {**VALID_PAYLOAD, "FreightOrder": ""}
        with pytest.raises(ValueError, match="FreightOrder"):
            FreightOrder.from_dict(payload)

    def test_missing_carrier_rejected(self):
        payload = {**VALID_PAYLOAD}
        del payload["Carrier"]
        with pytest.raises(ValueError, match="Carrier"):
            FreightOrder.from_dict(payload)

    def test_invalid_carrier_cnpj_rejected(self):
        payload = {**VALID_PAYLOAD, "Carrier": "11111111111111"}
        with pytest.raises(ValueError, match="Carrier.*CNPJ"):
            FreightOrder.from_dict(payload)

    def test_invalid_origin_cnpj_rejected(self):
        payload = {**VALID_PAYLOAD, "CNPJ_Origin": "99999999999999"}
        with pytest.raises(ValueError, match="CNPJ_Origin.*CNPJ"):
            FreightOrder.from_dict(payload)

    def test_empty_folder_array_rejected(self):
        payload = {**VALID_PAYLOAD, "Folder": []}
        with pytest.raises(ValueError, match="Folder"):
            FreightOrder.from_dict(payload)

    def test_missing_folder_rejected(self):
        payload = {**VALID_PAYLOAD}
        del payload["Folder"]
        with pytest.raises(ValueError, match="Folder"):
            FreightOrder.from_dict(payload)


class TestFreightOrderFolder:
    """FreightOrderFolder VO tests."""

    def test_valid_folder_accepted(self):
        folder = FreightOrderFolder.from_dict(VALID_FOLDER, index=0)
        assert folder.folder_number == "001"
        assert folder.net_value == 1500.00

    def test_missing_folder_number_rejected(self):
        data = {**VALID_FOLDER, "FolderNumber": ""}
        with pytest.raises(ValueError, match="FolderNumber"):
            FreightOrderFolder.from_dict(data, index=0)

    def test_invalid_vehicle_plate_rejected(self):
        data = {**VALID_FOLDER, "VehiclePlate": "INVALID"}
        with pytest.raises(ValueError, match="VehiclePlate"):
            FreightOrderFolder.from_dict(data, index=0)

    def test_invalid_cfop_rejected(self):
        data = {**VALID_FOLDER, "CFOP": "1234"}
        with pytest.raises(ValueError, match="CFOP"):
            FreightOrderFolder.from_dict(data, index=0)

    def test_valid_cfops_accepted(self):
        for cfop in ["5352", "5353", "6352", "6353", "7352"]:
            data = {**VALID_FOLDER, "CFOP": cfop}
            folder = FreightOrderFolder.from_dict(data, index=0)
            assert folder.cfop == cfop

    def test_invalid_driver_cpf_rejected(self):
        data = {**VALID_FOLDER, "DriverID": "11111111111"}
        with pytest.raises(ValueError, match="DriverID"):
            FreightOrderFolder.from_dict(data, index=0)

    def test_net_value_zero_rejected(self):
        data = {**VALID_FOLDER, "NetValue": 0}
        with pytest.raises(ValueError, match="NetValue"):
            FreightOrderFolder.from_dict(data, index=0)

    def test_net_value_negative_rejected(self):
        data = {**VALID_FOLDER, "NetValue": -100}
        with pytest.raises(ValueError, match="NetValue"):
            FreightOrderFolder.from_dict(data, index=0)

    def test_empty_tax_rejected(self):
        data = {**VALID_FOLDER, "Tax": []}
        with pytest.raises(ValueError, match="Tax"):
            FreightOrderFolder.from_dict(data, index=0)

    def test_empty_related_nfe_rejected(self):
        data = {**VALID_FOLDER, "RelatedNFE": []}
        with pytest.raises(ValueError, match="RelatedNFE"):
            FreightOrderFolder.from_dict(data, index=0)

    def test_error_includes_folder_index(self):
        data = {**VALID_FOLDER, "NetValue": -1}
        with pytest.raises(ValueError, match=r"Folder\[2\]"):
            FreightOrderFolder.from_dict(data, index=2)

    def test_net_value_rounded_to_2dp(self):
        data = {**VALID_FOLDER, "NetValue": 1500.1234}
        folder = FreightOrderFolder.from_dict(data, index=0)
        assert folder.net_value == 1500.12

    def test_string_net_value_parsed_and_rounded(self):
        data = {**VALID_FOLDER, "NetValue": "1702.4000"}
        folder = FreightOrderFolder.from_dict(data, index=0)
        assert folder.net_value == 1702.40


class TestFreightOrderTax:
    """FreightOrderTax VO tests."""

    def test_valid_tax_accepted(self):
        tax = FreightOrderTax.from_dict(VALID_FOLDER["Tax"][0])
        assert tax.tax_type == "ICMS"
        assert tax.rate == 12.00

    def test_missing_tax_type_rejected(self):
        data = {**VALID_FOLDER["Tax"][0], "TaxType": ""}
        with pytest.raises(ValueError, match="TaxType"):
            FreightOrderTax.from_dict(data)

    def test_tax_base_rounded_to_2dp(self):
        data = {**VALID_FOLDER["Tax"][0], "Base": 100.1234, "Value": 12.01}
        tax = FreightOrderTax.from_dict(data)
        assert tax.base == 100.12

    def test_tax_value_rounded_to_2dp(self):
        data = {**VALID_FOLDER["Tax"][0], "Value": 180.1234, "Base": 1501.03, "Rate": 12.00}
        tax = FreightOrderTax.from_dict(data)
        assert tax.value == 180.12

    def test_tax_rate_rounded_to_4dp(self):
        data = {**VALID_FOLDER["Tax"][0], "Rate": 12.12345, "Base": 1500.00, "Value": 181.85}
        tax = FreightOrderTax.from_dict(data)
        assert tax.rate == 12.1235

    def test_string_tax_base_parsed(self):
        data = {**VALID_FOLDER["Tax"][0], "Base": "1500.0000"}
        tax = FreightOrderTax.from_dict(data)
        assert tax.base == 1500.00

    def test_tax_value_mismatch_rejected(self):
        data = {**VALID_FOLDER["Tax"][0], "Base": 100, "Rate": 12, "Value": 15}
        with pytest.raises(ValueError, match="imposto não confere"):
            FreightOrderTax.from_dict(data)

    def test_tax_value_within_tolerance_accepted(self):
        data = {**VALID_FOLDER["Tax"][0], "Base": 100, "Rate": 12.5, "Value": 12.50}
        tax = FreightOrderTax.from_dict(data)
        assert tax.value == 12.50

    def test_tax_zero_exempt_accepted(self):
        data = {**VALID_FOLDER["Tax"][0], "Base": 0, "Rate": 0, "Value": 0}
        tax = FreightOrderTax.from_dict(data)
        assert tax.base == 0
        assert tax.value == 0
