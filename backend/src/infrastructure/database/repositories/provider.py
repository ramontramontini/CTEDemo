"""Repository provider — switches between memory and DB implementations."""

from src.config.settings import settings
from src.infrastructure.database.repositories.memory.state import MemoryState

from src.domain.cte.repository import CteRepository
from src.domain.remetente.repository import RemetenteRepository
from src.domain.destinatario.repository import DestinatarioRepository
from src.domain.transportadora.repository import TransportadoraRepository
from src.domain.nfe.repository import NfeRepository

from src.infrastructure.database.repositories.memory.cte_repository import MemoryCteRepository
from src.infrastructure.database.repositories.memory.remetente_repository import MemoryRemetenteRepository
from src.infrastructure.database.repositories.memory.destinatario_repository import MemoryDestinatarioRepository
from src.infrastructure.database.repositories.memory.transportadora_repository import MemoryTransportadoraRepository
from src.infrastructure.database.repositories.memory.nfe_repository import MemoryNfeRepository


class RepositoryProvider:
    def __init__(self, data_mode: str = "memory"):
        self._data_mode = data_mode
        self._memory_state = MemoryState() if data_mode == "memory" else None


    def get_cte_repository(self) -> CteRepository:
        if self._data_mode == "memory":
            return MemoryCteRepository(self._memory_state)
        raise NotImplementedError("DB repositories not yet implemented")

    def get_remetente_repository(self) -> RemetenteRepository:
        if self._data_mode == "memory":
            return MemoryRemetenteRepository(self._memory_state)
        raise NotImplementedError("DB repositories not yet implemented")

    def get_destinatario_repository(self) -> DestinatarioRepository:
        if self._data_mode == "memory":
            return MemoryDestinatarioRepository(self._memory_state)
        raise NotImplementedError("DB repositories not yet implemented")

    def get_transportadora_repository(self) -> TransportadoraRepository:
        if self._data_mode == "memory":
            return MemoryTransportadoraRepository(self._memory_state)
        raise NotImplementedError("DB repositories not yet implemented")

    def get_nfe_repository(self) -> NfeRepository:
        if self._data_mode == "memory":
            return MemoryNfeRepository(self._memory_state)
        raise NotImplementedError("DB repositories not yet implemented")


_provider: RepositoryProvider | None = None


def get_repository_provider() -> RepositoryProvider:
    global _provider
    if _provider is None:
        _provider = RepositoryProvider(data_mode=settings.data_mode)
    return _provider
