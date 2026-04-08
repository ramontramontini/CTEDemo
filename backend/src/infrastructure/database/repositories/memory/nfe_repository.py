"""In-memory NF-e repository with seed data."""

from src.domain.nfe.entity import Nfe
from src.domain.nfe.repository import NfeRepository
from src.infrastructure.database.repositories.memory.state import MemoryState


_SEED_DATA = [
    {
        "key": "35230410758386000159550010000000011000000015",
        "status": "authorized",
        "emitter_cnpj": "10758386000159",
    },
    {
        "key": "35230410758386000159550010000000021000000022",
        "status": "canceled",
        "emitter_cnpj": "10758386000159",
    },
    {
        "key": "31230499888777000166550010000000031000000039",
        "status": "authorized",
        "emitter_cnpj": "99888777000166",
    },
]


class MemoryNfeRepository(NfeRepository):
    """Memory-backed repository for NF-e mock data."""

    def __init__(self, state: MemoryState):
        self._state = state
        self._collection_name = "nfes"
        self._seed_if_empty()

    def find_by_key(self, key: str) -> Nfe | None:
        collection = self._state.get_collection(self._collection_name)
        for item in collection:
            if item["key"] == key:
                return self._to_entity(item)
        return None

    def find_all(self) -> list[Nfe]:
        collection = self._state.get_collection(self._collection_name)
        return [self._to_entity(item) for item in collection]

    def _seed_if_empty(self) -> None:
        collection = self._state.get_collection(self._collection_name)
        if collection:
            return
        for seed in _SEED_DATA:
            collection.append(dict(seed))
        self._state.save()

    @staticmethod
    def _to_entity(data: dict) -> Nfe:
        return Nfe(
            key=data["key"],
            status=data["status"],
            emitter_cnpj=data["emitter_cnpj"],
        )
