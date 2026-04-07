"""Transportadora Home — factory + lifecycle management."""

from datetime import datetime, timezone
from uuid import uuid4

from src.domain.transportadora.entity import Transportadora
from src.domain.transportadora.enums import TransportadoraStatus


class TransportadoraHome:
    """Factory and lifecycle manager for Transportadora aggregate."""

    @staticmethod
    def create(name: str) -> Transportadora:
        """Create a new Transportadora instance."""
        if not name or not name.strip():
            raise ValueError("Name is required")
        return Transportadora(
            id=uuid4(),
            name=name.strip(),
            status=TransportadoraStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
        )
