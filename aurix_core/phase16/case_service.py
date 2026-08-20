"""Phase 16 case management helpers."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from aurix_core.phase16.models import Phase16CaseModel


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _decode_json_object(payload: Any) -> Optional[Dict[str, Any]]:
    """Decode a persisted JSON object from text or an already-decoded mapping."""
    if payload is None:
        return None

    if isinstance(payload, str):
        payload = json.loads(payload)

    if isinstance(payload, dict):
        return payload

    return None


def build_case_record(
    tenant_id: str,
    case_type: str,
    severity: str,
    title: str,
    impact: Dict[str, Any],
    recommended_action: Optional[Dict[str, Any]] = None,
) -> Phase16CaseModel:
    """Build a case without committing, for callers already inside a transaction."""
    return Phase16CaseModel(
        id=f"CASE-{uuid.uuid4().hex[:16].upper()}",
        tenant_id=tenant_id,
        case_type=case_type,
        severity=severity,
        status="OPEN",
        title=title,
        impact_json=impact,
        recommended_action_json=recommended_action,
        created_at=_now(),
        updated_at=_now(),
    )


def create_case(
    db: Session,
    tenant_id: str,
    case_type: str,
    severity: str,
    title: str,
    impact: Dict[str, Any],
    recommended_action: Optional[Dict[str, Any]] = None,
) -> str:
    record = build_case_record(
        tenant_id,
        case_type,
        severity,
        title,
        impact,
        recommended_action,
    )
    db.add(record)
    db.commit()
    return record.id


def get_case(
    db: Session,
    tenant_id: str,
    case_id: str,
) -> Optional[Dict[str, Any]]:
    record = db.execute(
        select(Phase16CaseModel).where(
            Phase16CaseModel.tenant_id == tenant_id,
            Phase16CaseModel.id == case_id,
        )
    ).scalar_one_or_none()

    if record is None:
        return None

    impact = _decode_json_object(record.impact_json) or {}
    recommended_action = _decode_json_object(record.recommended_action_json)

    return {
        "case_id": record.id,
        "case_type": record.case_type,
        "severity": record.severity,
        "status": record.status,
        "title": record.title,
        "impact": impact,
        "recommended_action": recommended_action,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


_ALLOWED_CASE_TRANSITIONS: dict[str, set[str]] = {
    "OPEN": {"ACKNOWLEDGED", "ANALYZING", "CLOSED"},
    "ACKNOWLEDGED": {"ANALYZING", "ACTION_PROPOSED", "CLOSED"},
    "ANALYZING": {"ACTION_PROPOSED", "RESOLVED", "CLOSED"},
    "ACTION_PROPOSED": {"AWAITING_APPROVAL", "IN_PROGRESS", "RESOLVED"},
    "AWAITING_APPROVAL": {"IN_PROGRESS", "CLOSED"},
    "IN_PROGRESS": {"RESOLVED", "CLOSED"},
    "RESOLVED": {"VERIFIED", "CLOSED"},
    "VERIFIED": {"CLOSED"},
    "CLOSED": set(),
}


def transition_case(
    db: Session,
    tenant_id: str,
    case_id: str,
    target_status: str,
    owner: Optional[str] = None,
    resolution: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Apply a guarded case lifecycle transition."""
    record = db.execute(
        select(Phase16CaseModel).where(
            Phase16CaseModel.tenant_id == tenant_id,
            Phase16CaseModel.id == case_id,
        )
    ).scalar_one_or_none()

    if record is None:
        return None

    current = str(record.status)

    if target_status not in _ALLOWED_CASE_TRANSITIONS.get(current, set()):
        return {
            "case_id": case_id,
            "status": current,
            "error": "INVALID_CASE_TRANSITION",
        }

    record.status = target_status

    if owner is not None:
        record.owner = owner

    if resolution is not None:
        record.resolution_json = resolution

    record.updated_at = _now()
    db.commit()

    return get_case(db, tenant_id, case_id)