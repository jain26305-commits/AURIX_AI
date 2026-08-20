"""Request and Correlation ID middleware for end-to-end distributed tracing in Phase 10."""

import time
import uuid
from typing import Awaitable, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from aurix_core.observability.metrics import MetricsRegistry

CORRELATION_HEADER = "X-Request-ID"
CORRELATION_HEADER_ALT = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware that ensures every incoming HTTP request carries a unique Request/Correlation ID."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Extracts or generates correlation ID, binds it to request state, and attaches it to response headers."""
        # 1. Extract existing correlation ID or generate a standardized AURIX Request ID
        incoming_id = request.headers.get(CORRELATION_HEADER) or request.headers.get(CORRELATION_HEADER_ALT)
        if incoming_id and incoming_id.strip():
            request_id = incoming_id.strip()[:64]  # Bounded to prevent header abuse
        else:
            request_id = f"REQ-{uuid.uuid4().hex[:12].upper()}"

        # 2. Attach to request state for downstream handlers, logging, and error envelopes
        request.state.request_id = request_id

        # 3. Process the request through downstream dependencies and routers.
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            MetricsRegistry.increment_api_request(
                is_error=True,
                latency_seconds=time.perf_counter() - started,
            )
            raise

        # 4. Record request telemetry without changing response behavior.
        MetricsRegistry.increment_api_request(
            is_error=response.status_code >= 500,
            latency_seconds=time.perf_counter() - started,
        )

        # 5. Attach request ID to response header for client-side correlation.
        response.headers[CORRELATION_HEADER] = request_id
        return response
