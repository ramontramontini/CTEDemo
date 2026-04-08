"""Dependency injection for API endpoints."""

from src.domain.cte.repository import CteRepository
from src.domain.remetente.repository import RemetenteRepository
from src.domain.destinatario.repository import DestinatarioRepository
from src.domain.transportadora.repository import TransportadoraRepository
from src.domain.cte.publisher import CtePublisher
from src.domain.nfe.repository import NfeRepository

# Singleton publisher instance (memory mode)
_cte_publisher: CtePublisher | None = None


def get_cte_publisher() -> CtePublisher:
    """Get CT-e publisher (singleton MemoryCtePublisher)."""
    global _cte_publisher
    if _cte_publisher is None:
        from src.infrastructure.messaging.memory_cte_publisher import MemoryCtePublisher
        _cte_publisher = MemoryCtePublisher()
    return _cte_publisher


def get_cte_repository() -> CteRepository:
    """Get cte repository based on DATA_MODE."""
    from src.infrastructure.database.repositories.provider import get_repository_provider
    return get_repository_provider().get_cte_repository()

def get_remetente_repository() -> RemetenteRepository:
    """Get remetente repository based on DATA_MODE."""
    from src.infrastructure.database.repositories.provider import get_repository_provider
    return get_repository_provider().get_remetente_repository()

def get_destinatario_repository() -> DestinatarioRepository:
    """Get destinatario repository based on DATA_MODE."""
    from src.infrastructure.database.repositories.provider import get_repository_provider
    return get_repository_provider().get_destinatario_repository()

def get_transportadora_repository() -> TransportadoraRepository:
    """Get transportadora repository based on DATA_MODE."""
    from src.infrastructure.database.repositories.provider import get_repository_provider
    return get_repository_provider().get_transportadora_repository()

def get_nfe_repository() -> NfeRepository:
    """Get NF-e repository based on DATA_MODE."""
    from src.infrastructure.database.repositories.provider import get_repository_provider
    return get_repository_provider().get_nfe_repository()
