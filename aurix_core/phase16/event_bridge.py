"""Bridge Phase 13 operational events into Phase 16 cases and supervisor analysis."""

from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from aurix_core.events.contracts import EventTaxonomy, InternalEvent
from aurix_core.phase16.case_service import build_case_record
from aurix_core.phase16.impact import ImpactPropagationService


class Phase16EventBridge:
    """Create governed Phase 16 cases only for events with explicit semantics."""

    @staticmethod
    def handle(
        db: Session,
        event: InternalEvent,
    ) -> Optional[str]:
        if event.event_type == EventTaxonomy.SUPPLIER_UPDATED:
            delay_days = int(event.payload.get("delay_days", 0) or 0)
            if delay_days <= 0:
                return None
            supplier_impact = ImpactPropagationService.supplier_delay(
                db=db,
                tenant_id=event.tenant_id,
                supplier_id=event.entity_id,
                delay_days=delay_days,
            )
            severity = "HIGH" if supplier_impact.get("affected_sales_line_count", 0) > 0 else "MEDIUM"
            record = build_case_record(
                tenant_id=event.tenant_id,
                case_type="SUPPLIER_DELAY",
                severity=severity,
                title=f"Supplier {event.entity_id} delay of {delay_days} day(s)",
                impact=supplier_impact,
                recommended_action={
                    "action_type": "ANALYZE_RECOVERY_OPTIONS",
                    "execution_authority": "PHASE14_ACTION_EXECUTOR",
                },
            )
            record.updated_at = record.created_at
            db.add(record)
            return record.id

        if event.event_type == EventTaxonomy.ETA_CHANGED:
            delay_days = int(event.payload.get("delay_days", 0) or 0)
            if delay_days <= 0:
                return None
            impact: Dict[str, Any] = {
                "entity_id": event.entity_id,
                "delay_days": delay_days,
                "limitations": [
                    "ETA impact is event-scoped; financial/customer impact requires linked shipment and order data."
                ],
            }
            record = build_case_record(
                tenant_id=event.tenant_id,
                case_type="ETA_DELAY",
                severity="HIGH" if delay_days >= 3 else "MEDIUM",
                title=f"Shipment {event.entity_id} ETA delayed by {delay_days} day(s)",
                impact=impact,
                recommended_action={
                    "action_type": "ANALYZE_FULFILLMENT_IMPACT",
                    "execution_authority": "PHASE14_ACTION_EXECUTOR",
                },
            )
            db.add(record)
            return record.id

        return None
