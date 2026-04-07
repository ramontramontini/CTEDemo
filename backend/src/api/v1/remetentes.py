"""Remetente API endpoints."""

import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response

from src.api.dependencies import get_remetente_repository
from src.api.v1.schemas.remetente_schemas import CreateRemetenteRequest, UpdateRemetenteRequest
from src.api.v1.serializers.remetente_serializer import remetente_to_response
from src.domain.remetente.errors import DuplicateCnpjError, RemetenteNotFoundError
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
        raise RemetenteNotFoundError(str(id))
    return remetente_to_response(entity)


@router.post("/remetentes", status_code=201)
async def create_remetente(
    request: CreateRemetenteRequest,
    repo: RemetenteRepository = Depends(get_remetente_repository),
):
    cnpj_clean = re.sub(r"\D", "", request.cnpj)
    existing = repo.find_by_cnpj(cnpj_clean)
    if existing is not None:
        raise DuplicateCnpjError(cnpj_clean)

    try:
        entity = RemetenteHome.create(
            cnpj=request.cnpj,
            razao_social=request.razao_social,
            nome_fantasia=request.nome_fantasia,
            ie=request.ie,
            uf=request.uf,
            cidade=request.cidade,
            logradouro=request.logradouro,
            numero=request.numero,
            bairro=request.bairro,
            cep=request.cep,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    repo.save(entity)
    return remetente_to_response(entity)


@router.patch("/remetentes/{id}")
async def update_remetente(
    id: UUID,
    request: UpdateRemetenteRequest,
    repo: RemetenteRepository = Depends(get_remetente_repository),
):
    entity = repo.find_by_id(id)
    if entity is None:
        raise RemetenteNotFoundError(str(id))

    if request.razao_social is not None:
        entity.update_razao_social(request.razao_social)

    has_endereco_update = any(
        getattr(request, f) is not None
        for f in ("uf", "cidade", "logradouro", "numero", "bairro", "cep")
    )
    if has_endereco_update:
        entity.update_endereco(
            uf=request.uf if request.uf is not None else entity.uf,
            cidade=request.cidade if request.cidade is not None else entity.cidade,
            logradouro=request.logradouro if request.logradouro is not None else entity.logradouro,
            numero=request.numero if request.numero is not None else entity.numero,
            bairro=request.bairro if request.bairro is not None else entity.bairro,
            cep=request.cep if request.cep is not None else entity.cep,
        )

    if request.nome_fantasia is not None:
        entity.update_nome_fantasia(request.nome_fantasia)

    if request.ie is not None:
        entity.update_ie(request.ie)

    repo.save(entity)
    return remetente_to_response(entity)


@router.delete("/remetentes/{id}", status_code=204)
async def delete_remetente(
    id: UUID,
    repo: RemetenteRepository = Depends(get_remetente_repository),
):
    deleted = repo.delete(id)
    if not deleted:
        raise RemetenteNotFoundError(str(id))
    return Response(status_code=204)
