"""Cte API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from src.api.dependencies import (
    get_cte_repository,
    get_destinatario_repository,
    get_transportadora_repository,
)
from src.api.exceptions import NotFoundError
from src.api.v1.schemas.cte_schemas import GenerateCteRequest
from src.api.v1.serializers.cte_serializer import cte_to_response
from src.domain.cte.cfop_validator import CfopGeographicValidator
from src.domain.cte.home import CteHome
from src.domain.cte.repository import CteRepository
from src.domain.destinatario.repository import DestinatarioRepository
from src.domain.transportadora.repository import TransportadoraRepository

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
    transportadora_repo: TransportadoraRepository = Depends(get_transportadora_repository),
    destinatario_repo: DestinatarioRepository = Depends(get_destinatario_repository),
):
    payload = request.model_dump()

    geo_errors = _validate_cfop_geography(payload, transportadora_repo, destinatario_repo)
    if geo_errors:
        errors = _parse_validation_errors("\n".join(geo_errors))
        return JSONResponse(status_code=422, content={"detail": errors})

    try:
        entity = CteHome.generate(payload)
    except ValueError as e:
        errors = _parse_validation_errors(str(e))
        return JSONResponse(status_code=422, content={"detail": errors})
    repo.save(entity)
    return cte_to_response(entity)


def _validate_cfop_geography(
    payload: dict,
    transportadora_repo: TransportadoraRepository,
    destinatario_repo: DestinatarioRepository,
) -> list[str]:
    """Resolve UFs from entities and validate CFOP geographic rules."""
    carrier_cnpj = payload.get("Carrier")
    cnpj_dest = payload.get("CNPJ_Dest")

    if not carrier_cnpj or not cnpj_dest:
        return []

    transportadora = transportadora_repo.find_by_cnpj(carrier_cnpj)
    if not transportadora:
        return []

    destinatario = destinatario_repo.find_by_cnpj(cnpj_dest)
    if not destinatario:
        return []

    folders = payload.get("Folder", [])
    return CfopGeographicValidator.validate(transportadora.uf, destinatario.uf, folders)


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
