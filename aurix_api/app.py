"""Master FastAPI application factory for AURIX Enterprise Platform."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aurix_api.middleware.correlation import CorrelationIdMiddleware
from aurix_api.middleware.security_headers import SecurityHeadersMiddleware
from aurix_api.middleware.error_handler import register_error_handlers
from aurix_api.routers import (
    auth,
    actions,
    ai,
    analytics,
    assurance,
    capabilities,
    data,
    events,
    health,
    integrations,
    intelligence,
    onboarding,
    phase16,
    runs,
)

from sqlalchemy import text

from aurix_core.database.engine import SessionLocal

# Optional domain router imports
try:
    from aurix_api.routers import finance
except ImportError:
    finance = None  # type: ignore[assignment]

try:
    from aurix_api.routers import commercial
except ImportError:
    commercial = None  # type: ignore[assignment]

try:
    from aurix_api.routers import manufacturing
except ImportError:
    manufacturing = None  # type: ignore[assignment]

try:
    from aurix_api.routers import context
except ImportError:
    context = None  # type: ignore[assignment]

try:
    from aurix_api.routers import process
except ImportError:
    process = None  # type: ignore[assignment]

try:
    from aurix_api.routers import risk
except ImportError:
    risk = None  # type: ignore[assignment]

try:
    from aurix_api.routers import decisions
except ImportError:
    decisions = None  # type: ignore[assignment]

try:
    from aurix_api.routers import scenarios
except ImportError:
    scenarios = None  # type: ignore[assignment]

try:
    from aurix_api.routers import executive
except ImportError:
    executive = None  # type: ignore[assignment]

try:
    from aurix_api.routers import agents
except ImportError:
    agents = None  # type: ignore[assignment]

try:
    from aurix_api.routers import agent_studio
except ImportError:
    agent_studio = None  # type: ignore[assignment]

from aurix_core.config.settings import settings
from aurix_core.observability.logging import setup_structured_logging

setup_structured_logging()

logger = logging.getLogger("aurix_api.app")


def _cors_methods() -> list[str]:
    return [
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ]


def _cors_headers() -> list[str]:
    return [
        "Accept",
        "Authorization",
        "Content-Type",
        "X-Correlation-ID",
        "X-Request-ID",
        "X-Tenant-ID",
    ]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info(
        "AURIX Enterprise API Platform started successfully "
        "[Environment: %s, Build: %s, Schema: %s]",
        settings.environment,
        settings.build_version,
        settings.schema_version,
    )

    # Warm the PostgreSQL connection pool before the first real request/event.
    # This removes cold connection acquisition and first-transaction setup from
    # the latency of the first production operation while preserving pool_pre_ping,
    # PostgreSQL RLS, and normal request-scoped session behavior.
    try:
        warm_start = __import__("time").perf_counter()

        with SessionLocal() as db:
            db.execute(text("SELECT 1"))

        warm_ms = (__import__("time").perf_counter() - warm_start) * 1000.0

        logger.info(
            "AURIX PostgreSQL connection pool warmed successfully "
            "[Warmup: %.3f ms]",
            warm_ms,
        )
    except Exception:
        logger.exception(
            "AURIX PostgreSQL connection pool warmup failed."
        )
        raise

    try:
        yield
    except Exception:
        logger.exception("AURIX Enterprise API lifecycle failure.")
        raise
    finally:
        logger.info("AURIX Enterprise API Platform shutting down gracefully.")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.build_version,
        description=(
            "Enterprise Supply Chain Intelligence Platform, Universal "
            "Integration Hub, Real-Time Event Intelligence, Controlled "
            "Decision Execution, Enterprise Data Fabric, Continuous Assurance, "
            "Business Finance Intelligence, Commercial Intelligence, "
            "Manufacturing Intelligence, Enterprise Business Context Graph, "
            "Process Intelligence, Risk Intelligence, Deterministic Decision Engine 2.0, "
            "Scenario Simulation, Executive Intelligence, Governed Autonomous Agents & "
            "Enterprise Agent Studio."
        ),
        docs_url="/docs" if settings.enable_docs else None,
        redoc_url="/redoc" if settings.enable_docs else None,
        openapi_url="/openapi.json" if settings.enable_docs else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=_cors_methods(),
        allow_headers=_cors_headers(),
    )

    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    register_error_handlers(app)

    # Authentication
    app.include_router(auth.router)

    # Core Domain Routers
    app.include_router(health.router)
    app.include_router(health.admin_health_router)
    app.include_router(data.router)
    app.include_router(onboarding.router)
    app.include_router(integrations.router)
    app.include_router(events.router)
    app.include_router(actions.router)
    app.include_router(assurance.router)
    if finance is not None and hasattr(finance, "router"):
        app.include_router(finance.router)
    if commercial is not None and hasattr(commercial, "router"):
        app.include_router(commercial.router)
    if manufacturing is not None and hasattr(manufacturing, "router"):
        app.include_router(manufacturing.router)
    if context is not None and hasattr(context, "router"):
        app.include_router(context.router)
    if process is not None and hasattr(process, "router"):
        app.include_router(process.router)
    if risk is not None and hasattr(risk, "router"):
        app.include_router(risk.router)
    if decisions is not None and hasattr(decisions, "router"):
        app.include_router(decisions.router)
    if scenarios is not None and hasattr(scenarios, "router"):
        app.include_router(scenarios.router)
    if executive is not None and hasattr(executive, "router"):
        app.include_router(executive.router)
    if agents is not None and hasattr(agents, "router"):
        app.include_router(agents.router)
    if agent_studio is not None and hasattr(agent_studio, "router"):
        app.include_router(agent_studio.router)
    app.include_router(capabilities.router)
    app.include_router(runs.router)
    app.include_router(analytics.router)
    app.include_router(intelligence.router)
    app.include_router(ai.router)
    app.include_router(phase16.router)

    return app


app = create_app()
