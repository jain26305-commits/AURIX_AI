"""Persistent database models for Phase 14 Controlled Actions & Phase 20 Continuous Assurance Remediations."""

from datetime import datetime, timezone
from typing import Any, Optional
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from aurix_core.database.engine import Base
from aurix_core.database.models.base import TenantMixin


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Phase14ActionModel(Base, TenantMixin):
    __tablename__ = "phase14_actions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(32), nullable=False, default="NORMAL")
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="AWAITING_APPROVAL", index=True)

    target_entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_entity_name: Mapped[str] = mapped_column(String(255), nullable=False)

    prescriptive_payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    initiated_by: Mapped[str] = mapped_column(String(128), nullable=False)
    assigned_approver_role: Mapped[str] = mapped_column(String(64), nullable=False, default="SUPER_ADMIN")

    preflight_cleared: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    preflight_checks_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)

    execution_token_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    audit_trail_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
