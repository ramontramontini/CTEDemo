"""Destinatario request/response schemas."""

from pydantic import BaseModel


class CreateDestinatarioRequest(BaseModel):
    name: str


class UpdateDestinatarioRequest(BaseModel):
    name: str | None = None
