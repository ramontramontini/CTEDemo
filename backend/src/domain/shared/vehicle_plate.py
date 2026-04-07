"""VehiclePlate value object — immutable, old + Mercosul format."""

import re
from dataclasses import dataclass

OLD_FORMAT = re.compile(r"^[A-Z]{3}[0-9]{4}$")
MERCOSUL_FORMAT = re.compile(r"^[A-Z]{3}[0-9][A-Z][0-9]{2}$")


@dataclass(frozen=True)
class VehiclePlate:
    """Brazilian vehicle plate — old (ABC1234) or Mercosul (ABC1D23) format."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Placa inválida — não pode ser vazia")
        normalized = self.value.upper()
        if not OLD_FORMAT.match(normalized) and not MERCOSUL_FORMAT.match(normalized):
            raise ValueError(
                "Placa inválida — formato aceito: ABC1234 ou ABC1D23"
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
