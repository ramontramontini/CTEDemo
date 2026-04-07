"""Cte request/response schemas."""

from typing import Any

from pydantic import BaseModel


class GenerateCteRequest(BaseModel):
    """Freight order input payload for CT-e generation."""
    FreightOrder: str = ""
    ERP: str = ""
    Carrier: str = ""
    CNPJ_Origin: str = ""
    Incoterms: str = ""
    OperationType: str = ""
    Folder: list[dict[str, Any]] = []
