"""Centralized domain-to-HTTP error mapping — RFC 9110 Problem Details."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.exceptions import problem_detail_response
from src.domain.cte.errors import CteNotFoundError
from src.domain.remetente.errors import DuplicateCnpjError as RemetenteDuplicateCnpjError, RemetenteNotFoundError
from src.domain.destinatario.errors import DestinatarioNotFoundError, DuplicateCnpjError as DestinatarioDuplicateCnpjError
from src.domain.transportadora.errors import TransportadoraNotFoundError


def register_error_handlers(app: FastAPI) -> None:
    """Register domain error handlers on the FastAPI app."""

    @app.exception_handler(CteNotFoundError)
    async def handle_cte_not_found(request: Request, exc: CteNotFoundError) -> JSONResponse:
        return problem_detail_response(404, str(exc))

    @app.exception_handler(RemetenteNotFoundError)
    async def handle_remetente_not_found(request: Request, exc: RemetenteNotFoundError) -> JSONResponse:
        return problem_detail_response(404, str(exc))

    @app.exception_handler(DestinatarioNotFoundError)
    async def handle_destinatario_not_found(request: Request, exc: DestinatarioNotFoundError) -> JSONResponse:
        return problem_detail_response(404, str(exc))

    @app.exception_handler(TransportadoraNotFoundError)
    async def handle_transportadora_not_found(request: Request, exc: TransportadoraNotFoundError) -> JSONResponse:
        return problem_detail_response(404, str(exc))

    @app.exception_handler(RemetenteDuplicateCnpjError)
    async def handle_remetente_duplicate_cnpj(request: Request, exc: RemetenteDuplicateCnpjError) -> JSONResponse:
        return problem_detail_response(409, str(exc))

    @app.exception_handler(DestinatarioDuplicateCnpjError)
    async def handle_destinatario_duplicate_cnpj(request: Request, exc: DestinatarioDuplicateCnpjError) -> JSONResponse:
        return problem_detail_response(409, str(exc))
