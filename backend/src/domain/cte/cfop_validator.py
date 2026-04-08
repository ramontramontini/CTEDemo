"""CFOP geographic validation — validates CFOP prefix against origin/destination UF."""

from typing import Any


class CfopGeographicValidator:
    """Validates CFOP codes against origin/destination state (UF).

    Rules:
    - 5xxx: origin and destination must be same UF (intrastate)
    - 6xxx: origin and destination must be different UFs (interstate)
    - 7xxx: UF check skipped (international/export)
    """

    @staticmethod
    def validate(origin_uf: str, dest_uf: str, folders: list[dict[str, Any]]) -> list[str]:
        """Validate CFOP geographic rules per folder.

        Returns list of error messages (empty if all valid).
        """
        errors: list[str] = []
        same_state = origin_uf.upper() == dest_uf.upper()

        for index, folder in enumerate(folders):
            cfop = folder.get("CFOP", "")
            if not cfop:
                continue

            prefix = cfop[0]

            if prefix == "7":
                continue

            if prefix == "5" and not same_state:
                errors.append(
                    f"Folder[{index}].CFOP {cfop} requer mesmo estado. "
                    f"Origem: {origin_uf}, Destino: {dest_uf}"
                )
            elif prefix == "6" and same_state:
                errors.append(
                    f"Folder[{index}].CFOP {cfop} requer estados diferentes. "
                    f"Origem: {origin_uf}, Destino: {dest_uf}"
                )

        return errors
