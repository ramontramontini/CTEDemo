"""Cte request/response schemas."""

from pydantic import BaseModel


class CreateCteRequest(BaseModel):
    name: str


class UpdateCteRequest(BaseModel):
    name: str | None = None
