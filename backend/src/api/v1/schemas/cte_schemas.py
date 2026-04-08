"""Cte request/response schemas."""

from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class GenerateCteRequest(BaseModel):
    """Freight order input payload for CT-e generation."""

    model_config = ConfigDict(extra="forbid")

    FreightOrder: str = ""
    ERP: str = ""
    Carrier: str = ""
    CNPJ_Origin: str = ""
    CNPJ_Dest: str = ""
    Incoterms: str = ""
    OperationType: str = ""
    Folder: list[dict[str, Any]] = []
    BusinessTransactionDocument: str = ""
    BusinessTransactionDocType: str = ""
    Issuer: str = ""
    DocumentType: str = ""
    FleetType: str = ""
    TransportType: str = ""

    @field_validator("Incoterms")
    @classmethod
    def validate_incoterms(cls, v: str) -> str:
        if v and v not in ("CIF", "FOB"):
            raise ValueError(f"Incoterms inválido '{v}' — valores aceitos: CIF, FOB")
        return v

    @field_validator("OperationType")
    @classmethod
    def validate_operation_type(cls, v: str) -> str:
        if v and v not in ("0", "1", "2", "3"):
            raise ValueError(
                f"OperationType inválido '{v}' — valores aceitos: 0, 1, 2, 3"
            )
        return v
