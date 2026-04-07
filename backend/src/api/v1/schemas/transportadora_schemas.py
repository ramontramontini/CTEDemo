"""Transportadora request/response schemas."""

from pydantic import BaseModel, Field


class CreateTransportadoraRequest(BaseModel):
    cnpj: str
    razao_social: str = Field(max_length=150)
    nome_fantasia: str = ""
    ie: str = ""
    uf: str = Field(min_length=2, max_length=2)
    cidade: str
    logradouro: str
    numero: str
    bairro: str
    cep: str = Field(min_length=8, max_length=8)


class UpdateTransportadoraRequest(BaseModel):
    cnpj: str | None = None
    razao_social: str | None = Field(default=None, max_length=150)
    nome_fantasia: str | None = None
    ie: str | None = None
    uf: str | None = Field(default=None, min_length=2, max_length=2)
    cidade: str | None = None
    logradouro: str | None = None
    numero: str | None = None
    bairro: str | None = None
    cep: str | None = Field(default=None, min_length=8, max_length=8)
