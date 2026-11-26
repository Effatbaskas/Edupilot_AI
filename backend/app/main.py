from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import get_settings
from app.database.connection import engine
from app.utils.logger import setup_logging

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    # Startup
    setup_logging(settings.LOG_LEVEL)
    logger = structlog.get_logger(__name__)
    logger.info("Starting EduPilot AI backend", environment=settings.ENVIRONMENT)

    # Schema changes are applied explicitly with Alembic. The API process must
    # not modify the database as a side effect of starting.
    yield

    # Shutdown
    await engine.dispose()
    logger.info("EduPilot AI backend stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title="EduPilot AI API",
        description="AI-powered educational platform backend",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
                "path": str(request.url.path),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation failed",
                "details": exc.errors(),
                "path": str(request.url.path),
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger = structlog.get_logger(__name__)
        logger.error("Unhandled exception", exc_info=exc, path=str(request.url.path))
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "status_code": 500,
                "path": str(request.url.path),
            },
        )

    # Health check
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "environment": settings.ENVIRONMENT,
            "version": "1.0.0",
            "ai_mode": settings.AI_MODE,
        }

    # Include API routers
    from app.api.router import api_router
    app.include_router(api_router)

    return app


app = create_app()
