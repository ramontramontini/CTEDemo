"""Base API exception classes and RFC 9110 Problem Details helpers."""

from typing import Optional

from fastapi.responses import JSONResponse


# RFC 9110 status code to title mapping
_STATUS_TITLES = {
    400: "Bad Request",
    404: "Not Found",
    409: "Conflict",
    422: "Unprocessable Entity",
    500: "Internal Server Error",
}

RFC_9110_TYPE = "https://tools.ietf.org/html/rfc9110#section-15.5.1"


def problem_detail_response(
    status: int,
    detail: str,
    errors: Optional[dict[str, str]] = None,
) -> JSONResponse:
    """Return a RFC 9110 Problem Details JSON response."""
    body: dict = {
        "type": RFC_9110_TYPE,
        "title": _STATUS_TITLES.get(status, "Error"),
        "status": status,
        "detail": detail,
    }
    if errors is not None:
        body["errors"] = errors
    return JSONResponse(
        status_code=status,
        content=body,
        media_type="application/problem+json",
    )


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
