"""Cte Home — factory + CT-e generation."""

import random
import threading
from datetime import datetime, timezone
from typing import Any

from src.domain.cte.entity import Cte
from src.domain.cte.enums import CteStatus
from src.domain.cte.value_objects import AccessKey, FreightOrder
from src.domain.cte.xml_builder import build_cte_xml
from src.domain.transportadora.entity import Transportadora


class _SequenceCounter:
    """Thread-safe in-memory sequential counter per série."""

    def __init__(self) -> None:
        self._counters: dict[str, int] = {}
        self._lock = threading.Lock()

    def next(self, serie: str) -> int:
        with self._lock:
            current = self._counters.get(serie, 0) + 1
            if current > 999999999:
                current = 1
            self._counters[serie] = current
            return current


_sequence = _SequenceCounter()

UF = "26"
SERIE = "020"


class CteHome:
    """Factory and lifecycle manager for CT-e generation."""

    @staticmethod
    def generate(payload: dict[str, Any], transportadora: Transportadora) -> Cte:
        """Generate a CT-e from a freight order payload.

        Args:
            payload: Raw freight order dict from API request.
            transportadora: Looked-up Transportadora entity for XML enrichment.
        """
        freight_order = FreightOrder.from_dict(payload)

        now = datetime.now(timezone.utc)
        aamm = now.strftime("%y%m")
        numero = _sequence.next(SERIE)
        codigo = str(random.randint(0, 99999999)).zfill(8)

        access_key = AccessKey.generate(
            uf=UF,
            aamm=aamm,
            cnpj=freight_order.carrier,
            serie=SERIE,
            numero=numero,
            codigo=codigo,
        )

        xml = build_cte_xml(freight_order, access_key, now, transportadora)

        return Cte._create_raw(
            access_key=access_key.value,
            freight_order_number=freight_order.freight_order,
            status=CteStatus.GERADO,
            xml=xml,
            original_payload=payload,
        )
