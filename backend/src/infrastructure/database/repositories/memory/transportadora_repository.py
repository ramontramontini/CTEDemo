"""In-memory Transportadora repository implementation."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from src.domain.shared.cnpj import Cnpj
from src.domain.transportadora.entity import Transportadora
from src.domain.transportadora.enums import TransportadoraStatus
from src.domain.transportadora.repository import TransportadoraRepository
from src.infrastructure.database.repositories.memory.state import MemoryState


_SEED_DATA = [
    {
        "cnpj": "11222333000181",
        "razao_social": "Transportadora ABC Ltda",
        "nome_fantasia": "ABC Transportes",
        "ie": "110042490114",
        "uf": "SP",
        "cidade": "Sao Paulo",
        "logradouro": "Av Paulista",
        "numero": "1000",
        "bairro": "Bela Vista",
        "cep": "01310100",
    },
    {
        "cnpj": "33014556000196",
        "razao_social": "Log Express SA",
        "nome_fantasia": "LogEx",
        "ie": "77868647",
        "uf": "RJ",
        "cidade": "Rio de Janeiro",
        "logradouro": "Rua da Assembleia",
        "numero": "50",
        "bairro": "Centro",
        "cep": "20011000",
    },
]


class MemoryTransportadoraRepository(TransportadoraRepository):
    """Memory-backed repository for Transportadora."""

    def __init__(self, state: MemoryState):
        self._state = state
        self._collection_name = "transportadoras"
        self._seed_if_empty()

    def save(self, entity: Transportadora) -> Transportadora:
        collection = self._state.get_collection(self._collection_name)
        data = {
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
        for i, item in enumerate(collection):
            if item["id"] == str(entity.id):
                collection[i] = data
                self._state.save()
                return entity
        collection.append(data)
        self._state.save()
        return entity

    def find_by_id(self, id: UUID) -> Optional[Transportadora]:
        collection = self._state.get_collection(self._collection_name)
        for item in collection:
            if item["id"] == str(id):
                return self._to_entity(item)
        return None

    def find_by_cnpj(self, cnpj: str) -> Optional[Transportadora]:
        collection = self._state.get_collection(self._collection_name)
        for item in collection:
            if item["cnpj"] == cnpj:
                return self._to_entity(item)
        return None

    def find_all(self) -> list[Transportadora]:
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

    def _seed_if_empty(self) -> None:
        collection = self._state.get_collection(self._collection_name)
        if collection:
            return
        from uuid import uuid4
        for seed in _SEED_DATA:
            collection.append({
                "id": str(uuid4()),
                "cnpj": seed["cnpj"],
                "razao_social": seed["razao_social"],
                "nome_fantasia": seed.get("nome_fantasia", ""),
                "ie": seed.get("ie", ""),
                "uf": seed["uf"],
                "cidade": seed["cidade"],
                "logradouro": seed["logradouro"],
                "numero": seed["numero"],
                "bairro": seed["bairro"],
                "cep": seed["cep"],
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "updated_at": None,
            })
        self._state.save()

    @staticmethod
    def _to_entity(data: dict) -> Transportadora:
        return Transportadora(
            id=UUID(data["id"]),
            cnpj=Cnpj(data["cnpj"]),
            razao_social=data.get("razao_social", data.get("name", "")),
            nome_fantasia=data.get("nome_fantasia", ""),
            ie=data.get("ie", ""),
            uf=data.get("uf", ""),
            cidade=data.get("cidade", ""),
            logradouro=data.get("logradouro", ""),
            numero=data.get("numero", ""),
            bairro=data.get("bairro", ""),
            cep=data.get("cep", ""),
            status=TransportadoraStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )
