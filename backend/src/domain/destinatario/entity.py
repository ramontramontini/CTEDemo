"""Destinatario entity — data + behavior + invariants."""

import re
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from src.domain.destinatario.enums import DestinatarioStatus


class Destinatario:
    """Destinatario (recipient) aggregate root — CT-e XML <dest> fields.

    Supports both PJ (CNPJ) and PF (CPF) identification.
    Exactly one of cnpj/cpf is set; the other is None.
    """

    def __init__(
        self,
        id: UUID,
        cnpj: Optional[str],
        cpf: Optional[str],
        razao_social: str,
        nome_fantasia: str,
        ie: str,
        uf: str,
        cidade: str,
        logradouro: str,
        numero: str,
        bairro: str,
        cep: str,
        status: DestinatarioStatus,
        created_at: datetime,
        updated_at: Optional[datetime] = None,
    ):
        self._id = id
        self._cnpj = cnpj
        self._cpf = cpf
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
    def cnpj(self) -> Optional[str]:
        return self._cnpj

    @property
    def cpf(self) -> Optional[str]:
        return self._cpf

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
    def status(self) -> DestinatarioStatus:
        return self._status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> Optional[datetime]:
        return self._updated_at

    def update_razao_social(self, new_razao_social: str) -> None:
        if not new_razao_social or not new_razao_social.strip():
            raise ValueError("Razão social cannot be empty")
        self._razao_social = new_razao_social.strip()
        self._updated_at = datetime.now(timezone.utc)

    def update_nome_fantasia(self, new_nome_fantasia: str) -> None:
        self._nome_fantasia = new_nome_fantasia
        self._updated_at = datetime.now(timezone.utc)

    def update_ie(self, new_ie: str) -> None:
        self._ie = new_ie
        self._updated_at = datetime.now(timezone.utc)

    def update_endereco(
        self, uf: str, cidade: str, logradouro: str,
        numero: str, bairro: str, cep: str,
    ) -> None:
        cep_clean = re.sub(r"\D", "", cep) if cep else ""
        if cep_clean and len(cep_clean) != 8:
            raise ValueError("CEP must be exactly 8 digits")
        if uf and not re.match(r"^[A-Z]{2}$", uf):
            raise ValueError("UF must be 2 uppercase letters")
        self._uf = uf
        self._cidade = cidade
        self._logradouro = logradouro
        self._numero = numero
        self._bairro = bairro
        self._cep = cep_clean
        self._updated_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        doc_id = self._cnpj or self._cpf or "?"
        return (
            f"Destinatario(id={self._id}, doc={doc_id}, "
            f"razao_social={self._razao_social!r}, uf={self._uf})"
        )
