"""Cte entity-to-response serializer."""

from src.domain.cte.entity import Cte


def cte_to_response(entity: Cte) -> dict:
    return {
        "id": str(entity.id),
        "access_key": entity.access_key,
        "formatted_access_key": entity.formatted_access_key(),
        "freight_order_number": entity.freight_order_number,
        "status": entity.status.value,
        "xml": entity.xml,
        "created_at": entity.created_at.isoformat(),
    }
