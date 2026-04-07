"""Transportadora entity — data + behavior + invariants."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from src.domain.transportadora.enums import TransportadoraStatus


class Transportadora:
    """Transportadora aggregate root."""

    def __init__(
        self,
        id: UUID,
        name: str,
        status: TransportadoraStatus,
        created_at: datetime,
        updated_at: Optional[datetime] = None,
    ):
        self._id = id
        self._name = name
        self._status = status
        self._created_at = created_at
        self._updated_at = updated_at

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def status(self) -> TransportadoraStatus:
        return self._status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> Optional[datetime]:
        return self._updated_at

    def update_name(self, new_name: str) -> None:
        if not new_name or not new_name.strip():
            raise ValueError("Name cannot be empty")
        self._name = new_name.strip()
        self._updated_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return f"Transportadora(id={self._id}, name={self._name!r}, status={self._status})"
