"""Transportadora domain errors."""


class TransportadoraNotFoundError(Exception):
    """Raised when a Transportadora cannot be found."""

    def __init__(self, identifier: str):
        self.identifier = identifier
        super().__init__(f"Transportadora not found: {identifier}")


class TransportadoraValidationError(Exception):
    """Raised when Transportadora data is invalid."""

    def __init__(self, message: str):
        super().__init__(message)


