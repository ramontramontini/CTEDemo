"""Transportadora API endpoints — full CRUD."""

import re
from uuid import UUID

from fastapi import APIRouter, Depends, Response

from src.api.dependencies import get_transportadora_repository
from src.api.exceptions import NotFoundError, ValidationError
from src.api.v1.schemas.transportadora_schemas import (
    CreateTransportadoraRequest,
    UpdateTransportadoraRequest,
)
from src.api.v1.serializers.transportadora_serializer import transportadora_to_response
from src.domain.transportadora.errors import TransportadoraValidationError
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
    try:
        entity = TransportadoraHome.create(
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
    except TransportadoraValidationError as e:
        raise ValidationError(str(e))

    existing = repo.find_by_cnpj(entity.cnpj)
    if existing is not None:
        raise ValidationError(f"CNPJ ja cadastrado: {entity.cnpj}")

    repo.save(entity)
    return transportadora_to_response(entity)


@router.patch("/transportadoras/{id}")
async def update_transportadora(
    id: UUID,
    request: UpdateTransportadoraRequest,
    repo: TransportadoraRepository = Depends(get_transportadora_repository),
):
    entity = repo.find_by_id(id)
    if entity is None:
        raise NotFoundError(f"Transportadora {id} not found")

    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    if updates:
        if "cnpj" in updates:
            stripped = re.sub(r"[.\-/]", "", updates["cnpj"])
            existing = repo.find_by_cnpj(stripped)
            if existing is not None and existing.id != entity.id:
                raise ValidationError(f"CNPJ ja cadastrado: {stripped}")
        try:
            entity.update(**updates)
        except ValueError as e:
            raise ValidationError(str(e))
        repo.save(entity)

    return transportadora_to_response(entity)


@router.delete("/transportadoras/{id}", status_code=204)
async def delete_transportadora(
    id: UUID,
    repo: TransportadoraRepository = Depends(get_transportadora_repository),
):
    deleted = repo.delete(id)
    if not deleted:
        raise NotFoundError(f"Transportadora {id} not found")
    return Response(status_code=204)
