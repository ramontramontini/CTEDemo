"""CteGenerationService — cross-aggregate orchestration for CT-e generation."""

from typing import Any

from src.domain.cte.entity import Cte
from src.domain.cte.home import CteHome
from src.domain.transportadora.entity import Transportadora
from src.domain.transportadora.repository import TransportadoraRepository


class CteGenerationService:
    """Orchestrates Transportadora lookup + CT-e generation.

    Cross-aggregate service per L1 §Cross-Aggregate Orchestration:
    - Looks up Transportadora by Carrier CNPJ
    - Validates carrier exists
    - Delegates generation to CteHome with Transportadora entity
    """

    def __init__(self, transportadora_repo: TransportadoraRepository) -> None:
        self._transportadora_repo = transportadora_repo

    def generate(self, payload: dict[str, Any]) -> Cte:
        """Generate a CT-e after validating the carrier exists."""
        carrier_cnpj = payload.get("Carrier", "")
        transportadora = self.lookup_carrier(carrier_cnpj)
        return CteHome.generate(payload, transportadora)

    def generate_with_carrier(
        self, payload: dict[str, Any], transportadora: Transportadora
    ) -> Cte:
        """Generate a CT-e with an already-looked-up Transportadora."""
        return CteHome.generate(payload, transportadora)

    def lookup_carrier(self, cnpj: str) -> Transportadora:
        """Look up Transportadora by CNPJ. Raises ValueError if not found."""
        transportadora = self._transportadora_repo.find_by_cnpj(cnpj)
        if transportadora is None:
            raise ValueError(f"Transportadora not found for CNPJ {cnpj}")
        return transportadora
