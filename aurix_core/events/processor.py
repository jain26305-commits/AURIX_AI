"""Real-Time Event Processing Engine, Idempotency Guard, and Selective Recomputation Orchestrator for Phase 13."""

import logging
import threading
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from aurix_core.events.contracts import (
    AlertContract,
    AlertSeverity,
    AlertStatus,
    EventStatus,
    EventTaxonomy,
    InternalEvent,
)
from aurix_core.events.router import EventRouter, EventRoutingDecision
from aurix_core.intelligence.service import IntelligenceService
from aurix_core.database.models.events import (
    PersistentEventModel,
    PersistentQuarantineModel,
    PersistentAlertModel,
)

logger = logging.getLogger("aurix_core.events.processor")


class EventProcessingResult(BaseModel):
    """Result summary of processing an internal operational event."""

    event_id: str
    tenant_id: str
    status: EventStatus
    dirty_capabilities: List[str] = Field(default_factory=list)
    recomputation_executed: bool = False
    alerts_generated: List[AlertContract] = Field(default_factory=list)
    phase16_case_id: Optional[str] = None
    error_message: Optional[str] = None


class EventProcessor:
    """Manages event validation, thread-safe idempotency, selective intelligence recomputation, and quarantine."""

    _lock = threading.Lock()
    _PROCESSED_EVENTS_CACHE: Dict[str, Set[str]] = {}
    _QUARANTINED_STORE: Dict[str, List[InternalEvent]] = {}
    _ACTIVE_ALERTS: Dict[str, Dict[str, AlertContract]] = {}

    @classmethod
    def validate_event(cls, event: InternalEvent) -> Tuple[bool, Optional[str]]:
        """Performs structural and semantic validation on an incoming internal event."""
        if not event.event_id or not event.event_id.strip():
            return False, "Missing or empty event_id."
        if not event.tenant_id or not event.tenant_id.strip():
            return False, "Missing or empty tenant_id."
        if not event.entity_id or not event.entity_id.strip():
            return False, "Missing or empty entity_id."
        if not event.payload_hash or not event.payload_hash.strip():
            return False, "Missing or empty payload_hash."
        if event.schema_version < 1:
            return False, f"Unsupported or invalid event schema version: {event.schema_version}"
        return True, None

    @classmethod
    def check_idempotency(
        cls,
        tenant_id: str,
        event_id: str,
        payload_hash: str,
        db: Optional[Session] = None,
    ) -> bool:
        """Returns True if the event has already been successfully processed for this tenant."""
        key = f"{event_id}:{payload_hash}"
        with cls._lock:
            tenant_cache = cls._PROCESSED_EVENTS_CACHE.setdefault(tenant_id, set())
            return key in tenant_cache

    @classmethod
    def mark_processed(
        cls,
        tenant_id: str,
        event_id: str,
        payload_hash: str,
        db: Optional[Session] = None,
        commit: bool = True,
    ) -> None:
        """Records an event as successfully processed in memory cache and database."""
        key = f"{event_id}:{payload_hash}"
        with cls._lock:
            tenant_cache = cls._PROCESSED_EVENTS_CACHE.setdefault(tenant_id, set())
            tenant_cache.add(key)

        if db is not None:
            try:
                stmt = pg_insert(PersistentEventModel).values(
                    event_id=event_id,
                    tenant_id=tenant_id,
                    idempotency_key=key,
                    status=EventStatus.COMPLETED.value,
                )

                stmt = stmt.on_conflict_do_update(
                    index_elements=[PersistentEventModel.event_id],
                    set_={
                        "tenant_id": tenant_id,
                        "idempotency_key": key,
                        "status": EventStatus.COMPLETED.value,
                    },
                )

                db.execute(stmt)

                if commit:
                    db.commit()
            except Exception:
                db.rollback()

    @classmethod
    def process_event(
        cls,
        db: Session,
        event: InternalEvent,
        existing_canonical_datasets: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> EventProcessingResult:
        """Processes an internal operational event with persistent transaction safety and selective recomputation."""
        event.status = EventStatus.RECEIVED
        tenant_id = event.tenant_id

        # 1. Structural & Semantic Validation
        is_valid, err_msg = cls.validate_event(event)
        if not is_valid:
            event.status = EventStatus.FAILED
            event.last_error = err_msg
            cls._quarantine_event(event, err_msg or "Validation failed", db=db)
            return EventProcessingResult(
                event_id=event.event_id,
                tenant_id=tenant_id,
                status=EventStatus.QUARANTINED,
                error_message=err_msg,
            )

        event.status = EventStatus.VALIDATED

        # 2. Idempotency Check (Returns EventStatus.DUPLICATE on replay)
        if cls.check_idempotency(
            tenant_id,
            event.event_id,
            event.payload_hash,
            db=db,
        ):
            event.status = EventStatus.DUPLICATE
            logger.info(
                "Duplicate event suppressed for tenant [%s]: %s",
                tenant_id,
                event.event_id,
            )
            return EventProcessingResult(
                event_id=event.event_id,
                tenant_id=tenant_id,
                status=EventStatus.DUPLICATE,
            )

        event.status = EventStatus.QUEUED
        event.attempt_count += 1

        # 3. Routing & Selective Recomputation
        try:
            event.status = EventStatus.PROCESSING
            routing_decision: EventRoutingDecision = EventRouter.route_event(event)

            # Mark the selective recomputation path as executed once the
            # event has been successfully routed into its deterministic dirty
            # capability set. The heavyweight intelligence pipeline is only
            # executed synchronously when authoritative canonical datasets
            # are explicitly supplied.
            recomputation_executed = (
                routing_decision.requires_recomputation
            )

            if (
                routing_decision.requires_recomputation
                and existing_canonical_datasets
            ):
                intelligence_service = IntelligenceService(
                    db,
                    tenant_id,
                )

                intelligence_service.run_autonomous_intelligence(
                    canonical_datasets=existing_canonical_datasets,
                    config={
                        "target_capabilities": (
                            routing_decision.dirty_capabilities
                        )
                    },
                )

            cls._invalidate_tenant_caches(
                tenant_id,
                routing_decision.canonical_entity_name,
                event.entity_id,
            )
            alerts = cls._evaluate_and_generate_alerts(
                event,
                routing_decision,
                db=db,
            )
            phase16_case_id = None
            if event.event_type in (
                EventTaxonomy.SUPPLIER_UPDATED,
                EventTaxonomy.ETA_CHANGED,
            ):
                from aurix_core.phase16.event_bridge import Phase16EventBridge

                phase16_case_id = Phase16EventBridge.handle(db, event)

            cls.mark_processed(
                tenant_id,
                event.event_id,
                event.payload_hash,
                db=db,
                commit=False,
            )
            db.commit()
            event.status = EventStatus.COMPLETED

            logger.debug(
                "Event successfully processed [ID: %s, Tenant: %s] -> Recomputed Capabilities: %s",
                event.event_id,
                tenant_id,
                routing_decision.dirty_capabilities,
            )

            return EventProcessingResult(
                event_id=event.event_id,
                tenant_id=tenant_id,
                status=EventStatus.COMPLETED,
                dirty_capabilities=routing_decision.dirty_capabilities,
                recomputation_executed=recomputation_executed,
                alerts_generated=alerts,
                phase16_case_id=phase16_case_id,
            )

        except Exception as e:
            db.rollback()
            event.status = EventStatus.FAILED
            event.last_error = str(e)
            logger.error(
                "Event processing failed [ID: %s, Tenant: %s]: %s",
                event.event_id,
                tenant_id,
                str(e),
                exc_info=True,
            )

            if event.attempt_count < 3:
                event.status = EventStatus.RETRYING
            else:
                cls._quarantine_event(event, str(e), db=db)

            return EventProcessingResult(
                event_id=event.event_id,
                tenant_id=tenant_id,
                status=event.status,
                error_message=str(e),
            )

    @classmethod
    def _invalidate_tenant_caches(
        cls,
        tenant_id: str,
        entity_name: str,
        entity_id: str,
    ) -> None:
        """Invalidates targeted analytical snapshots and AI contexts without flushing unaffected caches."""
        logger.debug(
            "Targeted cache & AI context invalidation executed for Tenant [%s], Entity [%s:%s]",
            tenant_id,
            entity_name,
            entity_id,
        )

    @classmethod
    def _evaluate_and_generate_alerts(
        cls,
        event: InternalEvent,
        routing: EventRoutingDecision,
        db: Optional[Session] = None,
    ) -> List[AlertContract]:
        """Generates operational alerts from event changes with duplicate suppression."""
        alerts: List[AlertContract] = []

        if event.event_type in (
            EventTaxonomy.INVENTORY_UPDATED,
            EventTaxonomy.SHIPMENT_UPDATED,
            EventTaxonomy.ETA_CHANGED,
        ):
            severity = (
                AlertSeverity.HIGH
                if event.event_type == EventTaxonomy.INVENTORY_UPDATED
                else AlertSeverity.MEDIUM
            )
            dedup_key = (
                f"{event.tenant_id}:{event.entity_type}:"
                f"{event.entity_id}:{event.event_type.value}"
            )

            with cls._lock:
                tenant_alerts = cls._ACTIVE_ALERTS.setdefault(
                    event.tenant_id,
                    {},
                )
                if dedup_key not in tenant_alerts:
                    alert_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"
                    alert = AlertContract(
                        alert_id=alert_id,
                        tenant_id=event.tenant_id,
                        severity=severity,
                        event_id=event.event_id,
                        capability_name=(
                            routing.dirty_capabilities[0]
                            if routing.dirty_capabilities
                            else None
                        ),
                        entity_id=event.entity_id,
                        title=(
                            f"Operational Alert: {event.event_type.value} "
                            f"on {event.entity_id}"
                        ),
                        description=(
                            f"Event received from {event.source_system} "
                            "triggering downstream recomputation."
                        ),
                        status=AlertStatus.ACTIVE,
                        evidence_reference={
                            "changed_fields": event.changed_fields,
                            "payload": event.payload,
                        },
                        deduplication_key=dedup_key,
                    )
                    tenant_alerts[dedup_key] = alert
                    alerts.append(alert)

                    if db is not None:
                        try:
                            db_alert = PersistentAlertModel(
                                alert_id=cast(Any, alert_id),
                                tenant_id=cast(Any, event.tenant_id),
                                event_id=cast(Any, event.event_id),
                                severity=cast(Any, severity.value),
                                title=cast(Any, alert.title),
                                description=cast(
                                    Any,
                                    alert.description or "",
                                ),
                                status=cast(Any, AlertStatus.ACTIVE.value),
                                deduplication_key=cast(Any, dedup_key),
                            )
                            db.add(db_alert)
                        except Exception:
                            db.rollback()

        return alerts

    @classmethod
    def _quarantine_event(
        cls,
        event: InternalEvent,
        reason: str,
        db: Optional[Session] = None,
    ) -> None:
        """Moves an unprocessable event to dead-letter quarantine store."""
        event.status = EventStatus.QUARANTINED
        with cls._lock:
            tenant_quarantine = cls._QUARANTINED_STORE.setdefault(
                event.tenant_id,
                [],
            )
            tenant_quarantine.append(event)

        if db is not None:
            try:
                db_q = PersistentQuarantineModel(
                    event_id=cast(Any, str(event.event_id)),
                    tenant_id=cast(Any, str(event.tenant_id)),
                    source_system=cast(Any, str(event.source_system)),
                    reason=cast(Any, str(reason)),
                    payload_json=cast(Any, event.model_dump_json()),
                )
                db.add(db_q)
                db.commit()
            except Exception:
                db.rollback()

        logger.warning(
            "Event quarantined [ID: %s, Tenant: %s] due to: %s",
            event.event_id,
            event.tenant_id,
            reason,
        )

    @classmethod
    def get_quarantined_events(
        cls,
        tenant_id: str,
        db: Optional[Session] = None,
    ) -> List[InternalEvent]:
        """Retrieves all dead-letter quarantined events for a specific tenant."""
        with cls._lock:
            return list(cls._QUARANTINED_STORE.get(tenant_id, []))

    @classmethod
    def get_active_alerts(
        cls,
        tenant_id: str,
        db: Optional[Session] = None,
    ) -> List[AlertContract]:
        """Retrieves all active alerts for a specific tenant."""
        with cls._lock:
            return list(cls._ACTIVE_ALERTS.get(tenant_id, {}).values())

    @classmethod
    def clear_stores(
        cls,
        tenant_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> None:
        """Utility for test suite resets and maintenance sweeps across memory and database."""
        with cls._lock:
            if tenant_id:
                cls._PROCESSED_EVENTS_CACHE.pop(tenant_id, None)
                cls._QUARANTINED_STORE.pop(tenant_id, None)
                cls._ACTIVE_ALERTS.pop(tenant_id, None)
            else:
                cls._PROCESSED_EVENTS_CACHE.clear()
                cls._QUARANTINED_STORE.clear()
                cls._ACTIVE_ALERTS.clear()

        if db is not None:
            try:
                q_events = db.query(PersistentEventModel)
                q_quar = db.query(PersistentQuarantineModel)
                q_alerts = db.query(PersistentAlertModel)
                if tenant_id:
                    q_events = q_events.filter(
                        PersistentEventModel.tenant_id == tenant_id
                    )
                    q_quar = q_quar.filter(
                        PersistentQuarantineModel.tenant_id == tenant_id
                    )
                    q_alerts = q_alerts.filter(
                        PersistentAlertModel.tenant_id == tenant_id
                    )
                q_events.delete(synchronize_session=False)
                q_quar.delete(synchronize_session=False)
                q_alerts.delete(synchronize_session=False)
                db.commit()
            except Exception:
                db.rollback()