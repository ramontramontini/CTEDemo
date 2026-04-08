"""CteGenerationService — cross-aggregate orchestration for CT-e generation."""

from typing import Any, Optional

from src.domain.cte.entity import Cte
from src.domain.cte.home import CteHome
from src.domain.destinatario.entity import Destinatario
from src.domain.destinatario.repository import DestinatarioRepository
from src.domain.remetente.entity import Remetente
from src.domain.remetente.repository import RemetenteRepository
from src.domain.transportadora.entity import Transportadora
from src.domain.transportadora.repository import TransportadoraRepository


class CteGenerationService:
    """Orchestrates Transportadora/Remetente/Destinatario lookup + CT-e generation.

    Cross-aggregate service per L1 §Cross-Aggregate Orchestration:
    - Looks up Transportadora by Carrier CNPJ (mandatory)
    - Looks up Remetente by CNPJ_Origin (optional — graceful degradation)
    - Looks up Destinatario by CNPJ_Dest (optional — graceful degradation)
    - Delegates generation to CteHome with all resolved entities
    """

    def __init__(
        self,
        transportadora_repo: TransportadoraRepository,
        remetente_repo: Optional[RemetenteRepository] = None,
        destinatario_repo: Optional[DestinatarioRepository] = None,
    ) -> None:
        self._transportadora_repo = transportadora_repo
        self._remetente_repo = remetente_repo
        self._destinatario_repo = destinatario_repo

    def generate(self, payload: dict[str, Any]) -> Cte:
        """Generate a CT-e after resolving all related entities."""
        carrier_cnpj = payload.get("Carrier", "")
        transportadora = self.lookup_carrier(carrier_cnpj)

        remetente = self._lookup_remetente(payload.get("CNPJ_Origin", ""))
        destinatario = self._lookup_destinatario(payload.get("CNPJ_Dest", ""))

        return CteHome.generate(payload, transportadora, remetente, destinatario)

    def generate_with_carrier(
        self,
        payload: dict[str, Any],
        transportadora: Transportadora,
        remetente: Optional[Remetente] = None,
        destinatario: Optional[Destinatario] = None,
    ) -> Cte:
        """Generate a CT-e with already-looked-up entities."""
        return CteHome.generate(payload, transportadora, remetente, destinatario)

    def lookup_carrier(self, cnpj: str) -> Transportadora:
        """Look up Transportadora by CNPJ. Raises ValueError if not found."""
        transportadora = self._transportadora_repo.find_by_cnpj(cnpj)
        if transportadora is None:
            raise ValueError(f"Transportadora not found for CNPJ {cnpj}")
        return transportadora

    def _lookup_remetente(self, cnpj: str) -> Optional[Remetente]:
        """Look up Remetente by CNPJ. Returns None if not found or no repo."""
        if not cnpj or self._remetente_repo is None:
            return None
        return self._remetente_repo.find_by_cnpj(cnpj)

    def _lookup_destinatario(self, cnpj: str) -> Optional[Destinatario]:
        """Look up Destinatario by CNPJ. Returns None if not found or no repo."""
        if not cnpj or self._destinatario_repo is None:
            return None
        return self._destinatario_repo.find_by_cnpj(cnpj)
