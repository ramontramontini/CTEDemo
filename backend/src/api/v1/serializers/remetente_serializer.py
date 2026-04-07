"""Remetente entity-to-response serializer."""

from src.domain.remetente.entity import Remetente


def remetente_to_response(entity: Remetente) -> dict:
    return {
        "id": str(entity.id),
        "name": entity.name,
        "status": entity.status.value,
        "created_at": entity.created_at.isoformat(),
        "updated_at": entity.updated_at.isoformat() if entity.updated_at else None,
    }
