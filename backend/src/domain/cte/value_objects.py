"""Cte value objects — immutable domain concepts."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CteId:
    """Strongly-typed identifier for Cte."""
    value: str

    def __str__(self) -> str:
        return self.value
