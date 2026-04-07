"""Transportadora repository interface (port)."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from src.domain.transportadora.entity import Transportadora


class TransportadoraRepository(ABC):
    """Abstract repository for Transportadora persistence."""

    @abstractmethod
    def save(self, entity: Transportadora) -> Transportadora:
        ...

    @abstractmethod
    def find_by_id(self, id: UUID) -> Optional[Transportadora]:
        ...

    @abstractmethod
    def find_by_cnpj(self, cnpj: str) -> Optional[Transportadora]:
        ...

    @abstractmethod
    def find_all(self) -> list[Transportadora]:
        ...

    @abstractmethod
    def delete(self, id: UUID) -> bool:
        ...
