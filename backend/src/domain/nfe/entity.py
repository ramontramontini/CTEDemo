"""NF-e entity — lightweight mock for related NF-e validation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Nfe:
    """Represents a Nota Fiscal Eletrônica record in the mock database."""

    key: str
    status: str
    emitter_cnpj: str
