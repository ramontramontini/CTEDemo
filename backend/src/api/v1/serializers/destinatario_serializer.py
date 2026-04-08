"""Destinatario entity-to-response serializer."""

from src.domain.destinatario.entity import Destinatario


def destinatario_to_response(entity: Destinatario) -> dict:
    return {
        "id": str(entity.id),
        "cnpj": entity.cnpj,
        "cpf": entity.cpf,
        "razao_social": entity.razao_social,
        "nome_fantasia": entity.nome_fantasia,
        "ie": entity.ie,
        "uf": entity.uf,
        "cidade": entity.cidade,
        "logradouro": entity.logradouro,
        "numero": entity.numero,
        "bairro": entity.bairro,
        "cep": entity.cep,
        "status": entity.status.value,
        "created_at": entity.created_at.isoformat(),
        "updated_at": entity.updated_at.isoformat() if entity.updated_at else None,
    }
