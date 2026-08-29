"""Canonical authentication API for the AURIX application."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from aurix_api.security.auth import create_access_token
from aurix_core.database.engine import SessionLocal
from aurix_core.database.models.auth import User

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


def get_db() -> Session:
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


class LoginRequest(BaseModel):
    email: str
    password: str
    tenantId: str


class LoginUserResponse(BaseModel):
    userId: str
    email: str
    fullName: str
    role: str
    tenantId: str
    permissions: list[str]


class LoginResponse(BaseModel):
    token: str
    user: LoginUserResponse
    expiresInSeconds: int


def _verify_password(password: str, encoded_hash: str) -> bool:
    """
    Verifies passwords stored in the local AURIX PBKDF2 format:

    pbkdf2_sha256$iterations$salt$derived_key
    """
    try:
        algorithm, iterations_raw, salt, expected_hash = encoded_hash.split("$", 3)

        if algorithm != "pbkdf2_sha256":
            return False

        iterations = int(iterations_raw)

        derived = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        ).hex()

        return hmac.compare_digest(derived, expected_hash)
    except (ValueError, TypeError):
        return False


def hash_password(password: str, iterations: int = 310_000) -> str:
    """Creates the password format used by the AURIX authentication layer."""
    salt = secrets.token_hex(16)

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()

    return f"pbkdf2_sha256${iterations}${salt}${derived}"


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest):
    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(
                User.email == payload.email.strip().lower(),
                User.tenant_id == payload.tenantId.strip(),
                User.is_active.is_(True),
            )
            .first()
        )

        # Deliberately do not reveal whether the email or password was wrong.
        if not user or not _verify_password(
            payload.password,
            user.hashed_password,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email, password, or tenant.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            permissions = (
                json.loads(user.permissions_json)
                if user.permissions_json
                else []
            )
        except (json.JSONDecodeError, TypeError):
            permissions = []

        if not isinstance(permissions, list):
            permissions = []

        permissions = [str(p).upper() for p in permissions]

        role = str(user.role).upper()

        # Match the claims expected by aurix_api.security.auth.
        token = create_access_token(
            {
                "sub": str(user.id),
                "tenant_id": str(user.tenant_id),
                "roles": [role],
                "permissions": permissions,
            }
        )

        now = datetime.now(timezone.utc)
        user.last_login_at = now
        db.commit()

        expires_in_seconds = 1440 * 60

        return LoginResponse(
            token=token,
            user=LoginUserResponse(
                userId=str(user.id),
                email=str(user.email),
                fullName=str(user.full_name),
                role=role,
                tenantId=str(user.tenant_id),
                permissions=permissions,
            ),
            expiresInSeconds=expires_in_seconds,
        )

    finally:
        db.close()
