"""Remetente Home — factory + lifecycle management."""

from datetime import datetime, timezone
from uuid import uuid4

from src.domain.remetente.entity import Remetente
from src.domain.remetente.enums import RemetenteStatus


class RemetenteHome:
    """Factory and lifecycle manager for Remetente aggregate."""

    @staticmethod
    def create(name: str) -> Remetente:
        """Create a new Remetente instance."""
        if not name or not name.strip():
            raise ValueError("Name is required")
        return Remetente(
            id=uuid4(),
            name=name.strip(),
            status=RemetenteStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
        )
