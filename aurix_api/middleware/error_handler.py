"""Centralized exception handling, error response mapping, and sanitized logging for Phase 10."""

import logging
import uuid
from typing import Any, Callable, List, Optional, Union, cast
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from aurix_api.schemas.base import (
    ApiErrorPayload,
    ApiErrorResponse,
    ErrorDetail,
    ResponseMetadata,
    ResponseStatus,
)

logger = logging.getLogger("aurix_api.error_handler")


def _get_request_id(request: Request) -> str:
    """Safely extracts request_id from request state or generates a fallback ID."""
    req_id: Optional[str] = getattr(request.state, "request_id", None)
    if req_id and isinstance(req_id, str):
        return req_id
    return f"REQ-{uuid.uuid4().hex[:12].upper()}"


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handles explicit HTTP exceptions raised within routes and dependencies."""
    request_id = _get_request_id(request)
    code_map = {
        status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
        status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
        status.HTTP_403_FORBIDDEN: "FORBIDDEN",
        status.HTTP_404_NOT_FOUND: "NOT_FOUND",
        status.HTTP_409_CONFLICT: "CONFLICT",
        status.HTTP_429_TOO_MANY_REQUESTS: "RATE_LIMIT_EXCEEDED",
    }
    error_code = code_map.get(exc.status_code, f"HTTP_{exc.status_code}")

    error_response = ApiErrorResponse(
        status=ResponseStatus.FAILED,
        request_id=request_id,
        error=ApiErrorPayload(
            code=error_code,
            message=str(exc.detail),
            details=[],
        ),
        meta=ResponseMetadata(tenant_id="SYSTEM"),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(),
    )


async def validation_exception_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError],
) -> JSONResponse:
    """Handles Pydantic and FastAPI payload validation failures."""
    request_id = _get_request_id(request)
    details: List[ErrorDetail] = []

    for err in exc.errors():
        loc = ".".join(str(item) for item in err.get("loc", []))
        details.append(
            ErrorDetail(
                field=loc if loc else None,
                issue=str(err.get("type", "validation_error")),
                message=str(err.get("msg", "Invalid field value")),
            )
        )

    error_response = ApiErrorResponse(
        status=ResponseStatus.FAILED,
        request_id=request_id,
        error=ApiErrorPayload(
            code="VALIDATION_ERROR",
            message="The request payload failed validation checks.",
            details=details,
        ),
        meta=ResponseMetadata(tenant_id="SYSTEM"),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(),
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Sanitizes database exceptions to prevent raw SQL or schema leakage."""
    request_id = _get_request_id(request)
    logger.error("Database exception occurred [Request ID: %s]: %s", request_id, str(exc), exc_info=True)

    if isinstance(exc, IntegrityError):
        status_code = status.HTTP_409_CONFLICT
        error_code = "DATABASE_CONFLICT"
        message = "A database constraint or unique key conflict occurred."
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_code = "DATABASE_ERROR"
        message = "A database operation error occurred. Diagnostics have been logged."

    error_response = ApiErrorResponse(
        status=ResponseStatus.FAILED,
        request_id=request_id,
        error=ApiErrorPayload(
            code=error_code,
            message=message,
            details=[],
        ),
        meta=ResponseMetadata(tenant_id="SYSTEM"),
    )
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all error handler shielding internal stack traces and server internals."""
    request_id = _get_request_id(request)
    logger.error("Unhandled server exception [Request ID: %s]: %s", request_id, str(exc), exc_info=True)

    error_response = ApiErrorResponse(
        status=ResponseStatus.FAILED,
        request_id=request_id,
        error=ApiErrorPayload(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal server error occurred. Please reference the request ID.",
            details=[],
        ),
        meta=ResponseMetadata(tenant_id="SYSTEM"),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(),
    )


def register_error_handlers(app: FastAPI) -> None:
    """Registers all centralized exception handlers to the FastAPI app instance."""
    app.add_exception_handler(HTTPException, cast(Callable[..., Any], http_exception_handler))
    app.add_exception_handler(RequestValidationError, cast(Callable[..., Any], validation_exception_handler))
    app.add_exception_handler(ValidationError, cast(Callable[..., Any], validation_exception_handler))
    app.add_exception_handler(SQLAlchemyError, cast(Callable[..., Any], sqlalchemy_exception_handler))
    app.add_exception_handler(Exception, cast(Callable[..., Any], generic_exception_handler))