"""In-memory Cte repository implementation."""

import json
from typing import Optional
from uuid import UUID

from src.domain.cte.entity import Cte
from src.domain.cte.enums import CteStatus
from src.domain.cte.repository import CteRepository
from src.infrastructure.database.repositories.memory.state import MemoryState


class MemoryCteRepository(CteRepository):
    """Memory-backed repository for Cte."""

    def __init__(self, state: MemoryState):
        self._state = state
        self._collection_name = "ctes"

    def save(self, entity: Cte) -> Cte:
        collection = self._state.get_collection(self._collection_name)
        data = {
            "id": str(entity.id),
            "access_key": entity.access_key,
            "freight_order_number": entity.freight_order_number,
            "status": entity.status.value,
            "xml": entity.xml,
            "original_payload": json.dumps(entity.original_payload),
            "created_at": entity.created_at.isoformat(),
        }
        for i, item in enumerate(collection):
            if item["id"] == str(entity.id):
                collection[i] = data
                self._state.save()
                return entity
        collection.append(data)
        self._state.save()
        return entity

    def find_by_id(self, id: UUID) -> Optional[Cte]:
        collection = self._state.get_collection(self._collection_name)
        for item in collection:
            if item["id"] == str(id):
                return self._to_entity(item)
        return None

    def find_all(self) -> list[Cte]:
        collection = self._state.get_collection(self._collection_name)
        return [self._to_entity(item) for item in collection]

    def delete(self, id: UUID) -> bool:
        collection = self._state.get_collection(self._collection_name)
        for i, item in enumerate(collection):
            if item["id"] == str(id):
                collection.pop(i)
                self._state.save()
                return True
        return False

    @staticmethod
    def _to_entity(data: dict) -> Cte:
        from datetime import datetime
        payload = data.get("original_payload", "{}")
        if isinstance(payload, str):
            payload = json.loads(payload)
        return Cte(
            id=UUID(data["id"]),
            access_key=data["access_key"],
            freight_order_number=data["freight_order_number"],
            status=CteStatus(data["status"]),
            xml=data["xml"],
            original_payload=payload,
            created_at=datetime.fromisoformat(data["created_at"]),
        )
