"""Cte API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from src.api.dependencies import (
    get_cte_repository,
    get_destinatario_repository,
    get_nfe_repository,
    get_remetente_repository,
    get_transportadora_repository,
)
from src.api.exceptions import NotFoundError
from src.api.v1.schemas.cte_schemas import GenerateCteRequest
from src.api.v1.serializers.cte_serializer import cte_to_response
from src.domain.cte.cfop_validator import CfopGeographicValidator
from src.domain.cte.repository import CteRepository
from src.domain.destinatario.repository import DestinatarioRepository
from src.domain.nfe.repository import NfeRepository
from src.domain.remetente.repository import RemetenteRepository
from src.domain.services.cte_generation_service import CteGenerationService
from src.domain.services.nfe_validation_service import NfeValidationService
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
    remetente_repo: RemetenteRepository = Depends(get_remetente_repository),
    nfe_repo: NfeRepository = Depends(get_nfe_repository),
):
    payload = request.model_dump()

    service = CteGenerationService(transportadora_repo, remetente_repo, destinatario_repo)
    try:
        transportadora = service.lookup_carrier(payload.get("Carrier", ""))
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "type": "about:blank",
                "title": "Bad Request",
                "status": 400,
                "detail": str(e),
            },
        )

    nfe_warnings = _validate_nfe_keys(payload, nfe_repo)
    if isinstance(nfe_warnings, JSONResponse):
        return nfe_warnings

    geo_errors = _validate_cfop_geography_with_entity(
        payload, transportadora, destinatario_repo
    )
    if geo_errors:
        errors = _parse_validation_errors("\n".join(geo_errors))
        return JSONResponse(status_code=422, content={"detail": errors})

    remetente = remetente_repo.find_by_cnpj(payload.get("CNPJ_Origin", "")) if payload.get("CNPJ_Origin") else None
    destinatario = destinatario_repo.find_by_cnpj(payload.get("CNPJ_Dest", "")) if payload.get("CNPJ_Dest") else None

    try:
        entity = service.generate_with_carrier(payload, transportadora, remetente, destinatario)
    except ValueError as e:
        errors = _parse_validation_errors(str(e))
        return JSONResponse(status_code=422, content={"detail": errors})
    repo.save(entity)
    return cte_to_response(entity, warnings=nfe_warnings)


def _validate_nfe_keys(payload: dict, nfe_repo: NfeRepository) -> list[str] | JSONResponse:
    """Validate all NF-e keys across all folders. Returns warnings list or 400 JSONResponse."""
    all_nfe_keys: list[str] = []
    for folder in payload.get("Folder", []):
        all_nfe_keys.extend(folder.get("RelatedNFE", []))

    if not all_nfe_keys:
        return []

    nfe_service = NfeValidationService(nfe_repo)
    try:
        return nfe_service.validate_keys(all_nfe_keys, payload.get("CNPJ_Origin", ""))
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "type": "about:blank",
                "title": "Bad Request",
                "status": 400,
                "detail": str(e),
            },
        )


def _validate_cfop_geography_with_entity(
    payload: dict,
    transportadora: "Transportadora",
    destinatario_repo: DestinatarioRepository,
) -> list[str]:
    """Validate CFOP geographic rules using already-looked-up Transportadora."""
    cnpj_dest = payload.get("CNPJ_Dest")
    if not cnpj_dest:
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
