"""Transportadora entity-to-response serializer."""

from src.domain.transportadora.entity import Transportadora


def transportadora_to_response(entity: Transportadora) -> dict:
    return {
        "id": str(entity.id),
        "name": entity.name,
        "status": entity.status.value,
        "created_at": entity.created_at.isoformat(),
        "updated_at": entity.updated_at.isoformat() if entity.updated_at else None,
    }
