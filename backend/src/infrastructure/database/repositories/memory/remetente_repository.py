"""In-memory Remetente repository implementation."""

from typing import Optional
from uuid import UUID

from src.domain.remetente.entity import Remetente
from src.domain.remetente.enums import RemetenteStatus
from src.domain.remetente.repository import RemetenteRepository
from src.infrastructure.database.repositories.memory.state import MemoryState


class MemoryRemetenteRepository(RemetenteRepository):
    """Memory-backed repository for Remetente."""

    def __init__(self, state: MemoryState):
        self._state = state
        self._collection_name = "remetentes"

    def save(self, entity: Remetente) -> Remetente:
        collection = self._state.get_collection(self._collection_name)
        data = {
            "id": str(entity.id),
            "name": entity.name,
            "status": entity.status.value,
            "created_at": entity.created_at.isoformat(),
            "updated_at": entity.updated_at.isoformat() if entity.updated_at else None,
        }
        # Update existing or append
        for i, item in enumerate(collection):
            if item["id"] == str(entity.id):
                collection[i] = data
                self._state.save()
                return entity
        collection.append(data)
        self._state.save()
        return entity

    def find_by_id(self, id: UUID) -> Optional[Remetente]:
        collection = self._state.get_collection(self._collection_name)
        for item in collection:
            if item["id"] == str(id):
                return self._to_entity(item)
        return None

    def find_all(self) -> list[Remetente]:
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
    def _to_entity(data: dict) -> Remetente:
        from datetime import datetime
        return Remetente(
            id=UUID(data["id"]),
            name=data["name"],
            status=RemetenteStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )
