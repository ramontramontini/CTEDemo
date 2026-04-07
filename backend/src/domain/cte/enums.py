"""Cte enumerations."""

from enum import Enum


class CteStatus(str, Enum):
    """Status of a generated CT-e document."""
    GERADO = "gerado"
    ERRO = "erro"
