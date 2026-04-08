"""In-memory Remetente repository implementation."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from src.domain.remetente.entity import Remetente
from src.domain.remetente.enums import RemetenteStatus
from src.domain.remetente.home import RemetenteHome
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

    def find_by_cnpj(self, cnpj: str) -> Optional[Remetente]:
        collection = self._state.get_collection(self._collection_name)
        for item in collection:
            if item["cnpj"] == cnpj:
                return self._to_entity(item)
        return None

    def seed_if_empty(self) -> None:
        collection = self._state.get_collection(self._collection_name)
        if collection:
            return
        seeds = [
            RemetenteHome.create(
                cnpj="03026527000183",
                razao_social="Remetente Postman Ltda",
                nome_fantasia="Postman Rem",
                ie="123456789",
                uf="SP",
                cidade="Sao Paulo",
                logradouro="Rua das Flores",
                numero="100",
                bairro="Centro",
                cep="01001000",
            ),
            RemetenteHome.create(
                cnpj="11444777000161",
                razao_social="Industria XYZ SA",
                nome_fantasia="XYZ",
                ie="987654321",
                uf="RJ",
                cidade="Rio de Janeiro",
                logradouro="Av Atlantica",
                numero="200",
                bairro="Copacabana",
                cep="22041080",
            ),
        ]
        for entity in seeds:
            self.save(entity)

    @staticmethod
    def _to_entity(data: dict) -> Remetente:
        return Remetente(
            id=UUID(data["id"]),
            cnpj=data["cnpj"],
            razao_social=data["razao_social"],
            nome_fantasia=data.get("nome_fantasia", ""),
            ie=data.get("ie", ""),
            uf=data.get("uf", ""),
            cidade=data.get("cidade", ""),
            logradouro=data.get("logradouro", ""),
            numero=data.get("numero", ""),
            bairro=data.get("bairro", ""),
            cep=data.get("cep", ""),
            status=RemetenteStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )
