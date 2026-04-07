"""Remetente repository interface (port)."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from src.domain.remetente.entity import Remetente


class RemetenteRepository(ABC):
    """Abstract repository for Remetente persistence."""

    @abstractmethod
    def save(self, entity: Remetente) -> Remetente:
        ...

    @abstractmethod
    def find_by_id(self, id: UUID) -> Optional[Remetente]:
        ...

    @abstractmethod
    def find_all(self) -> list[Remetente]:
        ...

    @abstractmethod
    def delete(self, id: UUID) -> bool:
        ...
