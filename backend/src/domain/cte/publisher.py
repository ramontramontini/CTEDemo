"""CtePublisher — abstract port for CT-e event publishing."""

from abc import ABC, abstractmethod
from typing import Any


class CtePublisher(ABC):
    """Abstract port for publishing CT-e generation events."""

    @abstractmethod
    def publish(
        self,
        freight_order_number: str,
        access_key: str,
        payload: dict[str, Any],
    ) -> None:
        """Publish a CT-e generation event. Fire-and-forget."""
