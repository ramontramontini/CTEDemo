"""Cte API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from src.api.dependencies import get_cte_repository
from src.api.exceptions import NotFoundError, problem_detail_response
from src.api.v1.schemas.cte_schemas import GenerateCteRequest
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


@router.post("/ctes/generate", status_code=201)
async def generate_cte(
    request: GenerateCteRequest,
    repo: CteRepository = Depends(get_cte_repository),
):
    payload = request.model_dump()
    try:
        entity = CteHome.generate(payload)
    except ValueError as e:
        errors = _parse_validation_errors(str(e))
        detail = "; ".join(f"{k}: {v}" for k, v in errors.items())
        return problem_detail_response(422, detail, errors=errors)
    repo.save(entity)
    return cte_to_response(entity)


def _parse_validation_errors(error_message: str) -> dict[str, str]:
    """Parse multi-line validation errors into field→message dict."""
    lines = error_message.strip().split("\n")
    errors: dict[str, str] = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if "—" in line:
            parts = line.split("—", 1)
            field = parts[0].strip().rstrip(" .")
        elif ":" in line:
            parts = line.split(":", 1)
            field = parts[0].strip()
        else:
            field = "general"
        field = field if "." in field else field.split(".")[-1]
        errors[field] = line
    return errors
