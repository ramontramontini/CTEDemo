"""Cte value objects — immutable domain concepts."""

from dataclasses import dataclass, field
from typing import Any

from src.domain.shared.cnpj import Cnpj
from src.domain.shared.cpf import Cpf
from src.domain.shared.vehicle_plate import VehiclePlate

VALID_CFOPS = {"5352", "5353", "6352", "6353", "7352"}


@dataclass(frozen=True)
class CteId:
    """Strongly-typed identifier for Cte."""
    value: str

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class AccessKey:
    """44-digit CT-e access key with mod11 DV."""

    value: str

    @classmethod
    def generate(
        cls,
        uf: str,
        aamm: str,
        cnpj: str,
        serie: str,
        numero: int,
        codigo: str,
    ) -> "AccessKey":
        mod = "57"
        tipo = "1"
        numero_str = str(numero).zfill(9)

        base = f"{uf}{aamm}{cnpj}{mod}{serie}{numero_str}{tipo}{codigo}"
        dv = cls._calc_dv(base)
        return cls(value=f"{base}{dv}")

    @staticmethod
    def _calc_dv(digits_43: str) -> int:
        weights = [2, 3, 4, 5, 6, 7, 8, 9]
        total = 0
        for i, digit in enumerate(reversed(digits_43)):
            total += int(digit) * weights[i % len(weights)]
        remainder = total % 11
        if remainder < 2:
            return 0
        return 11 - remainder

    def formatted(self) -> str:
        v = self.value
        return (
            f"{v[0:2]} {v[2:6]} {v[6:20]} {v[20:22]} "
            f"{v[22:25]} {v[25:34]} {v[34:35]} {v[35:43]} {v[43:44]}"
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class FreightOrderTax:
    """Tax entry within a freight order folder."""

    tax_type: str
    base: float
    rate: float
    value: float
    tax_code: str
    reduced_base: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FreightOrderTax":
        tax_type = data.get("TaxType", "")
        if not tax_type:
            raise ValueError("TaxType é obrigatório")
        base = round(float(data.get("Base", 0)), 2)
        rate = round(float(data.get("Rate", 0)), 4)
        value = round(float(data.get("Value", 0)), 2)
        reduced_base = round(float(data.get("ReducedBase", 0)), 2)

        if base > 0 and rate > 0:
            expected = round(base * rate / 100, 2)
            if abs(expected - value) > 0.01:
                raise ValueError(
                    f"Valor do imposto não confere: base={base}, "
                    f"alíquota={rate}, valor esperado={expected}, "
                    f"valor informado={value}"
                )

        return cls(
            tax_type=tax_type,
            base=base,
            rate=rate,
            value=value,
            tax_code=str(data.get("TaxCode", "")),
            reduced_base=reduced_base,
        )


@dataclass(frozen=True)
class FreightOrderFolder:
    """Folder (shipment) within a freight order."""

    folder_number: str
    reference_number: str
    net_value: float
    vehicle_plate: str
    trailer_plates: tuple[str, ...]
    vehicle_axles: str
    equipment_type: str
    weight: float
    cfop: str
    driver_id: str
    cancel: bool
    taxes: tuple[FreightOrderTax, ...]
    related_nfe: tuple[str, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any], index: int) -> "FreightOrderFolder":
        errors: list[str] = []
        prefix = f"Folder[{index}]"

        folder_number = data.get("FolderNumber", "")
        if not folder_number:
            errors.append(f"{prefix}.FolderNumber é obrigatório")

        reference_number = data.get("ReferenceNumber", "")
        if not reference_number:
            errors.append(f"{prefix}.ReferenceNumber é obrigatório")

        net_value = round(float(data.get("NetValue", 0)), 2)
        if net_value <= 0:
            errors.append(f"{prefix}.NetValue deve ser maior que zero")

        plate_raw = data.get("VehiclePlate", "")
        try:
            plate = VehiclePlate(plate_raw)
            plate_value = plate.value
        except ValueError:
            errors.append(
                f"{prefix}.VehiclePlate — Placa inválida — formato aceito: ABC1234 ou ABC1D23"
            )
            plate_value = plate_raw

        cfop = data.get("CFOP", "")
        if cfop not in VALID_CFOPS:
            errors.append(
                f"{prefix}.CFOP inválido — valores aceitos: 5352, 5353, 6352, 6353, 7352"
            )

        driver_id = data.get("DriverID", "")
        try:
            Cpf(driver_id)
        except ValueError as e:
            errors.append(f"{prefix}.DriverID — {e}")

        tax_list = data.get("Tax", [])
        if not tax_list:
            errors.append(f"{prefix}.Tax é obrigatório em cada Folder")

        related_nfe = data.get("RelatedNFE", [])
        if not related_nfe:
            errors.append(f"{prefix}.RelatedNFE é obrigatório em cada Folder")

        if errors:
            raise ValueError("\n".join(errors))

        taxes = tuple(FreightOrderTax.from_dict(t) for t in tax_list)
        trailer_plates = tuple(data.get("TrailerPlate", []))

        return cls(
            folder_number=folder_number,
            reference_number=reference_number,
            net_value=net_value,
            vehicle_plate=plate_value,
            trailer_plates=trailer_plates,
            vehicle_axles=str(data.get("VehicleAxles", "")),
            equipment_type=str(data.get("EquipmentType", "")),
            weight=float(data.get("Weight", 0)),
            cfop=cfop,
            driver_id=driver_id,
            cancel=bool(data.get("Cancel", False)),
            taxes=taxes,
            related_nfe=tuple(related_nfe),
        )


@dataclass(frozen=True)
class FreightOrder:
    """Parsed and validated freight order input."""

    freight_order: str
    erp: str
    carrier: str
    cnpj_origin: str
    incoterms: str
    operation_type: str
    folders: tuple[FreightOrderFolder, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FreightOrder":
        errors: list[str] = []

        freight_order = data.get("FreightOrder", "")
        if not freight_order:
            errors.append("FreightOrder é obrigatório")

        carrier = data.get("Carrier")
        if not carrier:
            errors.append("Carrier é obrigatório")
        else:
            try:
                Cnpj(carrier)
            except ValueError as e:
                errors.append(f"Carrier — CNPJ inválido: {e}")

        cnpj_origin = data.get("CNPJ_Origin", "")
        if cnpj_origin:
            try:
                Cnpj(cnpj_origin)
            except ValueError as e:
                errors.append(f"CNPJ_Origin — CNPJ inválido: {e}")

        folder_list = data.get("Folder")
        if not folder_list:
            errors.append("Folder é obrigatório e não pode ser vazio")

        if errors:
            raise ValueError("\n".join(errors))

        folders: list[FreightOrderFolder] = []
        for i, folder_data in enumerate(folder_list):
            folders.append(FreightOrderFolder.from_dict(folder_data, index=i))

        return cls(
            freight_order=freight_order,
            erp=str(data.get("ERP", "")),
            carrier=carrier,
            cnpj_origin=cnpj_origin,
            incoterms=str(data.get("Incoterms", "")),
            operation_type=str(data.get("OperationType", "")),
            folders=tuple(folders),
        )
