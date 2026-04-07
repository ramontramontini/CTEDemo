"""Transportadora request/response schemas."""

from pydantic import BaseModel


class CreateTransportadoraRequest(BaseModel):
    name: str


class UpdateTransportadoraRequest(BaseModel):
    name: str | None = None
