"""Destinatario entity-to-response serializer."""

from src.domain.destinatario.entity import Destinatario


def destinatario_to_response(entity: Destinatario) -> dict:
    return {
        "id": str(entity.id),
        "name": entity.name,
        "status": entity.status.value,
        "created_at": entity.created_at.isoformat(),
        "updated_at": entity.updated_at.isoformat() if entity.updated_at else None,
    }
