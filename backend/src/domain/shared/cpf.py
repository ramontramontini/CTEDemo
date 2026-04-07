"""Cpf value object — immutable, mod11 validated."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Cpf:
    """Brazilian CPF (11-digit personal ID) with mod11 validation."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.isdigit() or len(self.value) != 11:
            raise ValueError("CPF inválido — deve conter exatamente 11 dígitos")
        if len(set(self.value)) == 1:
            raise ValueError("CPF inválido — sequência repetida")
        if not self._validate_dv():
            raise ValueError("CPF inválido — dígito verificador incorreto")

    def _validate_dv(self) -> bool:
        digits = [int(d) for d in self.value]
        dv1 = self._calc_dv(digits[:9], list(range(10, 1, -1)))
        dv2 = self._calc_dv(digits[:10], list(range(11, 1, -1)))
        return digits[9] == dv1 and digits[10] == dv2

    @staticmethod
    def _calc_dv(digits: list[int], weights: list[int]) -> int:
        total = sum(d * w for d, w in zip(digits, weights))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    def __str__(self) -> str:
        return self.value
