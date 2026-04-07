"""Transportadora value objects — immutable domain concepts."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TransportadoraId:
    """Strongly-typed identifier for Transportadora."""
    value: str

    def __str__(self) -> str:
        return self.value
