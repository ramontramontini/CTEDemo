"""Centralized domain-to-HTTP error mapping."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.domain.cte.errors import CteNotFoundError
from src.domain.remetente.errors import RemetenteNotFoundError
from src.domain.destinatario.errors import DestinatarioNotFoundError
from src.domain.transportadora.errors import TransportadoraNotFoundError


def register_error_handlers(app: FastAPI) -> None:
    """Register domain error handlers on the FastAPI app."""


    @app.exception_handler(CteNotFoundError)
    async def handle_cte_not_found(request: Request, exc: CteNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(RemetenteNotFoundError)
    async def handle_remetente_not_found(request: Request, exc: RemetenteNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(DestinatarioNotFoundError)
    async def handle_destinatario_not_found(request: Request, exc: DestinatarioNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(TransportadoraNotFoundError)
    async def handle_transportadora_not_found(request: Request, exc: TransportadoraNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})
