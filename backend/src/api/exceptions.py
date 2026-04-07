"""Base API exception classes."""


class APIException(Exception):
    """Base exception for API errors."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class NotFoundError(APIException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail)


class ValidationError(APIException):
    def __init__(self, detail: str = "Validation error"):
        super().__init__(status_code=422, detail=detail)
