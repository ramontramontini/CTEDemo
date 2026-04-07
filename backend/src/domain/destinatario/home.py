"""Destinatario Home — factory + lifecycle management."""

from datetime import datetime, timezone
from uuid import uuid4

from src.domain.destinatario.entity import Destinatario
from src.domain.destinatario.enums import DestinatarioStatus


class DestinatarioHome:
    """Factory and lifecycle manager for Destinatario aggregate."""

    @staticmethod
    def create(name: str) -> Destinatario:
        """Create a new Destinatario instance."""
        if not name or not name.strip():
            raise ValueError("Name is required")
        return Destinatario(
            id=uuid4(),
            name=name.strip(),
            status=DestinatarioStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
        )
