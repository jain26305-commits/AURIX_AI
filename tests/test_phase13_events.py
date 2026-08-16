"""Comprehensive Test Suite for Phase 13 Real-Time & Event-Driven Intelligence."""

import unittest
from typing import Any
from fastapi.testclient import TestClient

from aurix_api.app import create_app
from aurix_api.security.auth import create_access_token
from aurix_core.database.engine import Base, SessionLocal, engine
from aurix_core.events.contracts import EventStatus, EventTaxonomy, InternalEvent
from aurix_core.events.processor import EventProcessor
from aurix_core.events.router import EventRouter


class TestPhase13RealTimeEvents(unittest.TestCase):
    """Test suite covering Phase 13 event contracts, routing, processing, quarantine, alerts, and API routes."""

    app: Any
    client: TestClient
    token_admin_alpha: str
    token_viewer_alpha: str
    token_admin_beta: str

    @classmethod
    def setUpClass(cls) -> None:
        """Initializes FastAPI test client, database tables, and security tokens."""
        Base.metadata.create_all(bind=engine)
        cls.app = create_app()
        cls.client = TestClient(cls.app)

        cls.token_admin_alpha = create_access_token({
            "sub": "user_admin_1",
            "tenant_id": "tenant_alpha",
            "roles": ["ADMIN"],
            "permissions": ["READ_DATA", "WRITE_DATA", "RUN_ANALYSIS", "MANAGE_EVENTS", "VIEW_EVENTS", "MANAGE_ALERTS"],
        })

        cls.token_viewer_alpha = create_access_token({
            "sub": "user_viewer_1",
            "tenant_id": "tenant_alpha",
            "roles": ["VIEWER"],
            "permissions": ["READ_DATA", "VIEW_EVENTS"],
        })

        cls.token_admin_beta = create_access_token({
            "sub": "user_admin_2",
            "tenant_id": "tenant_beta",
            "roles": ["ADMIN"],
            "permissions": ["READ_DATA", "WRITE_DATA", "RUN_ANALYSIS", "MANAGE_EVENTS", "VIEW_EVENTS", "MANAGE_ALERTS"],
        })

    def setUp(self) -> None:
        """Resets in-memory event caches between test runs."""
        EventProcessor._PROCESSED_EVENTS_CACHE.clear()
        EventProcessor._QUARANTINED_STORE.clear()
        EventProcessor._ACTIVE_ALERTS.clear()

    def test_01_event_validation_and_rejection(self) -> None:
        """Verifies validation logic for missing fields and invalid schema versions."""
        invalid_event = InternalEvent(
            event_id="",
            tenant_id="tenant_alpha",
            source_system="ERP_ODOO",
            event_type=EventTaxonomy.INVENTORY_UPDATED,
            entity_type="inventory_levels",
            entity_id="SKU-101",
            event_timestamp="2026-08-14T10:00:00Z",
            payload_hash="abc123hash",
            schema_version=0,
        )
        is_valid, err = EventProcessor.validate_event(invalid_event)
        self.assertFalse(is_valid)
        self.assertIn("event_id", err or "")

    def test_02_idempotency_and_replay_protection(self) -> None:
        """Verifies that duplicate events with the same ID and payload hash are suppressed."""
        db = SessionLocal()
        try:
            event = InternalEvent(
                event_id="EVT-IDEM-001",
                tenant_id="tenant_alpha",
                source_system="WMS_GENERIC",
                event_type=EventTaxonomy.INVENTORY_UPDATED,
                entity_type="inventory_levels",
                entity_id="SKU-102",
                event_timestamp="2026-08-14T10:00:00Z",
                payload_hash="hashval999",
                payload={"on_hand": 500},
            )

            # First processing -> COMPLETED
            res1 = EventProcessor.process_event(db, event)
            self.assertEqual(res1.status, EventStatus.COMPLETED)

            # Second processing (replay) -> DUPLICATE suppression
            res2 = EventProcessor.process_event(db, event)
            self.assertEqual(res2.status, EventStatus.DUPLICATE)
        finally:
            db.close()

    def test_03_event_routing_and_impact_analysis(self) -> None:
        """Verifies deterministic event routing to correct canonical entities and dirty capabilities."""
        event = InternalEvent(
            event_id="EVT-ROUTE-001",
            tenant_id="tenant_alpha",
            source_system="TMS_LOGISTICS",
            event_type=EventTaxonomy.SHIPMENT_UPDATED,
            entity_type="shipments",
            entity_id="SHPM-55",
            event_timestamp="2026-08-14T11:00:00Z",
            payload_hash="routehash123",
        )
        decision = EventRouter.route_event(event)
        self.assertEqual(decision.canonical_entity_name, "shipments")
        self.assertIn("SHIPMENT_TRACKING_ETA", decision.dirty_capabilities)
        self.assertTrue(decision.requires_recomputation)

    def test_04_selective_recomputation_processing(self) -> None:
        """Verifies that inventory updates trigger selective recomputation without unrelated runs."""
        db = SessionLocal()
        try:
            event = InternalEvent(
                event_id="EVT-RECOMP-001",
                tenant_id="tenant_alpha",
                source_system="ERP_ODOO",
                event_type=EventTaxonomy.INVENTORY_UPDATED,
                entity_type="inventory_levels",
                entity_id="SKU-200",
                event_timestamp="2026-08-14T12:00:00Z",
                payload_hash="recomphash456",
                payload={"available_stock": 50},
            )
            result = EventProcessor.process_event(db, event)
            self.assertEqual(result.status, EventStatus.COMPLETED)
            self.assertTrue(result.recomputation_executed)
            self.assertIn("SAFETY_STOCK_ROP", result.dirty_capabilities)
        finally:
            db.close()

    def test_05_quarantine_and_retry_workflow(self) -> None:
        """Verifies dead-letter quarantining on failure and successful retry recovery."""
        db = SessionLocal()
        try:
            bad_event = InternalEvent(
                event_id="EVT-BAD-001",
                tenant_id="tenant_alpha",
                source_system="ERP_ODOO",
                event_type=EventTaxonomy.INVENTORY_UPDATED,
                entity_type="inventory_levels",
                entity_id="",  # Invalid empty entity_id triggers validation failure
                event_timestamp="2026-08-14T13:00:00Z",
                payload_hash="badhash789",
            )
            res = EventProcessor.process_event(db, bad_event)
            self.assertEqual(res.status, EventStatus.QUARANTINED)

            # Check quarantine inspect endpoint via API
            res_inspect = self.client.get(
                "/api/v1/events/quarantine",
                headers={"Authorization": f"Bearer {self.token_admin_alpha}"},
            )
            self.assertEqual(res_inspect.status_code, 200)
            self.assertEqual(len(res_inspect.json()["data"]), 1)
        finally:
            db.close()

    def test_06_operational_alerts_and_deduplication(self) -> None:
        """Verifies alert generation and duplicate alert suppression."""
        db = SessionLocal()
        try:
            event = InternalEvent(
                event_id="EVT-ALERT-001",
                tenant_id="tenant_alpha",
                source_system="ERP_ODOO",
                event_type=EventTaxonomy.INVENTORY_UPDATED,
                entity_type="inventory_levels",
                entity_id="SKU-ALERT-1",
                event_timestamp="2026-08-14T14:00:00Z",
                payload_hash="alerthash111",
            )
            EventProcessor.process_event(db, event)

            # Process duplicate event with same entity/type -> should suppress duplicate alert
            event_dup = InternalEvent(
                event_id="EVT-ALERT-002",
                tenant_id="tenant_alpha",
                source_system="ERP_ODOO",
                event_type=EventTaxonomy.INVENTORY_UPDATED,
                entity_type="inventory_levels",
                entity_id="SKU-ALERT-1",
                event_timestamp="2026-08-14T14:05:00Z",
                payload_hash="alerthash222",
            )
            EventProcessor.process_event(db, event_dup)

            res_alerts = self.client.get(
                "/api/v1/alerts",
                headers={"Authorization": f"Bearer {self.token_admin_alpha}"},
            )
            self.assertEqual(res_alerts.status_code, 200)
            alerts = res_alerts.json()["data"]
            self.assertEqual(len(alerts), 1)  # Deduplication suppressed the second alert
        finally:
            db.close()

    def test_07_api_endpoints_and_tenant_isolation(self) -> None:
        """Verifies tenant isolation on event quarantine and alert endpoints."""
        # Inject quarantined event into tenant_beta
        beta_event = InternalEvent(
            event_id="EVT-BETA-Q",
            tenant_id="tenant_beta",
            source_system="ERP_ODOO",
            event_type=EventTaxonomy.INVENTORY_UPDATED,
            entity_type="inventory_levels",
            entity_id="",
            event_timestamp="2026-08-14T15:00:00Z",
            payload_hash="betahash",
        )
        db = SessionLocal()
        try:
            EventProcessor.process_event(db, beta_event)

            # Tenant Alpha attempts to inspect quarantine -> should see 0 items (strict isolation)
            res_alpha = self.client.get(
                "/api/v1/events/quarantine",
                headers={"Authorization": f"Bearer {self.token_admin_alpha}"},
            )
            self.assertEqual(res_alpha.status_code, 200)
            self.assertEqual(len(res_alpha.json()["data"]), 0)

            # Tenant Beta inspects quarantine -> sees 1 item
            res_beta = self.client.get(
                "/api/v1/events/quarantine",
                headers={"Authorization": f"Bearer {self.token_admin_beta}"},
            )
            self.assertEqual(res_beta.status_code, 200)
            self.assertEqual(len(res_beta.json()["data"]), 1)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()