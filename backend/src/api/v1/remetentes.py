"""Remetente API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends

from src.api.dependencies import get_remetente_repository
from src.api.exceptions import NotFoundError
from src.api.v1.schemas.remetente_schemas import CreateRemetenteRequest
from src.api.v1.serializers.remetente_serializer import remetente_to_response
from src.domain.remetente.home import RemetenteHome
from src.domain.remetente.repository import RemetenteRepository

router = APIRouter()


@router.get("/remetentes")
async def list_remetentes(
    repo: RemetenteRepository = Depends(get_remetente_repository),
):
    entities = repo.find_all()
    return [remetente_to_response(e) for e in entities]


@router.get("/remetentes/{id}")
async def get_remetente(
    id: UUID,
    repo: RemetenteRepository = Depends(get_remetente_repository),
):
    entity = repo.find_by_id(id)
    if entity is None:
        raise NotFoundError(f"Remetente {id} not found")
    return remetente_to_response(entity)


@router.post("/remetentes", status_code=201)
async def create_remetente(
    request: CreateRemetenteRequest,
    repo: RemetenteRepository = Depends(get_remetente_repository),
):
    entity = RemetenteHome.create(name=request.name)
    repo.save(entity)
    return remetente_to_response(entity)
