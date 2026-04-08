"""Destinatario domain errors."""


class DestinatarioNotFoundError(Exception):
    """Raised when a Destinatario cannot be found."""

    def __init__(self, identifier: str):
        self.identifier = identifier
        super().__init__(f"Destinatario not found: {identifier}")


class DestinatarioValidationError(Exception):
    """Raised when Destinatario data is invalid."""

    def __init__(self, message: str):
        super().__init__(message)


class DuplicateCnpjError(Exception):
    """Raised when a Destinatario with the same CNPJ already exists."""

    def __init__(self, cnpj: str):
        self.cnpj = cnpj
        super().__init__(f"CNPJ already registered: {cnpj}")
