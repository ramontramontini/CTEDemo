"""Dev utilities — memory mode only."""

from fastapi import APIRouter

from src.config.settings import settings
from src.infrastructure.database.repositories.provider import get_repository_provider

router = APIRouter(prefix="/dev", tags=["dev"])


@router.post("/reset-data")
async def reset_data():
    """Clear all in-memory data and re-seed with fresh seed data."""
    if settings.data_mode != "memory":
        return {"status": "error", "message": "Reset only available in memory mode"}

    provider = get_repository_provider()
    provider._memory_state.clear()

    provider.get_remetente_repository().seed_if_empty()
    provider.get_destinatario_repository().seed_if_empty()
    # Transportadora and NFE seed in __init__ when collection is empty
    provider.get_transportadora_repository()
    provider.get_nfe_repository()

    return {"status": "ok", "message": "Dados resetados com sucesso"}
