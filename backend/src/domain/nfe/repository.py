"""NF-e repository interface (port)."""

from abc import ABC, abstractmethod

from src.domain.nfe.entity import Nfe


class NfeRepository(ABC):
    @abstractmethod
    def find_by_key(self, key: str) -> Nfe | None: ...

    @abstractmethod
    def find_all(self) -> list[Nfe]: ...
