"""Destinatario API endpoints."""

import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response

from src.api.dependencies import get_destinatario_repository
from src.api.v1.schemas.destinatario_schemas import CreateDestinatarioRequest, UpdateDestinatarioRequest
from src.api.v1.serializers.destinatario_serializer import destinatario_to_response
from src.domain.destinatario.errors import DestinatarioNotFoundError, DuplicateCnpjError
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
        raise DestinatarioNotFoundError(str(id))
    return destinatario_to_response(entity)


@router.post("/destinatarios", status_code=201)
async def create_destinatario(
    request: CreateDestinatarioRequest,
    repo: DestinatarioRepository = Depends(get_destinatario_repository),
):
    if request.cnpj:
        cnpj_clean = re.sub(r"\D", "", request.cnpj)
        existing = repo.find_by_cnpj(cnpj_clean)
        if existing is not None:
            raise DuplicateCnpjError(cnpj_clean)

    try:
        entity = DestinatarioHome.create(
            cnpj=request.cnpj,
            cpf=request.cpf,
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
    return destinatario_to_response(entity)


@router.patch("/destinatarios/{id}")
async def update_destinatario(
    id: UUID,
    request: UpdateDestinatarioRequest,
    repo: DestinatarioRepository = Depends(get_destinatario_repository),
):
    entity = repo.find_by_id(id)
    if entity is None:
        raise DestinatarioNotFoundError(str(id))

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
    return destinatario_to_response(entity)


@router.delete("/destinatarios/{id}", status_code=204)
async def delete_destinatario(
    id: UUID,
    repo: DestinatarioRepository = Depends(get_destinatario_repository),
):
    deleted = repo.delete(id)
    if not deleted:
        raise DestinatarioNotFoundError(str(id))
    return Response(status_code=204)
