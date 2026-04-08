"""Cte API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from src.api.dependencies import get_cte_repository
from src.api.exceptions import NotFoundError
from src.api.v1.schemas.cte_schemas import GenerateCteRequest
from src.api.v1.serializers.cte_serializer import cte_to_response
from src.domain.cte.home import CteHome
from src.domain.cte.repository import CteRepository

router = APIRouter()


@router.get("/cte")
async def list_ctes(
    repo: CteRepository = Depends(get_cte_repository),
):
    entities = repo.find_all()
    return [cte_to_response(e) for e in entities]


@router.get("/cte/{id_or_freight_order}")
async def get_cte(
    id_or_freight_order: str,
    repo: CteRepository = Depends(get_cte_repository),
):
    try:
        cte_id = UUID(id_or_freight_order)
        entity = repo.find_by_id(cte_id)
    except ValueError:
        entity = repo.find_by_freight_order_number(id_or_freight_order)
    if entity is None:
        raise NotFoundError(f"Cte {id_or_freight_order} not found")
    return cte_to_response(entity)


@router.post("/cte", status_code=201)
async def generate_cte(
    request: GenerateCteRequest,
    repo: CteRepository = Depends(get_cte_repository),
):
    payload = request.model_dump()
    try:
        entity = CteHome.generate(payload)
    except ValueError as e:
        errors = _parse_validation_errors(str(e))
        return JSONResponse(status_code=422, content={"detail": errors})
    repo.save(entity)
    return cte_to_response(entity)


def _parse_validation_errors(error_message: str) -> list[dict[str, str]]:
    """Parse multi-line validation errors into field-level error list."""
    lines = error_message.strip().split("\n")
    errors = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if "—" in line:
            parts = line.split("—", 1)
            field = parts[0].strip().rstrip(" .")
            message = line
        elif ":" in line:
            parts = line.split(":", 1)
            field = parts[0].strip()
            message = line
        else:
            field = "general"
            message = line
        # Clean field path: extract the dotted path
        field = field.split(".")[-1] if "." not in field else field
        errors.append({"field": field, "message": message})
    return errors
