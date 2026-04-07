"""Remetente request/response schemas."""

from pydantic import BaseModel


class CreateRemetenteRequest(BaseModel):
    name: str


class UpdateRemetenteRequest(BaseModel):
    name: str | None = None
