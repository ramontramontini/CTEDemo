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
