"""FastAPI application entry point."""

import os

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from fastapi.exceptions import RequestValidationError

from src.api.exceptions import APIException, problem_detail_response
from src.api.error_handlers import register_error_handlers

from src.api.v1.ctes import router as cte_router
from src.api.v1.remetentes import router as remetente_router
from src.api.v1.destinatarios import router as destinatario_router
from src.api.v1.transportadoras import router as transportadora_router

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
)
logger = structlog.get_logger()


def create_app() -> FastAPI:
    app = FastAPI(title="CTEDemo API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            o.strip()
            for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
            if o.strip()
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
        return problem_detail_response(exc.status_code, exc.detail)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = {}
        for err in exc.errors():
            field = ".".join(str(loc) for loc in err["loc"] if loc != "body")
            errors[field] = err["msg"]
        detail = "; ".join(f"{k}: {v}" for k, v in errors.items()) if errors else str(exc)
        return problem_detail_response(422, detail, errors=errors)

    @app.get("/api/v1/health")
    async def health_check():
        return {"status": "healthy"}

    app.include_router(cte_router, prefix="/api/v1", tags=["cte"])
    app.include_router(remetente_router, prefix="/api/v1", tags=["remetente"])
    app.include_router(destinatario_router, prefix="/api/v1", tags=["destinatario"])
    app.include_router(transportadora_router, prefix="/api/v1", tags=["transportadora"])

    register_error_handlers(app)

    @app.on_event("startup")
    async def seed_memory_data():
        from src.config.settings import settings
        if settings.data_mode == "memory":
            from src.infrastructure.database.repositories.provider import get_repository_provider
            provider = get_repository_provider()
            repo = provider.get_remetente_repository()
            repo.seed_if_empty()

    return app


app = create_app()
