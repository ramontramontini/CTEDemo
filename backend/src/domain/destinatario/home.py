"""Destinatario Home — factory + lifecycle management."""

import re
from datetime import datetime, timezone
from uuid import uuid4

from src.domain.destinatario.entity import Destinatario
from src.domain.destinatario.enums import DestinatarioStatus
from src.domain.shared.cnpj import Cnpj
from src.domain.shared.cpf import Cpf


class DestinatarioHome:
    """Factory and lifecycle manager for Destinatario aggregate."""

    @staticmethod
    def create(
        razao_social: str,
        cnpj: str = "",
        cpf: str = "",
        nome_fantasia: str = "",
        ie: str = "",
        uf: str = "",
        cidade: str = "",
        logradouro: str = "",
        numero: str = "",
        bairro: str = "",
        cep: str = "",
    ) -> Destinatario:
        """Create a new Destinatario with either CNPJ (PJ) or CPF (PF)."""
        has_cnpj = bool(cnpj and cnpj.strip())
        has_cpf = bool(cpf and cpf.strip())

        if has_cnpj == has_cpf:
            raise ValueError(
                "Informe CNPJ ou CPF — exatamente um deve ser fornecido"
            )

        cnpj_clean = None
        cpf_clean = None

        if has_cnpj:
            cnpj_clean = re.sub(r"\D", "", cnpj)
            Cnpj(cnpj_clean)
        else:
            cpf_clean = re.sub(r"\D", "", cpf)
            Cpf(cpf_clean)

        if not razao_social or not razao_social.strip():
            raise ValueError("Razão social is required")
        razao_social = razao_social.strip()

        if uf and not re.match(r"^[A-Z]{2}$", uf):
            raise ValueError("UF must be 2 uppercase letters")

        cep_clean = re.sub(r"\D", "", cep) if cep else ""
        if cep_clean and len(cep_clean) != 8:
            raise ValueError("CEP must be exactly 8 digits")

        return Destinatario(
            id=uuid4(),
            cnpj=cnpj_clean,
            cpf=cpf_clean,
            razao_social=razao_social,
            nome_fantasia=nome_fantasia,
            ie=ie,
            uf=uf,
            cidade=cidade,
            logradouro=logradouro,
            numero=numero,
            bairro=bairro,
            cep=cep_clean,
            status=DestinatarioStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
        )
