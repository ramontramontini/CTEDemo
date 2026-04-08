"""NF-e validation service — validates related NF-e keys against mock repository."""

from src.domain.nfe.repository import NfeRepository


class NfeValidationService:
    """Validates NF-e keys exist and are authorized. Returns CNPJ divergence warnings."""

    def __init__(self, nfe_repo: NfeRepository) -> None:
        self._nfe_repo = nfe_repo

    def validate_keys(self, nfe_keys: list[str], cnpj_origin: str) -> list[str]:
        """Validate NF-e keys. Returns list of warnings. Raises ValueError on hard errors."""
        warnings: list[str] = []
        for key in nfe_keys:
            nfe = self._nfe_repo.find_by_key(key)
            if nfe is None:
                raise ValueError(f"NF-e not found: {key}")
            if nfe.status == "canceled":
                raise ValueError(f"NF-e canceled: {key}")
            if nfe.emitter_cnpj != cnpj_origin:
                warnings.append(
                    f"NF-e emitter CNPJ {nfe.emitter_cnpj} differs from CNPJ_Origin {cnpj_origin}"
                )
        return warnings
