"""Comprehensive Hardening Test Suite for Phase 14 Controlled Decision Execution."""

import unittest
from typing import Any
from fastapi.testclient import TestClient

from aurix_api.app import create_app
from aurix_api.security.auth import create_access_token
from aurix_core.database.engine import Base, SessionLocal, engine
from aurix_core.actions.contracts import ActionCategory, ActionState, ActionType, ApprovalState
from aurix_core.actions.executor import ActionExecutor


class TestPhase14ControlledActionsHardened(unittest.TestCase):
    """Test suite covering Phase 14 hardening: timeouts, approval immutability, conflicts, and tenant isolation."""

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
            "permissions": [
                "READ_DATA",
                "WRITE_DATA",
                "RUN_ANALYSIS",
                "APPROVE_ACTION",
                "EXECUTE_ACTION",
                "VIEW_ACTION",
                "VIEW_ACTION_AUDIT",
            ],
        })

        cls.token_viewer_alpha = create_access_token({
            "sub": "user_viewer_1",
            "tenant_id": "tenant_alpha",
            "roles": ["VIEWER"],
            "permissions": ["READ_DATA", "VIEW_ACTION"],
        })

        cls.token_admin_beta = create_access_token({
            "sub": "user_admin_2",
            "tenant_id": "tenant_beta",
            "roles": ["ADMIN"],
            "permissions": [
                "READ_DATA",
                "WRITE_DATA",
                "RUN_ANALYSIS",
                "APPROVE_ACTION",
                "EXECUTE_ACTION",
                "VIEW_ACTION",
                "VIEW_ACTION_AUDIT",
            ],
        })

    def setUp(self) -> None:
        """Clears in-memory action stores between test runs."""
        ActionExecutor._ACTIONS_STORE.clear()
        ActionExecutor._AUDIT_STORE.clear()

    def test_01_action_creation_and_preflight(self) -> None:
        """Verifies action creation and preflight policy evaluation."""
        payload = {
            "action_type": ActionType.TRANSFER_STOCK.value,
            "action_category": ActionCategory.EXECUTABLE.value,
            "entity_type": "inventory_levels",
            "entity_id": "SKU-500",
            "payload": {"quantity": 50, "unit_price": 20.0, "source_location": "WH-A", "destination_location": "WH-B"},
        }
        res_create = self.client.post(
            "/api/v1/actions",
            json=payload,
            headers={"Authorization": f"Bearer {self.token_admin_alpha}"},
        )
        self.assertEqual(res_create.status_code, 200)
        action_id = res_create.json()["data"]["action_id"]

        res_pre = self.client.post(
            f"/api/v1/actions/{action_id}/preflight",
            headers={"Authorization": f"Bearer {self.token_admin_alpha}"},
        )
        self.assertEqual(res_pre.status_code, 200)
        self.assertTrue(res_pre.json()["data"]["allowed"])

    def test_02_approval_workflow_and_execution(self) -> None:
        """Verifies the complete lifecycle: create -> preflight -> approve -> execute -> verify."""
        db = SessionLocal()
        try:
            action = ActionExecutor.create_action(
                tenant_id="tenant_alpha",
                action_type=ActionType.TRIGGER_REPLENISHMENT,
                action_category=ActionCategory.APPROVAL_REQUIRED,
                entity_type="purchase_orders",
                entity_id="SKU-999",
                requested_by="user_admin_1",
                payload={"quantity": 2000, "unit_price": 50.0, "supplier_id": "SUP-1"},
            )

            allowed, _, _ = ActionExecutor.preflight_action(db, "tenant_alpha", action.action_id, "user_admin_1", ["ADMIN"])
            self.assertTrue(allowed)
            self.assertEqual(action.execution_state, ActionState.PENDING_APPROVAL)

            ActionExecutor.approve_action(db, "tenant_alpha", action.action_id, "user_admin_2", "ADMIN", "Approved for procurement")
            self.assertEqual(action.approval_state, ApprovalState.APPROVED)

            exec_res = ActionExecutor.execute_action(db, "tenant_alpha", action.action_id, "user_admin_1", ["ADMIN"], dry_run=True)
            self.assertTrue(exec_res.success)
            self.assertEqual(exec_res.execution_state, ActionState.VERIFIED)
        finally:
            db.close()

    def test_03_stale_data_policy_block(self) -> None:
        """Verifies that actions with stale freshness timestamps are blocked by the policy engine."""
        db = SessionLocal()
        try:
            action = ActionExecutor.create_action(
                tenant_id="tenant_alpha",
                action_type=ActionType.TRANSFER_STOCK,
                action_category=ActionCategory.EXECUTABLE,
                entity_type="inventory_levels",
                entity_id="SKU-STALE",
                requested_by="user_admin_1",
                payload={"quantity": 10},
            )
            action.freshness_timestamp = "2020-01-01T00:00:00Z"

            allowed, _, policy_res = ActionExecutor.preflight_action(db, "tenant_alpha", action.action_id, "user_admin_1", ["ADMIN"])
            self.assertFalse(allowed)
            assert policy_res is not None
            self.assertFalse(policy_res.is_allowed)
            self.assertIn("freshness", policy_res.block_reason or "")
        finally:
            db.close()

    def test_04_external_unknown_timeout_simulation(self) -> None:
        """Verifies that network timeouts during execution correctly map to EXTERNAL_UNKNOWN."""
        db = SessionLocal()
        try:
            action = ActionExecutor.create_action(
                tenant_id="tenant_alpha",
                action_type=ActionType.TRANSFER_STOCK,
                action_category=ActionCategory.EXECUTABLE,
                entity_type="inventory_levels",
                entity_id="SKU-TIMEOUT",
                requested_by="user_admin_1",
                payload={"quantity": 100, "simulate_timeout": True},
            )
            ActionExecutor.preflight_action(db, "tenant_alpha", action.action_id, "user_admin_1", ["ADMIN"])

            exec_res = ActionExecutor.execute_action(db, "tenant_alpha", action.action_id, "user_admin_1", ["ADMIN"], dry_run=False)
            self.assertFalse(exec_res.success)
            self.assertEqual(exec_res.execution_state, ActionState.EXTERNAL_UNKNOWN)
        finally:
            db.close()

    def test_05_post_approval_mutation_invalidation(self) -> None:
        """Verifies that modifying action payload after approval invalidates approval and blocks execution."""
        db = SessionLocal()
        try:
            action = ActionExecutor.create_action(
                tenant_id="tenant_alpha",
                action_type=ActionType.TRANSFER_STOCK,
                action_category=ActionCategory.APPROVAL_REQUIRED,
                entity_type="inventory_levels",
                entity_id="SKU-MUTATE",
                requested_by="user_admin_1",
                payload={"quantity": 100},
            )
            ActionExecutor.preflight_action(db, "tenant_alpha", action.action_id, "user_admin_1", ["ADMIN"])
            ActionExecutor.approve_action(db, "tenant_alpha", action.action_id, "user_admin_2", "ADMIN")
            self.assertEqual(action.approval_state, ApprovalState.APPROVED)

            # Mutate payload post-approval
            action.payload["quantity"] = 5000

            exec_res = ActionExecutor.execute_action(db, "tenant_alpha", action.action_id, "user_admin_1", ["ADMIN"], dry_run=True)
            self.assertFalse(exec_res.success)
            self.assertEqual(exec_res.execution_state, ActionState.APPROVAL_INVALIDATED)
        finally:
            db.close()

    def test_06_active_action_conflict_detection(self) -> None:
        """Verifies that overlapping active actions on the same entity and type are blocked by policy."""
        db = SessionLocal()
        try:
            action1 = ActionExecutor.create_action(
                tenant_id="tenant_alpha",
                action_type=ActionType.TRANSFER_STOCK,
                action_category=ActionCategory.EXECUTABLE,
                entity_type="inventory_levels",
                entity_id="SKU-CONFLICT",
                requested_by="user_admin_1",
                payload={"quantity": 50},
            )
            ActionExecutor.preflight_action(db, "tenant_alpha", action1.action_id, "user_admin_1", ["ADMIN"])

            # Create conflicting action 2 on same entity & type
            action2 = ActionExecutor.create_action(
                tenant_id="tenant_alpha",
                action_type=ActionType.TRANSFER_STOCK,
                action_category=ActionCategory.EXECUTABLE,
                entity_type="inventory_levels",
                entity_id="SKU-CONFLICT",
                requested_by="user_admin_1",
                payload={"quantity": 100},
            )
            allowed, _, policy_res = ActionExecutor.preflight_action(db, "tenant_alpha", action2.action_id, "user_admin_1", ["ADMIN"])
            self.assertFalse(allowed)
            assert policy_res is not None
            self.assertIn("conflict", policy_res.block_reason or "")
            self.assertEqual(action2.execution_state, ActionState.ACTION_CONFLICT)
        finally:
            db.close()

    def test_07_tenant_isolation(self) -> None:
        """Verifies that Tenant Alpha cannot inspect or approve Tenant Beta's actions."""
        action = ActionExecutor.create_action(
            tenant_id="tenant_beta",
            action_type=ActionType.TRANSFER_STOCK,
            action_category=ActionCategory.EXECUTABLE,
            entity_type="inventory_levels",
            entity_id="SKU-BETA",
            requested_by="user_admin_2",
            payload={"quantity": 5},
        )

        res = self.client.post(
            f"/api/v1/actions/{action.action_id}/preflight",
            headers={"Authorization": f"Bearer {self.token_admin_alpha}"},
        )
        self.assertEqual(res.status_code, 404)


if __name__ == "__main__":
    unittest.main()
