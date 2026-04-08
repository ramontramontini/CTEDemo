"""MemoryCtePublisher — in-memory Fila mock for CT-e events."""

from datetime import datetime, timezone
from typing import Any

from src.domain.cte.publisher import CtePublisher


class MemoryCtePublisher(CtePublisher):
    """In-memory publisher that records events for testing."""

    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []

    def publish(
        self,
        freight_order_number: str,
        access_key: str,
        payload: dict[str, Any],
    ) -> None:
        self._events.append({
            "freight_order_number": freight_order_number,
            "access_key": access_key,
            "payload": payload,
            "published_at": datetime.now(timezone.utc),
        })

    def published_events(self) -> list[dict[str, Any]]:
        return list(self._events)
