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


class DuplicateFreightOrderError(Exception):
    """Raised when a CT-e with the same FreightOrder already exists."""

    def __init__(self, freight_order: str):
        self.freight_order = freight_order
        super().__init__(f"Freight order '{freight_order}' already exists")


class CteXmlBuildError(Exception):
    """Raised when generated CT-e XML is not well-formed."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"CT-e XML malformado: {reason}")
