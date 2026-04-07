"""FastAPI application entry point."""

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.exceptions import APIException
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
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.get("/api/v1/health")
    async def health_check():
        return {"status": "healthy"}

    app.include_router(cte_router, prefix="/api/v1", tags=["cte"])
    app.include_router(remetente_router, prefix="/api/v1", tags=["remetente"])
    app.include_router(destinatario_router, prefix="/api/v1", tags=["destinatario"])
    app.include_router(transportadora_router, prefix="/api/v1", tags=["transportadora"])

    register_error_handlers(app)

    return app


app = create_app()
