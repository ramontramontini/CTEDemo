"""Cte entity-to-response serializer."""

from src.domain.cte.entity import Cte


def cte_to_response(entity: Cte, warnings: list[str] | None = None) -> dict:
    response = {
        "id": str(entity.id),
        "access_key": entity.access_key,
        "formatted_access_key": entity.formatted_access_key(),
        "freight_order_number": entity.freight_order_number,
        "status": entity.status.value,
        "xml": entity.xml,
        "original_payload": entity.original_payload,
        "created_at": entity.created_at.isoformat(),
        "warnings": warnings or [],
    }
    return response
