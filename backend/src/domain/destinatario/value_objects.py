"""Destinatario value objects — immutable domain concepts."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DestinatarioId:
    """Strongly-typed identifier for Destinatario."""
    value: str

    def __str__(self) -> str:
        return self.value
