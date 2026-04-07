"""Cte domain errors."""


class CteNotFoundError(Exception):
    """Raised when a Cte cannot be found."""

    def __init__(self, identifier: str):
        self.identifier = identifier
        super().__init__(f"Cte not found: {identifier}")


class CteValidationError(Exception):
    """Raised when Cte data is invalid."""

    def __init__(self, message: str):
        super().__init__(message)
