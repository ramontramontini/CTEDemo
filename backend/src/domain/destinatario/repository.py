"""Destinatario repository interface (port)."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from src.domain.destinatario.entity import Destinatario


class DestinatarioRepository(ABC):
    """Abstract repository for Destinatario persistence."""

    @abstractmethod
    def save(self, entity: Destinatario) -> Destinatario:
        ...

    @abstractmethod
    def find_by_id(self, id: UUID) -> Optional[Destinatario]:
        ...

    @abstractmethod
    def find_all(self) -> list[Destinatario]:
        ...

    @abstractmethod
    def delete(self, id: UUID) -> bool:
        ...

    @abstractmethod
    def find_by_cnpj(self, cnpj: str) -> Optional[Destinatario]:
        ...
