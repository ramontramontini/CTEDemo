"""Destinatario API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends

from src.api.dependencies import get_destinatario_repository
from src.api.exceptions import NotFoundError
from src.api.v1.schemas.destinatario_schemas import CreateDestinatarioRequest
from src.api.v1.serializers.destinatario_serializer import destinatario_to_response
from src.domain.destinatario.home import DestinatarioHome
from src.domain.destinatario.repository import DestinatarioRepository

router = APIRouter()


@router.get("/destinatarios")
async def list_destinatarios(
    repo: DestinatarioRepository = Depends(get_destinatario_repository),
):
    entities = repo.find_all()
    return [destinatario_to_response(e) for e in entities]


@router.get("/destinatarios/{id}")
async def get_destinatario(
    id: UUID,
    repo: DestinatarioRepository = Depends(get_destinatario_repository),
):
    entity = repo.find_by_id(id)
    if entity is None:
        raise NotFoundError(f"Destinatario {id} not found")
    return destinatario_to_response(entity)


@router.post("/destinatarios", status_code=201)
async def create_destinatario(
    request: CreateDestinatarioRequest,
    repo: DestinatarioRepository = Depends(get_destinatario_repository),
):
    entity = DestinatarioHome.create(name=request.name)
    repo.save(entity)
    return destinatario_to_response(entity)
