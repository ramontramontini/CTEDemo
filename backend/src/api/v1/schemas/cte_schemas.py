"""Cte request/response schemas."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class GenerateCteRequest(BaseModel):
    """Freight order input payload for CT-e generation."""

    model_config = ConfigDict(extra="allow")

    FreightOrder: str = ""
    ERP: str = ""
    Carrier: str = ""
    CNPJ_Origin: str = ""
    Incoterms: str = ""
    OperationType: str = ""
    Folder: list[dict[str, Any]] = []
    BusinessTransactionDocument: str = ""
    BusinessTransactionDocType: str = ""
    Issuer: str = ""
    DocumentType: str = ""
    FleetType: str = ""
    TransportType: str = ""
