"""Cnpj value object — immutable, mod11 validated."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Cnpj:
    """Brazilian CNPJ (14-digit tax ID) with mod11 validation."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.isdigit() or len(self.value) != 14:
            raise ValueError("CNPJ inválido — deve conter exatamente 14 dígitos")
        if len(set(self.value)) == 1:
            raise ValueError("CNPJ inválido — sequência repetida")
        if not self._validate_dv():
            raise ValueError("CNPJ inválido — dígito verificador incorreto")

    def _validate_dv(self) -> bool:
        digits = [int(d) for d in self.value]
        dv1 = self._calc_dv(digits[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
        dv2 = self._calc_dv(digits[:13], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
        return digits[12] == dv1 and digits[13] == dv2

    @staticmethod
    def _calc_dv(digits: list[int], weights: list[int]) -> int:
        total = sum(d * w for d, w in zip(digits, weights))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    def __str__(self) -> str:
        return self.value
