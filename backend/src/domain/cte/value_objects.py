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
        dv = cls.calc_dv(base)
        return cls(value=f"{base}{dv}")

    @staticmethod
    def calc_dv(digits_43: str) -> int:
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
    def from_dict(cls, data: dict[str, Any], prefix: str = "") -> "FreightOrderTax":
        errors: list[str] = []
        tax_type = data.get("TaxType", "")
        if not tax_type:
            errors.append(f"{prefix}TaxType é obrigatório")

        base = cls._parse_float(data.get("Base", 0), f"{prefix}Base", 2, errors)
        rate = cls._parse_float(data.get("Rate", 0), f"{prefix}Rate", 4, errors)
        value = cls._parse_float(data.get("Value", 0), f"{prefix}Value", 2, errors)
        reduced_base = cls._parse_float(data.get("ReducedBase", 0), f"{prefix}ReducedBase", 2, errors)

        if base is not None and base < 0:
            errors.append(f"{prefix}Base deve ser maior ou igual a zero")
        if rate is not None and rate < 0:
            errors.append(f"{prefix}Rate deve ser maior ou igual a zero")
        if value is not None and value < 0:
            errors.append(f"{prefix}Value deve ser maior ou igual a zero")

        if errors:
            raise ValueError("\n".join(errors))

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

    @staticmethod
    def _parse_float(
        raw: Any, field_name: str, decimals: int, errors: list[str],
    ) -> float | None:
        try:
            return round(float(raw), decimals)
        except (ValueError, TypeError):
            errors.append(f"{field_name} deve ser numérico")
            return None


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

        folder_number, reference_number, net_value, plate_value = (
            cls._validate_header_fields(data, prefix, errors)
        )
        cfop, driver_id, vehicle_axles, equipment_type, weight = (
            cls._validate_transport_fields(data, prefix, errors)
        )
        tax_list, related_nfe = cls._validate_doc_fields(data, prefix, errors)
        validated_trailer_plates = cls._validate_trailer_plates(data, prefix, errors)

        if errors:
            raise ValueError("\n".join(errors))

        taxes: list[FreightOrderTax] = []
        for k, t in enumerate(tax_list):
            taxes.append(FreightOrderTax.from_dict(t, prefix=f"{prefix}.Tax[{k}]."))

        return cls(
            folder_number=folder_number,
            reference_number=reference_number,
            net_value=net_value,
            vehicle_plate=plate_value,
            trailer_plates=tuple(validated_trailer_plates),
            vehicle_axles=vehicle_axles,
            equipment_type=equipment_type,
            weight=weight,
            cfop=cfop,
            driver_id=driver_id,
            cancel=bool(data.get("Cancel", False)),
            taxes=tuple(taxes),
            related_nfe=tuple(related_nfe),
        )

    @staticmethod
    def _validate_header_fields(
        data: dict[str, Any], prefix: str, errors: list[str],
    ) -> tuple[str, str, float, str]:
        folder_number = data.get("FolderNumber", "")
        if not folder_number:
            errors.append(f"{prefix}.FolderNumber é obrigatório")

        reference_number = data.get("ReferenceNumber", "")
        if not reference_number:
            errors.append(f"{prefix}.ReferenceNumber é obrigatório")

        try:
            net_value = round(float(data.get("NetValue", 0)), 2)
        except (ValueError, TypeError):
            errors.append(f"{prefix}.NetValue deve ser numérico")
            net_value = 0
        if net_value <= 0 and f"{prefix}.NetValue deve ser numérico" not in errors:
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

        return folder_number, reference_number, net_value, plate_value

    @staticmethod
    def _validate_transport_fields(
        data: dict[str, Any], prefix: str, errors: list[str],
    ) -> tuple[str, str, str, str, float]:
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

        vehicle_axles = str(data.get("VehicleAxles", ""))
        if not vehicle_axles:
            errors.append(f"{prefix}.VehicleAxles é obrigatório")

        equipment_type = str(data.get("EquipmentType", ""))
        if not equipment_type:
            errors.append(f"{prefix}.EquipmentType é obrigatório")

        try:
            weight = float(data.get("Weight", 0))
        except (ValueError, TypeError):
            errors.append(f"{prefix}.Weight deve ser numérico")
            weight = 0
        if weight <= 0 and f"{prefix}.Weight deve ser numérico" not in errors:
            errors.append(f"{prefix}.Weight deve ser maior que zero")

        return cfop, driver_id, vehicle_axles, equipment_type, weight

    @staticmethod
    def _validate_doc_fields(
        data: dict[str, Any], prefix: str, errors: list[str],
    ) -> tuple[list, list]:
        tax_list = data.get("Tax", [])
        if not tax_list:
            errors.append(f"{prefix}.Tax é obrigatório em cada Folder")

        related_nfe = data.get("RelatedNFE", [])
        if not related_nfe:
            errors.append(f"{prefix}.RelatedNFE é obrigatório em cada Folder")
        else:
            for j, key in enumerate(related_nfe):
                if not isinstance(key, str) or len(key) != 44 or not key.isdigit():
                    errors.append(
                        f"{prefix}.RelatedNFE[{j}] deve ser chave de 44 dígitos numéricos"
                    )

        return tax_list, related_nfe

    @staticmethod
    def _validate_trailer_plates(
        data: dict[str, Any], prefix: str, errors: list[str],
    ) -> list[str]:
        raw_trailer_plates = data.get("TrailerPlate", [])
        validated: list[str] = []
        for j, tp in enumerate(raw_trailer_plates):
            if not tp:
                continue
            try:
                validated.append(VehiclePlate(tp).value)
            except ValueError:
                errors.append(
                    f"{prefix}.TrailerPlate[{j}] — Placa inválida — "
                    f"formato aceito: ABC1234 ou ABC1D23"
                )
        return validated


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
        if not cnpj_origin:
            errors.append("CNPJ_Origin é obrigatório")
        else:
            try:
                Cnpj(cnpj_origin)
            except ValueError as e:
                errors.append(f"CNPJ_Origin — CNPJ inválido: {e}")

        incoterms = str(data.get("Incoterms", ""))
        if incoterms not in ("CIF", "FOB"):
            errors.append(
                f"Incoterms inválido '{incoterms}' — valores aceitos: CIF, FOB"
            )

        operation_type = str(data.get("OperationType", ""))
        if operation_type not in ("0", "1", "2", "3"):
            errors.append(
                f"OperationType inválido '{operation_type}' — valores aceitos: 0, 1, 2, 3"
            )

        folder_list = data.get("Folder")
        if not folder_list:
            errors.append("Folder é obrigatório e não pode ser vazio")

        if errors:
            raise ValueError("\n".join(errors))

        # Check duplicate FolderNumbers
        folder_numbers: list[str] = []
        for fd in folder_list:
            fn = fd.get("FolderNumber", "")
            if fn and fn in folder_numbers:
                errors.append(f"FolderNumber '{fn}' duplicado — cada pasta deve ter número único")
            folder_numbers.append(fn)

        if errors:
            raise ValueError("\n".join(errors))

        folders: list[FreightOrderFolder] = []
        folder_errors: list[str] = []
        for i, folder_data in enumerate(folder_list):
            try:
                folders.append(FreightOrderFolder.from_dict(folder_data, index=i))
            except ValueError as e:
                folder_errors.append(str(e))

        if folder_errors:
            raise ValueError("\n".join(folder_errors))

        return cls(
            freight_order=freight_order,
            erp=str(data.get("ERP", "")),
            carrier=carrier,
            cnpj_origin=cnpj_origin,
            incoterms=incoterms,
            operation_type=operation_type,
            folders=tuple(folders),
        )
