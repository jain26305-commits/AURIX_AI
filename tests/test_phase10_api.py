"""Comprehensive Integration and Security Test Suite for Phase 10 Application API Platform."""

import unittest
from typing import Any
from fastapi.testclient import TestClient

from aurix_api.app import create_app
from aurix_api.security.auth import create_access_token
from aurix_core.database.engine import Base, engine


class TestPhase10APIPlatform(unittest.TestCase):
    """Integration test suite covering security, RBAC, tenant isolation, and API route behaviors."""

    app: Any
    client: TestClient
    token_admin_alpha: str
    token_viewer_alpha: str
    token_admin_beta: str

    @classmethod
    def setUpClass(cls) -> None:
        """Configures test application, database tables, and authorized test tokens."""
        Base.metadata.create_all(bind=engine)
        cls.app = create_app()
        cls.client = TestClient(cls.app)

        # Generate cryptographic tokens for testing across tenants and roles
        cls.token_admin_alpha = create_access_token({
            "sub": "user_admin_1",
            "tenant_id": "tenant_alpha",
            "roles": ["ADMIN"],
            "permissions": ["READ_DATA", "RUN_ANALYSIS", "WRITE_DATA", "USE_AI", "VIEW_FINANCIALS"],
        })

        cls.token_viewer_alpha = create_access_token({
            "sub": "user_viewer_1",
            "tenant_id": "tenant_alpha",
            "roles": ["VIEWER"],
            "permissions": ["READ_DATA"],
        })

        cls.token_admin_beta = create_access_token({
            "sub": "user_admin_2",
            "tenant_id": "tenant_beta",
            "roles": ["ADMIN"],
            "permissions": ["READ_DATA", "RUN_ANALYSIS", "WRITE_DATA", "USE_AI", "VIEW_FINANCIALS"],
        })

    def test_01_health_endpoints(self) -> None:
        """Verifies liveness and readiness probes return 200 OK."""
        res_live = self.client.get("/api/v1/health/live")
        if res_live.status_code == 404:
            res_live = self.client.get("/health/live")
        self.assertEqual(res_live.status_code, 200)
        self.assertEqual(res_live.json()["status"], "SUCCESS")

        res_ready = self.client.get("/api/v1/health/ready")
        if res_ready.status_code == 404:
            res_ready = self.client.get("/health/ready")
        self.assertEqual(res_ready.status_code, 200)
        self.assertEqual(res_ready.json()["status"], "SUCCESS")

    def test_02_authentication_failures(self) -> None:
        """Verifies that protected routes reject missing or malformed tokens with 401."""
        res = self.client.get("/api/v1/capabilities")
        self.assertEqual(res.status_code, 401)

        res_bad = self.client.get(
            "/api/v1/capabilities",
            headers={"Authorization": "Bearer invalid.fake.token"},
        )
        self.assertEqual(res_bad.status_code, 401)

    def test_03_rbac_and_permissions(self) -> None:
        """Verifies that viewers cannot execute runs or ingest data (403 Forbidden)."""
        res = self.client.post(
            "/api/v1/runs",
            json={"execution_mode": "SYNCHRONOUS"},
            headers={"Authorization": f"Bearer {self.token_viewer_alpha}"},
        )
        self.assertEqual(res.status_code, 403)

        res_caps = self.client.get(
            "/api/v1/capabilities",
            headers={"Authorization": f"Bearer {self.token_admin_alpha}"},
        )
        self.assertEqual(res_caps.status_code, 200)

    def test_04_tenant_isolation(self) -> None:
        """Verifies strict tenant isolation (Tenant Alpha cannot inspect Tenant Beta resources)."""
        res_run = self.client.post(
            "/api/v1/runs",
            json={"execution_mode": "SYNCHRONOUS"},
            headers={"Authorization": f"Bearer {self.token_admin_alpha}"},
        )
        self.assertEqual(res_run.status_code, 200)
        run_id = res_run.json()["data"]["run_id"]

        res_beta = self.client.get(
            f"/api/v1/runs/{run_id}",
            headers={"Authorization": f"Bearer {self.token_admin_beta}"},
        )
        self.assertEqual(res_beta.status_code, 404)

    def test_05_data_ingestion_and_readiness(self) -> None:
        """Verifies canonical data submission and dataset readiness evaluation."""
        payload = {
            "entity_name": "demand_history",
            "records": [
                {"sku_id": "SKU-TEST-1", "date": "2026-08-14", "quantity": 150.0}
            ],
        }
        res = self.client.post(
            "/api/v1/data/ingest",
            json=payload,
            headers={"Authorization": f"Bearer {self.token_admin_alpha}"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["data"]["total_accepted"], 1)

        res_readiness = self.client.get(
            "/api/v1/data/readiness",
            headers={"Authorization": f"Bearer {self.token_viewer_alpha}"},
        )
        self.assertEqual(res_readiness.status_code, 200)
        self.assertIn("demand_history", res_readiness.json()["data"]["entities"])

    def test_06_capability_discovery(self) -> None:
        """Verifies portfolio capability discovery endpoint."""
        res = self.client.get(
            "/api/v1/capabilities",
            headers={"Authorization": f"Bearer {self.token_viewer_alpha}"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("DEMAND_CLASSIFICATION", res.json()["data"]["capabilities"])

    def test_07_run_lifecycle_and_idempotency(self) -> None:
        """Verifies run execution, history listing, and SHA-256 idempotency."""
        req_data = {
            "execution_mode": "SYNCHRONOUS",
            "canonical_datasets": {
                "demand_history": [
                    {"sku_id": "SKU-IDEM", "date": "2026-08-14", "quantity": 200.0}
                ]
            },
        }

        res1 = self.client.post(
            "/api/v1/runs",
            json=req_data,
            headers={"Authorization": f"Bearer {self.token_admin_alpha}"},
        )
        self.assertEqual(res1.status_code, 200)
        run_id_1 = res1.json()["data"]["run_id"]

        res2 = self.client.post(
            "/api/v1/runs",
            json=req_data,
            headers={"Authorization": f"Bearer {self.token_admin_alpha}"},
        )
        self.assertEqual(res2.status_code, 200)
        self.assertTrue(res2.json()["data"]["idempotent_hit"])
        self.assertEqual(run_id_1, res2.json()["data"]["run_id"])

        res_list = self.client.get(
            "/api/v1/runs",
            headers={"Authorization": f"Bearer {self.token_admin_alpha}"},
        )
        self.assertEqual(res_list.status_code, 200)
        self.assertGreaterEqual(res_list.json()["data"]["total_count"], 1)

    def test_08_domain_analytics_endpoints(self) -> None:
        """Verifies domain analytics read routes."""
        for endpoint in ["demand", "forecast", "inventory", "supply", "logistics", "network", "economics"]:
            res = self.client.get(
                f"/api/v1/{endpoint}",
                headers={"Authorization": f"Bearer {self.token_admin_alpha}"},
            )
            self.assertEqual(res.status_code, 200, f"Failed on endpoint: /api/v1/{endpoint}")

    def test_09_executive_intelligence_endpoints(self) -> None:
        """Verifies intelligence endpoints."""
        for subpath in ["signals", "actions", "summary", "snapshot"]:
            res = self.client.get(
                f"/api/v1/intelligence/{subpath}",
                headers={"Authorization": f"Bearer {self.token_admin_alpha}"},
            )
            self.assertEqual(res.status_code, 200, f"Failed on endpoint: /api/v1/intelligence/{subpath}")

    def test_10_grounded_ai_copilot_endpoint(self) -> None:
        """Verifies grounded AI Copilot query endpoint and page context mapping."""
        ai_payload = {
            "query": "What is the inventory position for SKU-TEST-1?",
            "page_context": {
                "current_page": "Inventory Overview",
                "active_entity_id": "SKU-TEST-1",
            },
        }
        res = self.client.post(
            "/api/v1/ai/query",
            json=ai_payload,
            headers={"Authorization": f"Bearer {self.token_admin_alpha}"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("headline", res.json()["data"])


if __name__ == "__main__":
    unittest.main()