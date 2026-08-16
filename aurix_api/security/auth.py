"""Authentication dependency, token verification, and tenant context resolution for Phase 10."""

import base64
import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from aurix_api.schemas.auth import (
    Permission,
    Role,
    TenantContext,
    TokenPayload,
    UserIdentity,
)
from aurix_core.config.settings import settings

# Security Scheme Dependencies
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


def _base64url_encode(data: bytes) -> str:
    """Encodes bytes to Base64URL string without trailing padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _base64url_decode(data_str: str) -> bytes:
    """Decodes Base64URL string restoring required padding."""
    padding = 4 - (len(data_str) % 4)
    if padding != 4:
        data_str += "=" * padding
    return base64.urlsafe_b64decode(data_str.encode("utf-8"))


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generates a cryptographically signed HS256 JWT access token."""
    now = int(time.time())
    expire_minutes = expires_delta.total_seconds() / 60.0 if expires_delta else settings.api_access_token_expire_minutes
    exp = now + int(expire_minutes * 60)

    payload = dict(data)
    payload["iat"] = now
    payload["exp"] = exp

    header = {"alg": settings.api_algorithm, "typ": "JWT"}

    encoded_header = _base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))

    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    signature = hmac.new(
        key=settings.api_secret_key.encode("utf-8"),
        msg=signing_input,
        digestmod=hashlib.sha256,
    ).digest()

    encoded_signature = _base64url_encode(signature)
    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"


def decode_access_token(token: str) -> TokenPayload:
    """Validates and decodes an HS256 JWT token into a structured TokenPayload."""
    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format. Expected header, payload, and signature.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    encoded_header, encoded_payload, encoded_signature = parts
    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    expected_sig = hmac.new(
        key=settings.api_secret_key.encode("utf-8"),
        msg=signing_input,
        digestmod=hashlib.sha256,
    ).digest()

    try:
        provided_sig = _base64url_decode(encoded_signature)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token signature.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not hmac.compare_digest(expected_sig, provided_sig):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid cryptographic signature on token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        raw_payload = json.loads(_base64url_decode(encoded_payload).decode("utf-8"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token payload JSON.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    exp = raw_payload.get("exp")
    if exp is None or int(exp) < int(time.time()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    sub = raw_payload.get("sub")
    tenant_id = raw_payload.get("tenant_id")
    if not sub or not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing required identity claims ('sub' or 'tenant_id').",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenPayload(
        sub=str(sub),
        tenant_id=str(tenant_id),
        roles=raw_payload.get("roles", ["VIEWER"]),
        permissions=raw_payload.get("permissions", []),
        exp=int(exp),
        iat=raw_payload.get("iat"),
    )


async def get_current_tenant_context(
    request: Request,
    bearer_auth: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    api_key_auth: Optional[str] = Security(api_key_header_scheme),
) -> TenantContext:
    """
    FastAPI security dependency resolving and injecting the authenticated TenantContext.
    Enforces strict tenant isolation by mapping verified claims to context.
    """
    token_str: Optional[str] = None

    if bearer_auth and bearer_auth.credentials:
        token_str = bearer_auth.credentials.strip()
    elif api_key_auth and api_key_auth.strip():
        token_str = api_key_auth.strip()

    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided. Include 'Authorization: Bearer <token>' header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token_str)

    # Convert payload role strings into typed Role enum instances
    parsed_roles: List[Role] = []
    for r_str in payload.roles:
        try:
            parsed_roles.append(Role(r_str.upper()))
        except ValueError:
            parsed_roles.append(Role.VIEWER)

    if not parsed_roles:
        parsed_roles = [Role.VIEWER]

    # Convert payload permission strings into typed Permission enum instances
    parsed_permissions: List[Permission] = []
    for p_str in payload.permissions:
        try:
            parsed_permissions.append(Permission(p_str.upper()))
        except ValueError:
            continue

    user_identity = UserIdentity(
        user_id=payload.sub,
        username=payload.sub,
        roles=parsed_roles,
        permissions=parsed_permissions,
    )

    tenant_context = TenantContext(
        tenant_id=payload.tenant_id,
        user=user_identity,
        session_id=getattr(request.state, "request_id", f"SESS-{uuid.uuid4().hex[:8].upper()}"),
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    # Mount resolved tenant context to request state for logging and analytics
    request.state.tenant_context = tenant_context
    request.state.tenant_id = tenant_context.tenant_id

    return tenant_context