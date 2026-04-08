"""Cte entity-to-response serializer — Postman-compatible field names."""

from src.domain.cte.entity import Cte

STATUS_MAP = {
    "gerado": "Generated",
    "erro": "Error",
}


def cte_to_response(entity: Cte) -> dict:
    payload = entity.original_payload
    return {
        "id": str(entity.id),
        "cTeKey": entity.access_key,
        "formattedAccessKey": entity.formatted_access_key(),
        "freightOrderNumber": entity.freight_order_number,
        "status": STATUS_MAP.get(entity.status.value, entity.status.value),
        "erp": payload.get("ERP", ""),
        "documentType": "CT-e",
        "totalFolders": len(payload.get("Folder", [])),
        "xml": entity.xml,
        "createdAt": entity.created_at.isoformat(),
        "updatedAt": entity.created_at.isoformat(),
    }
