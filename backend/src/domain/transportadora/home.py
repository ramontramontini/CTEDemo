"""Transportadora Home — factory + lifecycle management."""

import re
from datetime import datetime, timezone
from uuid import uuid4

from src.domain.shared.cnpj import Cnpj
from src.domain.transportadora.entity import Transportadora
from src.domain.transportadora.enums import TransportadoraStatus
from src.domain.transportadora.errors import TransportadoraValidationError


class TransportadoraHome:
    """Factory and lifecycle manager for Transportadora aggregate."""

    _REQUIRED_FIELDS = ("razao_social", "uf", "cidade", "logradouro", "numero", "bairro", "cep")

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
    ) -> Transportadora:
        """Create a new Transportadora with CNPJ validation."""
        stripped_cnpj = re.sub(r"[.\-/]", "", cnpj)
        try:
            cnpj_vo = Cnpj(stripped_cnpj)
        except ValueError as e:
            raise TransportadoraValidationError(f"CNPJ invalido: {e}") from e

        fields = {
            "razao_social": razao_social,
            "uf": uf,
            "cidade": cidade,
            "logradouro": logradouro,
            "numero": numero,
            "bairro": bairro,
            "cep": cep,
        }
        for field_name, value in fields.items():
            if not value or not value.strip():
                raise TransportadoraValidationError(f"{field_name} is required")

        return Transportadora(
            id=uuid4(),
            cnpj=cnpj_vo,
            razao_social=razao_social.strip(),
            nome_fantasia=nome_fantasia.strip() if nome_fantasia else "",
            ie=ie.strip() if ie else "",
            uf=uf.strip().upper(),
            cidade=cidade.strip(),
            logradouro=logradouro.strip(),
            numero=numero.strip(),
            bairro=bairro.strip(),
            cep=cep.strip(),
            status=TransportadoraStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
        )
