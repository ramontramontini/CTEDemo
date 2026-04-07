"""Remetente value objects — immutable domain concepts."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RemetenteId:
    """Strongly-typed identifier for Remetente."""
    value: str

    def __str__(self) -> str:
        return self.value
