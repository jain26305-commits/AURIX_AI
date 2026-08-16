"""Master FastAPI application factory for AURIX Enterprise Platform."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aurix_api.middleware.correlation import CorrelationIdMiddleware
from aurix_api.middleware.error_handler import register_error_handlers
from aurix_api.routers import (
    actions,
    ai,
    analytics,
    capabilities,
    data,
    events,
    health,
    integrations,
    intelligence,
    onboarding,
    runs,
)
from aurix_core.config.settings import settings
from aurix_core.observability.logging import setup_structured_logging

setup_structured_logging()

logger = logging.getLogger("aurix_api.app")


def _cors_methods() -> list[str]:
    """Return an explicit, production-safe HTTP method allow-list."""
    return [
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ]


def _cors_headers() -> list[str]:
    """Return the headers required by browser clients."""
    return [
        "Accept",
        "Authorization",
        "Content-Type",
        "X-Correlation-ID",
        "X-Request-ID",
    ]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and graceful shutdown."""
    logger.info(
        "AURIX Enterprise API Platform started successfully "
        "[Environment: %s, Build: %s, Schema: %s]",
        settings.environment,
        settings.build_version,
        settings.schema_version,
    )

    try:
        yield
    except Exception:
        # Never suppress an application-lifecycle exception. Logging the
        # failure here preserves the original traceback for the server while
        # allowing FastAPI/Uvicorn to terminate cleanly.
        logger.exception("AURIX Enterprise API lifecycle failure.")
        raise
    finally:
        logger.info(
            "AURIX Enterprise API Platform shutting down gracefully."
        )


def create_app() -> FastAPI:
    """Create and configure the AURIX FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.build_version,
        description=(
            "Enterprise Supply Chain Intelligence Platform, Universal "
            "Integration Hub, Real-Time Event Intelligence, Controlled "
            "Decision Execution & MLOps Hardening."
        ),
        docs_url="/docs" if settings.enable_docs else None,
        redoc_url="/redoc" if settings.enable_docs else None,
        openapi_url="/openapi.json" if settings.enable_docs else None,
        lifespan=lifespan,
    )

    # 1. CORS
    # Origins are supplied exclusively by validated application settings.
    # Methods/headers are explicit rather than wildcarded.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=_cors_methods(),
        allow_headers=_cors_headers(),
    )

    # 2. Correlation / request tracing
    app.add_middleware(CorrelationIdMiddleware)

    # 3. Centralized exception mapping
    register_error_handlers(app)

    # 4. Domain routers
    app.include_router(health.router)
    app.include_router(data.router)
    app.include_router(onboarding.router)
    app.include_router(integrations.router)
    app.include_router(events.router)
    app.include_router(actions.router)
    app.include_router(capabilities.router)
    app.include_router(runs.router)
    app.include_router(analytics.router)
    app.include_router(intelligence.router)
    app.include_router(ai.router)

    return app


app = create_app()