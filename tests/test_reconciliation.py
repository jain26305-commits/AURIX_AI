"""Comprehensive Verification Suite for AURIX Backend Integrity Reconciliation, AI Quota, and Zero-Fabrication."""

import threading
import unittest
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import MagicMock

from aurix_core.actions.contracts import (
    ActionCategory,
    ActionContract,
    ActionState,
    ActionType,
    ApprovalState,
)
from aurix_core.actions.executor import ActionExecutor
from aurix_core.config.settings import Settings
from aurix_core.events.contracts import (
    AlertSeverity,
    AlertStatus,
    EventStatus,
    EventTaxonomy,
    InternalEvent,
)
from aurix_core.events.processor import EventProcessor
from aurix_core.integrations.adapters.erp_odoo import OdooErpConnector
from aurix_core.integrations.adapters.wms_generic import GenericWMSAdapter
from aurix_core.integrations.contracts import ConnectorConfig
from aurix_core.intelligence.ai_gateway import AIGateway, ProviderStatus
from aurix_core.intelligence.context import FactItem, FactPack
from aurix_core.intelligence.quota import AIQuotaManager, TenantAIQuotaPolicy
from aurix_core.intelligence.router import QueryType, RouterConfidence, RoutingDecision
from aurix_core.observability.metrics import MetricsRegistry


