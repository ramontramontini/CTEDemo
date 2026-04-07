"""Cte entity — CT-e document aggregate root."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from src.domain.cte.enums import CteStatus


class Cte:
    """CT-e document aggregate root."""

    def __init__(
        self,
        id: UUID,
        access_key: str,
        freight_order_number: str,
        status: CteStatus,
        xml: str,
        original_payload: dict[str, Any],
        created_at: datetime,
    ):
        self._id = id
        self._access_key = access_key
        self._freight_order_number = freight_order_number
        self._status = status
        self._xml = xml
        self._original_payload = original_payload
        self._created_at = created_at

    @classmethod
    def _create_raw(
        cls,
        access_key: str,
        freight_order_number: str,
        status: CteStatus,
        xml: str,
        original_payload: dict[str, Any],
    ) -> "Cte":
        return cls(
            id=uuid4(),
            access_key=access_key,
            freight_order_number=freight_order_number,
            status=status,
            xml=xml,
            original_payload=original_payload,
            created_at=datetime.now(timezone.utc),
        )

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def access_key(self) -> str:
        return self._access_key

    @property
    def freight_order_number(self) -> str:
        return self._freight_order_number

    @property
    def status(self) -> CteStatus:
        return self._status

    @property
    def xml(self) -> str:
        return self._xml

    @property
    def original_payload(self) -> dict[str, Any]:
        return self._original_payload

    @property
    def created_at(self) -> datetime:
        return self._created_at

    def is_gerado(self) -> bool:
        """Whether this CT-e was successfully generated."""
        return self._status == CteStatus.GERADO

    def formatted_access_key(self) -> str:
        """Format 44-digit access key with readable separators.

        Format: UF AAMM CNPJ MOD SERIE NUMERO TIPO CODIGO DV
        """
        k = self._access_key
        if len(k) != 44:
            return k
        return (
            f"{k[:2]} {k[2:6]} {k[6:20]} {k[20:22]} "
            f"{k[22:25]} {k[25:34]} {k[34:35]} {k[35:43]} {k[43]}"
        )

    def __repr__(self) -> str:
        return (
            f"Cte(id={self._id}, "
            f"freight_order={self._freight_order_number!r}, "
            f"status={self._status})"
        )
