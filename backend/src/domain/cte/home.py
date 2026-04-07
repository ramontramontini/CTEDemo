"""Cte Home — factory + lifecycle management."""

from datetime import datetime, timezone
from uuid import uuid4

from src.domain.cte.entity import Cte
from src.domain.cte.enums import CteStatus


class CteHome:
    """Factory and lifecycle manager for Cte aggregate."""

    @staticmethod
    def create(name: str) -> Cte:
        """Create a new Cte instance."""
        if not name or not name.strip():
            raise ValueError("Name is required")
        return Cte(
            id=uuid4(),
            name=name.strip(),
            status=CteStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
        )
