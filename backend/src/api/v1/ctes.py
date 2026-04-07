"""Cte API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends

from src.api.dependencies import get_cte_repository
from src.api.exceptions import NotFoundError
from src.api.v1.schemas.cte_schemas import CreateCteRequest
from src.api.v1.serializers.cte_serializer import cte_to_response
from src.domain.cte.home import CteHome
from src.domain.cte.repository import CteRepository

router = APIRouter()


@router.get("/ctes")
async def list_ctes(
    repo: CteRepository = Depends(get_cte_repository),
):
    entities = repo.find_all()
    return [cte_to_response(e) for e in entities]


@router.get("/ctes/{id}")
async def get_cte(
    id: UUID,
    repo: CteRepository = Depends(get_cte_repository),
):
    entity = repo.find_by_id(id)
    if entity is None:
        raise NotFoundError(f"Cte {id} not found")
    return cte_to_response(entity)


@router.post("/ctes", status_code=201)
async def create_cte(
    request: CreateCteRequest,
    repo: CteRepository = Depends(get_cte_repository),
):
    entity = CteHome.create(name=request.name)
    repo.save(entity)
    return cte_to_response(entity)
