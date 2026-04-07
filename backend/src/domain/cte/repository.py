"""Cte repository interface (port)."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from src.domain.cte.entity import Cte


class CteRepository(ABC):
    """Abstract repository for Cte persistence."""

    @abstractmethod
    def save(self, entity: Cte) -> Cte:
        ...

    @abstractmethod
    def find_by_id(self, id: UUID) -> Optional[Cte]:
        ...

    @abstractmethod
    def find_all(self) -> list[Cte]:
        ...

    @abstractmethod
    def delete(self, id: UUID) -> bool:
        ...
