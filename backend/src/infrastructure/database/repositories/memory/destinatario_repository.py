"""In-memory Destinatario repository implementation."""

from typing import Optional
from uuid import UUID, uuid4

from src.domain.destinatario.entity import Destinatario
from src.domain.destinatario.enums import DestinatarioStatus
from src.domain.destinatario.repository import DestinatarioRepository
from src.infrastructure.database.repositories.memory.state import MemoryState


class MemoryDestinatarioRepository(DestinatarioRepository):
    """Memory-backed repository for Destinatario."""

    def __init__(self, state: MemoryState):
        self._state = state
        self._collection_name = "destinatarios"

    def save(self, entity: Destinatario) -> Destinatario:
        collection = self._state.get_collection(self._collection_name)
        data = {
            "id": str(entity.id),
            "cnpj": entity.cnpj,
            "cpf": entity.cpf,
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

    def find_by_id(self, id: UUID) -> Optional[Destinatario]:
        collection = self._state.get_collection(self._collection_name)
        for item in collection:
            if item["id"] == str(id):
                return self._to_entity(item)
        return None

    def find_all(self) -> list[Destinatario]:
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

    def find_by_cnpj(self, cnpj: str) -> Optional[Destinatario]:
        collection = self._state.get_collection(self._collection_name)
        for item in collection:
            if item.get("cnpj") == cnpj:
                return self._to_entity(item)
        return None

    def seed_if_empty(self) -> None:
        """Seed with geo-diverse entries: PE (same as carrier) + SP (different UF)."""
        collection = self._state.get_collection(self._collection_name)
        if collection:
            return
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        collection.extend([
            {
                "id": str(uuid4()),
                "cnpj": "44555666000181",
                "cpf": None,
                "razao_social": "Comercio Recife Ltda",
                "nome_fantasia": "Recife Com",
                "ie": "123456789",
                "uf": "PE",
                "cidade": "Recife",
                "logradouro": "Rua do Sol",
                "numero": "50",
                "bairro": "Boa Vista",
                "cep": "50060000",
                "status": "active",
                "created_at": now,
                "updated_at": None,
            },
            {
                "id": str(uuid4()),
                "cnpj": None,
                "cpf": "12345678909",
                "razao_social": "Maria Silva",
                "nome_fantasia": "",
                "ie": "",
                "uf": "SP",
                "cidade": "Sao Paulo",
                "logradouro": "Av Paulista",
                "numero": "1000",
                "bairro": "Bela Vista",
                "cep": "01310100",
                "status": "active",
                "created_at": now,
                "updated_at": None,
            },
        ])
        self._state.save()

    @staticmethod
    def _to_entity(data: dict) -> Destinatario:
        from datetime import datetime
        return Destinatario(
            id=UUID(data["id"]),
            cnpj=data.get("cnpj"),
            cpf=data.get("cpf"),
            razao_social=data.get("razao_social", ""),
            nome_fantasia=data.get("nome_fantasia", ""),
            ie=data.get("ie", ""),
            uf=data.get("uf", ""),
            cidade=data.get("cidade", ""),
            logradouro=data.get("logradouro", ""),
            numero=data.get("numero", ""),
            bairro=data.get("bairro", ""),
            cep=data.get("cep", ""),
            status=DestinatarioStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )
