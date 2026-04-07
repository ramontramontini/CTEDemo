"""Transportadora entity-to-response serializer."""

from src.domain.transportadora.entity import Transportadora


def transportadora_to_response(entity: Transportadora) -> dict:
    return {
        "id": str(entity.id),
        "cnpj": entity.cnpj,
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