class TestBackendIntegrityReconciliation(unittest.TestCase):
    """Rigorous test suite covering all reconciliation areas and invariants."""

    def setUp(self) -> None:
        """Resets in-memory registries, usage ledgers, and action stores before every test."""
        AIQuotaManager.reset_usage_ledger()
        ActionExecutor._ACTIONS_STORE.clear()
        ActionExecutor._AUDIT_STORE.clear()
        EventProcessor.clear_stores()
        MetricsRegistry.reset()

        self.db = MagicMock()
        self.db.commit.return_value = None
        self.db.rollback.return_value = None

    def tearDown(self) -> None:
        """Clean up."""
        MetricsRegistry.reset()

    # =========================================================================
    # 1. AI QUOTA & BUDGET CONTROL TESTS
    # =========================================================================

    def test_01_ai_quota_under_limit_and_usage_recording(self) -> None:
        """Verifies normal AI quota allowance and persistent usage ledger recording."""
        policy = TenantAIQuotaPolicy(
            tenant_id="tenant_alpha",
            monthly_spend_limit_usd=10.0,
            daily_spend_limit_usd=2.0,
            monthly_token_limit=100_000,
            daily_token_limit=20_000,
        )
        AIQuotaManager.set_policy(policy)

        check = AIQuotaManager.check_quota("tenant_alpha", estimated_tokens=500, estimated_cost_usd=0.01)
        self.assertTrue(check.allowed)
        self.assertFalse(check.is_warning)

        rec = AIQuotaManager.record_usage(
            tenant_id="tenant_alpha",
            provider="GEMINI_FLASH_LITE",
            model="gemini-2.5-flash-lite",
            input_tokens=400,
            output_tokens=100,
            estimated_cost_usd=0.01,
        )
        self.assertEqual(rec.tenant_id, "tenant_alpha")
        self.assertEqual(rec.input_tokens, 400)

        summary = AIQuotaManager.get_tenant_usage_summary("tenant_alpha")
        self.assertEqual(summary["daily_tokens"], 500)
        self.assertEqual(summary["daily_requests"], 1)
        self.assertAlmostEqual(summary["daily_spend_usd"], 0.01, places=3)

    def test_02_ai_quota_warning_threshold(self) -> None:
        """Verifies soft warning trigger when tenant usage reaches warning threshold percentage."""
        policy = TenantAIQuotaPolicy(
            tenant_id="tenant_beta",
            monthly_spend_limit_usd=1.0,
            daily_spend_limit_usd=1.0,
            warning_threshold_pct=80.0,
        )
        AIQuotaManager.set_policy(policy)

        AIQuotaManager.record_usage(
            tenant_id="tenant_beta",
            provider="GEMINI_FLASH",
            model="gemini-2.5-flash",
            input_tokens=1000,
            output_tokens=500,
            estimated_cost_usd=0.85,
        )

        check = AIQuotaManager.check_quota("tenant_beta", estimated_tokens=100, estimated_cost_usd=0.01)
        self.assertTrue(check.allowed)
        self.assertTrue(check.is_warning)
        self.assertIn("Warning: Tenant AI consumption has reached", str(check.warning_message))

    def test_03_ai_quota_hard_limit_deterministic_fallback(self) -> None:
        """Verifies that an exhausted AI quota safely routes queries to deterministic fallback without crashing."""
        policy = TenantAIQuotaPolicy(
            tenant_id="tenant_gamma",
            monthly_spend_limit_usd=0.05,
            daily_spend_limit_usd=0.05,
        )
        AIQuotaManager.set_policy(policy)

        AIQuotaManager.record_usage(
            tenant_id="tenant_gamma",
            provider="GEMINI_FLASH",
            model="gemini-2.5-flash",
            input_tokens=5000,
            output_tokens=2000,
            estimated_cost_usd=0.06,
        )

        gateway = AIGateway()
        fact_pack = FactPack(
            pack_id="FACT-QUOTA-01",
            tenant_id="tenant_gamma",
            facts=[
                FactItem(
                    domain="inventory",
                    entity_id="SKU-100",
                    metric_name="safety_stock",
                    value=45.0,
                    value_state="CALCULATED",
                    freshness="LIVE",
                )
            ],
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
        routing = RoutingDecision(
            query="Analyze inventory safety stock risk",
            query_type=QueryType.EXPLAIN,
            requires_ai=True,
            confidence=RouterConfidence.HIGH,
            context_source="DYNAMIC_ASSEMBLY",
        )

        response = gateway.process_query(fact_pack, routing)

        self.assertTrue(response.is_fallback)
        self.assertEqual(response.provider_used, "DETERMINISTIC_FALLBACK")
        self.assertTrue(response.provenance.get("quota_exhausted", False))
        self.assertIn("AI quota limit reached", response.explanation)

    def test_04_ai_quota_concurrency_thread_safety(self) -> None:
        """Simulates 20 concurrent threads to ensure atomic quota evaluation without race conditions."""
        policy = TenantAIQuotaPolicy(
            tenant_id="tenant_concurrent",
            monthly_spend_limit_usd=100.0,
            daily_spend_limit_usd=100.0,
            monthly_request_limit=1000,
            daily_request_limit=1000,
        )
        AIQuotaManager.set_policy(policy)

        thread_count = 20
        threads: List[threading.Thread] = []
        errors: List[Exception] = []

        def worker_task(idx: int) -> None:
            try:
                check = AIQuotaManager.check_quota("tenant_concurrent", estimated_tokens=100, estimated_cost_usd=0.001)
                if check.allowed:
                    AIQuotaManager.record_usage(
                        tenant_id="tenant_concurrent",
                        provider="GEMINI_FLASH_LITE",
                        model="gemini-2.5-flash-lite",
                        input_tokens=80,
                        output_tokens=20,
                        estimated_cost_usd=0.001,
                    )
            except Exception as e:
                errors.append(e)

        for i in range(thread_count):
            t = threading.Thread(target=worker_task, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)
        summary = AIQuotaManager.get_tenant_usage_summary("tenant_concurrent")
        self.assertEqual(summary["daily_requests"], thread_count)

    # =========================================================================
    # 2. ZERO-FABRICATION IN INTEGRATION ADAPTERS
    # =========================================================================

    def test_05_wms_adapter_zero_fabrication(self) -> None:
        """Verifies that WMS transforms preserve None for missing quantities/bins without defaulting to zeroes."""
        adapter = GenericWMSAdapter(tenant_id="tenant_wms")
        raw_items = [
            {
                "sku": "SKU-AUTHENTIC-01",
                "warehouse": "WH-NORTH",
                "qty_on_hand": "150.5",
                "bin": "BIN-A-12",
                "updated_at": "2026-08-14T10:00:00Z",
            },
            {
                "sku": "SKU-PARTIAL-02",
                "warehouse": "WH-SOUTH",
            },
        ]

        records = adapter.transform_inventory_payload(raw_items)
        self.assertEqual(len(records), 2)

        self.assertEqual(records[0].sku_id, "SKU-AUTHENTIC-01")
        self.assertEqual(records[0].quantity_on_hand, 150.5)
        self.assertEqual(records[0].bin_location, "BIN-A-12")
        self.assertIsNotNone(records[0].source_updated_at)

        self.assertEqual(records[1].sku_id, "SKU-PARTIAL-02")
        self.assertIsNone(records[1].quantity_on_hand)
        self.assertIsNone(records[1].bin_location)
        self.assertIsNone(records[1].source_updated_at)

    def test_06_odoo_erp_adapter_zero_fabrication(self) -> None:
        """Verifies that Odoo ERP adapter preserves None for missing costs/dates without defaulting to 0.0 or today."""
        config = ConnectorConfig(
            connector_id="ODOO-TEST-01",
            tenant_id="tenant_odoo",
            adapter_type="erp_odoo",
            name="Odoo ERP Connector",
            base_url="http://localhost:8069",
        )
        connector = OdooErpConnector(config)
        raw_records: List[Dict[str, Any]] = [
            {
                "product_id": [101, "SKU-ERP-FULL"],
                "quantity": "500",
                "standard_price": "24.50",
                "write_date": "2026-08-10",
                "location_id": [1, "WH/Stock"],
            },
            {
                "product_id": [102, "SKU-ERP-MISSING"],
                "location_id": None,
            },
        ]

        transformed = connector.transform(raw_records)
        self.assertEqual(len(transformed), 2)

        self.assertEqual(transformed[0]["sku_id"], "SKU-ERP-FULL")
        self.assertEqual(transformed[0]["inventory_level"], 500.0)
        self.assertEqual(transformed[0]["unit_cost"], 24.50)
        self.assertEqual(transformed[0]["date"], "2026-08-10")

        self.assertEqual(transformed[1]["sku_id"], "SKU-ERP-MISSING")
        self.assertIsNone(transformed[1]["inventory_level"])
        self.assertIsNone(transformed[1]["unit_cost"])
        self.assertIsNone(transformed[1]["date"])

    # =========================================================================
    # 3. ACTION EXECUTION & VERIFICATION GATING
    # =========================================================================

    def test_07_action_execution_transmission_and_verification_pending(self) -> None:
        """Verifies that successful adapter dispatch sets VERIFIED state with audit tracking."""
        action = ActionExecutor.create_action(
            tenant_id="tenant_act",
            action_type=ActionType.TRANSFER_STOCK,
            action_category=ActionCategory.EXECUTABLE,
            entity_type="inventory_levels",
            entity_id="SKU-TRF-01",
            requested_by="user_admin",
            payload={"quantity": 50, "source_location": "WH-1", "destination_location": "WH-2"},
        )

        allowed, _, _ = ActionExecutor.preflight_action(
            self.db, "tenant_act", action.action_id, "user_admin", ["ADMIN"]
        )
        self.assertTrue(allowed)

        res = ActionExecutor.execute_action(
            self.db, "tenant_act", action.action_id, "user_admin", ["ADMIN"]
        )
        self.assertTrue(res.success)
        self.assertEqual(res.execution_state, ActionState.VERIFIED)
        self.assertIsNotNone(res.external_transaction_id)

    def test_08_action_post_approval_tamper_detection(self) -> None:
        """Verifies that mutating an action payload after approval invalidates approval with APPROVAL_INVALIDATED."""
        action = ActionExecutor.create_action(
            tenant_id="tenant_tamper",
            action_type=ActionType.TRANSFER_STOCK,
            action_category=ActionCategory.APPROVAL_REQUIRED,
            entity_type="inventory_levels",
            entity_id="SKU-TAMPER-01",
            requested_by="requester_01",
            payload={"quantity": 10},
        )

        ActionExecutor.preflight_action(
            self.db, "tenant_tamper", action.action_id, "requester_01", ["USER"]
        )

        ActionExecutor.approve_action(
            self.db, "tenant_tamper", action.action_id, "approver_01", "MANAGER"
        )
        self.assertEqual(action.approval_state, ApprovalState.APPROVED)
        self.assertIsNotNone(action.approval_hash)

        action.payload["quantity"] = 10000

        res = ActionExecutor.execute_action(
            self.db, "tenant_tamper", action.action_id, "executor_01", ["MANAGER"]
        )
        self.assertFalse(res.success)
        self.assertEqual(res.execution_state, ActionState.APPROVAL_INVALIDATED)
        self.assertIn("modified after approval", res.message)

    def test_09_action_timeout_simulation_routes_to_external_unknown(self) -> None:
        """Verifies that network timeout simulation cleanly maps to EXTERNAL_UNKNOWN."""
        action = ActionExecutor.create_action(
            tenant_id="tenant_timeout",
            action_type=ActionType.TRANSFER_STOCK,
            action_category=ActionCategory.EXECUTABLE,
            entity_type="inventory_levels",
            entity_id="SKU-TIMEOUT-01",
            requested_by="user_admin",
            payload={"quantity": 20, "simulate_timeout": True},
        )

        ActionExecutor.preflight_action(
            self.db, "tenant_timeout", action.action_id, "user_admin", ["ADMIN"]
        )

        res = ActionExecutor.execute_action(
            self.db, "tenant_timeout", action.action_id, "user_admin", ["ADMIN"]
        )
        self.assertFalse(res.success)
        self.assertEqual(res.execution_state, ActionState.EXTERNAL_UNKNOWN)
        self.assertIn("Manual verification required", res.message)

    # =========================================================================
    # 4. REAL-TIME EVENT ENGINE & QUARANTINE TESTS
    # =========================================================================

    def test_10_event_processing_and_idempotency_suppression(self) -> None:
        """Verifies that duplicate operational events are suppressed via idempotency checks."""
        event = InternalEvent(
            event_id="EVT-IDEM-01",
            tenant_id="tenant_evt",
            source_system="ERP_CONNECTOR",
            event_type=EventTaxonomy.INVENTORY_UPDATED,
            entity_type="inventory_levels",
            entity_id="SKU-EVT-01",
            event_timestamp=datetime.now(timezone.utc).isoformat(),
            payload_hash="hash-12345",
            payload={"new_quantity": 200},
        )

        res1 = EventProcessor.process_event(self.db, event)
        self.assertEqual(res1.status, EventStatus.COMPLETED)

        res2 = EventProcessor.process_event(self.db, event)
        self.assertEqual(res2.status, EventStatus.DUPLICATE)

    def test_11_malformed_event_quarantine(self) -> None:
        """Verifies that invalid events with missing hashes or tenant IDs are moved to quarantine."""
        malformed_event = InternalEvent(
            event_id="EVT-BAD-01",
            tenant_id="",
            source_system="UNKNOWN",
            event_type=EventTaxonomy.INVENTORY_UPDATED,
            entity_type="inventory_levels",
            entity_id="SKU-BAD-01",
            event_timestamp=datetime.now(timezone.utc).isoformat(),
            payload_hash="",
            payload={},
        )

        res = EventProcessor.process_event(self.db, malformed_event)
        self.assertEqual(res.status, EventStatus.QUARANTINED)

        quarantined = EventProcessor.get_quarantined_events("")
        self.assertEqual(len(quarantined), 1)
        self.assertEqual(quarantined[0].event_id, "EVT-BAD-01")

    # =========================================================================
    # 5. PRODUCTION SECURITY FAIL-FAST VALIDATION
    # =========================================================================

    def test_12_production_security_fail_fast(self) -> None:
        """Verifies that production environment raises fatal security validation errors on default secrets."""
        with self.assertRaises(ValueError) as ctx:
            Settings(
                environment="production",
                api_secret_key="aurix-dev-secret-key-default",
            )
        self.assertIn("FATAL SECURITY VIOLATION", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            Settings(
                environment="production",
                api_secret_key="too-short-key",
            )
        self.assertIn("at least 32 characters long", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            Settings(
                environment="production",
                api_secret_key="a-very-secure-randomly-generated-key-for-production-use",
                debug=True,
            )
        self.assertIn("'debug' mode must be disabled", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()