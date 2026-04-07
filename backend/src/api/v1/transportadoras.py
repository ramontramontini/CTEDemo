"""Transportadora API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends

from src.api.dependencies import get_transportadora_repository
from src.api.exceptions import NotFoundError
from src.api.v1.schemas.transportadora_schemas import CreateTransportadoraRequest
from src.api.v1.serializers.transportadora_serializer import transportadora_to_response
from src.domain.transportadora.home import TransportadoraHome
from src.domain.transportadora.repository import TransportadoraRepository

router = APIRouter()


@router.get("/transportadoras")
async def list_transportadoras(
    repo: TransportadoraRepository = Depends(get_transportadora_repository),
):
    entities = repo.find_all()
    return [transportadora_to_response(e) for e in entities]


@router.get("/transportadoras/{id}")
async def get_transportadora(
    id: UUID,
    repo: TransportadoraRepository = Depends(get_transportadora_repository),
):
    entity = repo.find_by_id(id)
    if entity is None:
        raise NotFoundError(f"Transportadora {id} not found")
    return transportadora_to_response(entity)


@router.post("/transportadoras", status_code=201)
async def create_transportadora(
    request: CreateTransportadoraRequest,
    repo: TransportadoraRepository = Depends(get_transportadora_repository),
):
    entity = TransportadoraHome.create(name=request.name)
    repo.save(entity)
    return transportadora_to_response(entity)
