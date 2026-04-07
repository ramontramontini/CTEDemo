"""Remetente Home — factory + lifecycle management."""

import re
from datetime import datetime, timezone
from uuid import uuid4

from src.domain.remetente.entity import Remetente
from src.domain.remetente.enums import RemetenteStatus
from src.domain.shared.cnpj import Cnpj


class RemetenteHome:
    """Factory and lifecycle manager for Remetente aggregate."""

    @staticmethod
    def create(
        cnpj: str,
        razao_social: str,
        nome_fantasia: str = "",
        ie: str = "",
        uf: str = "",
        cidade: str = "",
        logradouro: str = "",
        numero: str = "",
        bairro: str = "",
        cep: str = "",
    ) -> Remetente:
        """Create a new Remetente instance with CT-e <rem> fields."""
        # Strip CNPJ formatting and validate via VO
        cnpj_clean = re.sub(r"\D", "", cnpj)
        Cnpj(cnpj_clean)  # raises ValueError if invalid

        if not razao_social or not razao_social.strip():
            raise ValueError("Razão social is required")
        razao_social = razao_social.strip()

        if uf and not re.match(r"^[A-Z]{2}$", uf):
            raise ValueError("UF must be 2 uppercase letters")

        cep_clean = re.sub(r"\D", "", cep) if cep else ""
        if cep_clean and len(cep_clean) != 8:
            raise ValueError("CEP must be exactly 8 digits")

        return Remetente(
            id=uuid4(),
            cnpj=cnpj_clean,
            razao_social=razao_social,
            nome_fantasia=nome_fantasia,
            ie=ie,
            uf=uf,
            cidade=cidade,
            logradouro=logradouro,
            numero=numero,
            bairro=bairro,
            cep=cep_clean,
            status=RemetenteStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
        )
