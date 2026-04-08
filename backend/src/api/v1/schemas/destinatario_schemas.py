"""Destinatario request/response schemas."""

from pydantic import BaseModel


class CreateDestinatarioRequest(BaseModel):
    cnpj: str = ""
    cpf: str = ""
    razao_social: str
    nome_fantasia: str = ""
    ie: str = ""
    uf: str
    cidade: str
    logradouro: str
    numero: str
    bairro: str
    cep: str


class UpdateDestinatarioRequest(BaseModel):
    razao_social: str | None = None
    nome_fantasia: str | None = None
    ie: str | None = None
    uf: str | None = None
    cidade: str | None = None
    logradouro: str | None = None
    numero: str | None = None
    bairro: str | None = None
    cep: str | None = None
