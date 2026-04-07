"""Transportadora entity — data + behavior + invariants."""

import re
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from src.domain.shared.cnpj import Cnpj
from src.domain.transportadora.enums import TransportadoraStatus


class Transportadora:
    """Transportadora (carrier) aggregate root — CT-e XML fields."""

    def __init__(
        self,
        id: UUID,
        cnpj: Cnpj,
        razao_social: str,
        nome_fantasia: str,
        ie: str,
        uf: str,
        cidade: str,
        logradouro: str,
        numero: str,
        bairro: str,
        cep: str,
        status: TransportadoraStatus,
        created_at: datetime,
        updated_at: Optional[datetime] = None,
    ):
        self._id = id
        self._cnpj = cnpj
        self._razao_social = razao_social
        self._nome_fantasia = nome_fantasia
        self._ie = ie
        self._uf = uf
        self._cidade = cidade
        self._logradouro = logradouro
        self._numero = numero
        self._bairro = bairro
        self._cep = cep
        self._status = status
        self._created_at = created_at
        self._updated_at = updated_at

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def cnpj(self) -> str:
        return self._cnpj.value

    @property
    def razao_social(self) -> str:
        return self._razao_social

    @property
    def nome_fantasia(self) -> str:
        return self._nome_fantasia

    @property
    def ie(self) -> str:
        return self._ie

    @property
    def uf(self) -> str:
        return self._uf

    @property
    def cidade(self) -> str:
        return self._cidade

    @property
    def logradouro(self) -> str:
        return self._logradouro

    @property
    def numero(self) -> str:
        return self._numero

    @property
    def bairro(self) -> str:
        return self._bairro

    @property
    def cep(self) -> str:
        return self._cep

    @property
    def status(self) -> TransportadoraStatus:
        return self._status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> Optional[datetime]:
        return self._updated_at

    def update(self, **kwargs: object) -> None:
        """Update mutable fields. Validates CNPJ if changed."""
        if not kwargs:
            return
        for field, value in kwargs.items():
            if field == "cnpj":
                stripped = re.sub(r"[.\-/]", "", str(value))
                self._cnpj = Cnpj(stripped)
            elif field == "razao_social":
                if not value or not str(value).strip():
                    raise ValueError("razao_social cannot be empty")
                self._razao_social = str(value).strip()
            elif field in (
                "nome_fantasia", "ie", "uf", "cidade",
                "logradouro", "numero", "bairro", "cep",
            ):
                setattr(self, f"_{field}", str(value))
            else:
                raise ValueError(f"Unknown field: {field}")
        self._updated_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return (
            f"Transportadora(id={self._id}, cnpj={self._cnpj}, "
            f"razao_social={self._razao_social!r}, status={self._status})"
        )
