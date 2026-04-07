"""Remetente domain errors."""


class RemetenteNotFoundError(Exception):
    """Raised when a Remetente cannot be found."""

    def __init__(self, identifier: str):
        self.identifier = identifier
        super().__init__(f"Remetente not found: {identifier}")


class RemetenteValidationError(Exception):
    """Raised when Remetente data is invalid."""

    def __init__(self, message: str):
        super().__init__(message)


class DuplicateCnpjError(Exception):
    """Raised when a Remetente with the same CNPJ already exists."""

    def __init__(self, cnpj: str):
        self.cnpj = cnpj
        super().__init__(f"CNPJ already registered: {cnpj}")
