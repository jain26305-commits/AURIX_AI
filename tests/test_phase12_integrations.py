"""Comprehensive Test Suite for Phase 12 Universal Integration & Data Connectivity Hub."""

import hashlib
import hmac
import json
import time
import unittest
from typing import Any, Dict, List
from fastapi.testclient import TestClient

from aurix_api.app import create_app
from aurix_api.security.auth import create_access_token
from aurix_core.integrations.adapters.erp_odoo import OdooErpConnector
from aurix_core.integrations.adapters.generic_rest import GenericRestConnector
from aurix_core.integrations.adapters.generic_sftp import GenericSftpConnector
from aurix_core.integrations.adapters.generic_webhook import GenericWebhookAdapter
from aurix_core.integrations.adapters.test_mock import MockIntegrationConnector
from aurix_core.integrations.adapters.wms_generic import GenericWmsConnector
from aurix_core.integrations.auth import (
    ApiKeyAuthProvider,
    AuthProviderFactory,
    BasicAuthProvider,
    BearerTokenAuthProvider,
    HmacSignatureProvider,
    OAuth2ClientCredentialsProvider,
    SecretResolutionException,
    SecretResolver,
)
from aurix_core.integrations.base import ConnectorException
from aurix_core.integrations.contracts import (
    AuthConfig,
    AuthType,
    ConnectorConfig,
    ConnectorHealthState,
    ConnectorLifecycleState,
    IntegrationFamily,
    ReconciliationStatus,
    SecretRef,
    SyncMode,
    SyncStatus,
    WebhookEventPayload,
)
from aurix_core.integrations.lineage import SourceLineageTracker
from aurix_core.integrations.reconciliation import ReconciliationEngine
from aurix_core.integrations.sync_manager import SyncManager


class TestPhase12Integrations(unittest.TestCase):
    """Integration, security, connector adapters, and reconciliation test suite for Phase 12."""

    app: Any
    client: TestClient
    token_admin_alpha: str
    token_viewer_alpha: str
    token_admin_beta: str

    @classmethod
    def setUpClass(cls) -> None:
        """Initializes FastAPI test client and RBAC authorization tokens."""
        cls.app = create_app()
        cls.client = TestClient(cls.app)

        cls.token_admin_alpha = create_access_token({
            "sub": "admin_user_alpha",
            "tenant_id": "tenant_integ_alpha",
            "roles": ["ADMIN"],
            "permissions": [
                "READ_DATA", "WRITE_DATA", "RUN_ANALYSIS", "USE_AI", "VIEW_FINANCIALS",
                "MANAGE_CONNECTORS", "TRIGGER_SYNC", "VIEW_LINEAGE", "VIEW_RECONCILIATION",
            ],
        })

        cls.token_viewer_alpha = create_access_token({
            "sub": "viewer_user_alpha",
            "tenant_id": "tenant_integ_alpha",
            "roles": ["VIEWER"],
            "permissions": ["READ_DATA"],
        })

        cls.token_admin_beta = create_access_token({
            "sub": "admin_user_beta",
            "tenant_id": "tenant_integ_beta",
            "roles": ["ADMIN"],
            "permissions": [
                "READ_DATA", "WRITE_DATA", "RUN_ANALYSIS",
                "MANAGE_CONNECTORS", "TRIGGER_SYNC", "VIEW_LINEAGE", "VIEW_RECONCILIATION",
            ],
        })

    def setUp(self) -> None:
        """Resets in-memory caches and test stores before each test execution."""
        SecretResolver.clear_test_vault()
        GenericWebhookAdapter.clear_test_buffers()
        GenericSftpConnector.clear_test_files()
        SourceLineageTracker.clear_test_store()
        SyncManager.clear_test_store()

    def test_01_secret_resolution_and_auth_providers(self) -> None:
        """Verifies SecretResolver resolution, AuthProviderFactory, and provider header generation."""
        # 1. Register test secret
        SecretResolver.register_test_secret("erp_api_key", "sec-key-12345")
        secret_val = SecretResolver.resolve(SecretRef(secret_id="erp_api_key"))
        self.assertEqual(secret_val, "sec-key-12345")

        # 2. Unresolved secret raises exception
        with self.assertRaises(SecretResolutionException):
            SecretResolver.resolve(SecretRef(secret_id="non_existent_key"))

        # 3. API Key Auth Provider
        api_key_provider = ApiKeyAuthProvider(key_name="X-API-KEY", key_value="sec-key-12345", in_header=True)
        self.assertEqual(api_key_provider.get_auth_headers(), {"X-API-KEY": "sec-key-12345"})

        # 4. Bearer Token Auth Provider
        bearer_provider = BearerTokenAuthProvider(token="bearer-token-xyz")
        self.assertEqual(bearer_provider.get_auth_headers(), {"Authorization": "Bearer bearer-token-xyz"})

        # 5. HTTP Basic Auth Provider
        basic_provider = BasicAuthProvider(username="odoo_user", password="secret_password")
        auth_header = basic_provider.get_auth_headers().get("Authorization", "")
        self.assertTrue(auth_header.startswith("Basic "))

        # 6. OAuth2 Client Credentials Provider (with mock fallback)
        oauth2_provider = OAuth2ClientCredentialsProvider(
            token_url="mock://auth.server/token",
            client_id="client_abc",
            client_secret="sec_xyz",
            scopes=["read", "write"],
        )
        oauth_headers = oauth2_provider.get_auth_headers()
        self.assertIn("Authorization", oauth_headers)

        # 7. HMAC Signature Provider
        hmac_provider = HmacSignatureProvider(secret_key="my_signing_key")
        hmac_headers = hmac_provider.get_auth_headers(body=b'{"event":"test"}')
        self.assertIn("X-Signature-SHA256", hmac_headers)
        self.assertIn("X-Timestamp", hmac_headers)

        # 8. AuthProviderFactory
        factory_provider = AuthProviderFactory.create(AuthConfig(
            auth_type=AuthType.API_KEY,
            secret_ref=SecretRef(secret_id="erp_api_key", key_name="X-Custom-Key"),
        ))
        self.assertIsInstance(factory_provider, ApiKeyAuthProvider)

    def test_02_connector_lifecycle_and_mock_adapter(self) -> None:
        """Verifies connector state transitions throughout standard synchronization runs."""
        config = ConnectorConfig(
            connector_id="CONN-MOCK-01",
            tenant_id="tenant_integ_alpha",
            name="Mock Connector",
            family=IntegrationFamily.CUSTOM,
            adapter_type="mock",
            custom_settings={"mock_records": [{"sku_id": "SKU-MOCK-1", "quantity": 100}]},
        )
        connector = MockIntegrationConnector(config)

        # Initial state
        self.assertEqual(connector.lifecycle_state, ConnectorLifecycleState.CONFIGURED)
        self.assertEqual(connector.health_check(), ConnectorHealthState.HEALTHY)

        # Execute full sync pass
        records, cursor = connector.execute_sync(mode=SyncMode.INITIAL_FULL)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["sku_id"], "SKU-MOCK-1")
        self.assertEqual(connector.lifecycle_state, ConnectorLifecycleState.COMPLETED)
        self.assertIsNotNone(cursor)

    def test_03_transient_retry_and_exponential_backoff(self) -> None:
        """Verifies SyncManager retrying transient failures and recovering gracefully."""
        config = ConnectorConfig(
            connector_id="CONN-MOCK-RETRY",
            tenant_id="tenant_integ_alpha",
            name="Retry Mock",
            family=IntegrationFamily.REST,
            adapter_type="mock",
            custom_settings={
                "transient_failures_count": 2,  # Fail twice then succeed on 3rd attempt
                "mock_records": [{"sku_id": "SKU-RETRY-1", "date": "2026-01-01", "quantity": 50}],
            },
        )
        connector = MockIntegrationConnector(config)

        # Run sync through SyncManager (max_retries = 3)
        run_record = SyncManager.run_sync(
            connector=connector,
            mode=SyncMode.INCREMENTAL,
            entity_name="demand_history",
        )
        self.assertEqual(run_record.status, SyncStatus.COMPLETED)
        self.assertEqual(run_record.records_accepted, 1)

    def test_04_rate_limiting_and_error_handling(self) -> None:
        """Verifies rate limiting mapping to RATE_LIMITED state without uncaught crashes."""
        config = ConnectorConfig(
            connector_id="CONN-MOCK-429",
            tenant_id="tenant_integ_alpha",
            name="Rate Limited Mock",
            family=IntegrationFamily.REST,
            adapter_type="mock",
            custom_settings={"force_rate_limit": True},
        )
        connector = MockIntegrationConnector(config)

        self.assertEqual(connector.health_check(), ConnectorHealthState.RATE_LIMITED)

        run_record = SyncManager.run_sync(connector=connector)
        self.assertEqual(run_record.status, SyncStatus.FAILED)
        self.assertIn("rate limit", str(run_record.error_summary).lower())

    def test_05_generic_rest_adapter_pagination_and_incremental(self) -> None:
        """Verifies GenericRestConnector pagination, timestamp cursor advancement, and field mapping."""
        mock_data = [
            {"item_num": "SKU-REST-1", "txn_date": "2026-01-01", "sales_units": 150},
            {"item_num": "SKU-REST-2", "txn_date": "2026-01-02", "sales_units": 200},
        ]
        config = ConnectorConfig(
            connector_id="CONN-REST-01",
            tenant_id="tenant_integ_alpha",
            name="REST Adapter",
            family=IntegrationFamily.REST,
            adapter_type="generic_rest",
            base_url="mock://api.external.com",
            custom_settings={
                "mock_records": mock_data,
                "pagination_type": "page",
                "field_mappings": {
                    "item_num": "sku_id",
                    "txn_date": "date",
                    "sales_units": "quantity",
                },
            },
        )
        rest_conn = GenericRestConnector(config)

        # Initial extraction
        records, cursor = rest_conn.execute_sync(mode=SyncMode.INITIAL_FULL)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["sku_id"], "SKU-REST-1")
        self.assertEqual(records[0]["quantity"], 150)
        assert cursor is not None
        self.assertEqual(cursor.get("last_page"), 1)

        # Incremental extraction
        records_inc, cursor_inc = rest_conn.execute_sync(mode=SyncMode.INCREMENTAL, cursor=cursor)
        self.assertEqual(len(records_inc), 2)
        assert cursor_inc is not None
        self.assertEqual(cursor_inc.get("last_page"), 2)

    def test_06_generic_webhook_adapter_hmac_and_replay_protection(self) -> None:
        """Verifies GenericWebhookAdapter HMAC-SHA256 signature verification and replay protection."""
        SecretResolver.register_test_secret("webhook_sig_key", "top-secret-signing-key")

        config = ConnectorConfig(
            connector_id="CONN-WH-01",
            tenant_id="tenant_integ_alpha",
            name="Webhook Adapter",
            family=IntegrationFamily.WEBHOOK,
            adapter_type="generic_webhook",
            auth_config=AuthConfig(
                auth_type=AuthType.HMAC_SIGNATURE,
                secret_ref=SecretRef(secret_id="webhook_sig_key"),
            ),
        )
        wh_adapter = GenericWebhookAdapter(config)

        now_ts = str(int(time.time()))
        payload = {"sku_id": "SKU-WH-1", "inventory_level": 75}
        raw_body = json.dumps(payload).encode("utf-8")

        # 1. Valid Signature Ingestion
        valid_sig = hmac.new(b"top-secret-signing-key", f"{now_ts}.".encode("utf-8") + raw_body, hashlib.sha256).hexdigest()
        event_valid = WebhookEventPayload(
            event_id="EVT-001",
            tenant_id="tenant_integ_alpha",
            source_system="WMS_WEBHOOK",
            connector_id="CONN-WH-01",
            event_type="INVENTORY_UPDATE",
            entity_type="inventory",
            event_timestamp=now_ts,
            payload=payload,
            signature=valid_sig,
            headers={"X-Timestamp": now_ts, "X-Signature-SHA256": valid_sig},
        )
        staged = wh_adapter.ingest_event(event=event_valid, raw_body=raw_body)
        self.assertEqual(staged["sku_id"], "SKU-WH-1")

        # 2. Replay Attack Guard (Duplicate event_id)
        with self.assertRaises(ConnectorException) as ctx:
            wh_adapter.ingest_event(event=event_valid, raw_body=raw_body)
        self.assertEqual(ctx.exception.code, "DUPLICATE_EVENT")

        # 3. Invalid Signature Rejection
        event_invalid = WebhookEventPayload(
            event_id="EVT-002",
            tenant_id="tenant_integ_alpha",
            source_system="WMS_WEBHOOK",
            connector_id="CONN-WH-01",
            event_type="INVENTORY_UPDATE",
            entity_type="inventory",
            event_timestamp=now_ts,
            payload=payload,
            signature="forged_invalid_signature_hex",
            headers={"X-Timestamp": now_ts, "X-Signature-SHA256": "forged_invalid_signature_hex"},
        )
        with self.assertRaises(ConnectorException) as ctx_sig:
            wh_adapter.ingest_event(event=event_invalid, raw_body=raw_body)
        self.assertEqual(ctx_sig.exception.code, "INVALID_SIGNATURE")

        # 4. Drain staged events via fetch_incremental
        drained_records, cursor = wh_adapter.fetch_incremental()
        self.assertEqual(len(drained_records), 1)
        self.assertEqual(drained_records[0]["sku_id"], "SKU-WH-1")

    def test_07_generic_sftp_adapter_and_quarantine(self) -> None:
        """Verifies GenericSftpConnector reading staged files and quarantining corrupted files."""
        config = ConnectorConfig(
            connector_id="CONN-SFTP-01",
            tenant_id="tenant_integ_alpha",
            name="SFTP File Hub",
            family=IntegrationFamily.SFTP,
            adapter_type="generic_sftp",
        )
        sftp_conn = GenericSftpConnector(config)

        # Stage 1 valid CSV file and 1 corrupted file
        valid_csv = b"SKU,DATE,DEMAND\nSKU-SFTP-1,2026-01-01,300\nSKU-SFTP-2,2026-01-01,450\n"
        GenericSftpConnector.stage_mock_remote_file("CONN-SFTP-01", "demand_batch.csv", valid_csv)
        GenericSftpConnector.stage_mock_remote_file("CONN-SFTP-01", "corrupt_data.exe", b"MZ\x90\x00corrupt")

        records, cursor = sftp_conn.fetch_incremental()
        self.assertEqual(len(records), 2)
        assert cursor is not None
        self.assertEqual(cursor.get("processed_files_count"), 1)
        self.assertEqual(records[0]["SKU"], "SKU-SFTP-1")

    def test_08_erp_and_wms_adapters_normalization(self) -> None:
        """Verifies Odoo ERP and Generic WMS adapters converting source schemas to canonical entities."""
        # 1. Odoo ERP normalization
        odoo_config = ConnectorConfig(
            connector_id="CONN-ODOO-01",
            tenant_id="tenant_integ_alpha",
            name="Odoo ERP",
            family=IntegrationFamily.ERP,
            adapter_type="erp_odoo",
            custom_settings={
                "mock_dataset": [
                    {
                        "product_id": [101, "SKU-ODOO-1"],
                        "quantity": 500.0,
                        "write_date": "2026-02-01",
                        "standard_price": 25.50,
                        "location_id": [5, "WH/Stock"],
                    }
                ]
            },
        )
        odoo_conn = OdooErpConnector(odoo_config)
        odoo_records, _ = odoo_conn.execute_sync()
        self.assertEqual(len(odoo_records), 1)
        self.assertEqual(odoo_records[0]["sku_id"], "SKU-ODOO-1")
        self.assertEqual(odoo_records[0]["inventory_level"], 500.0)
        self.assertEqual(odoo_records[0]["unit_cost"], 25.50)

        # 2. Generic WMS normalization (deducting allocated/reserved stock)
        wms_config = ConnectorConfig(
            connector_id="CONN-WMS-01",
            tenant_id="tenant_integ_alpha",
            name="WMS Warehouse",
            family=IntegrationFamily.WMS,
            adapter_type="wms_generic",
            custom_settings={
                "mock_dataset": [
                    {
                        "item_code": "SKU-WMS-1",
                        "on_hand_qty": 300.0,
                        "reserved_qty": 50.0,  # Available should be 250.0
                        "snapshot_date": "2026-02-01",
                        "facility": "EAST_DC",
                        "bin_id": "BIN-A-12",
                    }
                ]
            },
        )
        wms_conn = GenericWmsConnector(wms_config)
        wms_records, _ = wms_conn.execute_sync()
        self.assertEqual(len(wms_records), 1)
        self.assertEqual(wms_records[0]["sku_id"], "SKU-WMS-1")
        self.assertEqual(wms_records[0]["inventory_level"], 250.0)

    def test_09_multi_source_reconciliation_and_domain_priority(self) -> None:
        """Verifies ReconciliationEngine classifying variances and applying domain priority rules."""
        # 1. Exact Match
        _, _, stat_match = ReconciliationEngine.compare_numeric_values(100.0, 100.0)
        self.assertEqual(stat_match, ReconciliationStatus.MATCHED)

        # 2. Minor Variance (e.g. 2% variance with 5% threshold)
        _, var_pct, stat_minor = ReconciliationEngine.compare_numeric_values(100.0, 98.0, material_threshold_pct=5.0)
        self.assertEqual(stat_minor, ReconciliationStatus.MINOR_VARIANCE)
        self.assertEqual(var_pct, 2.0)

        # 3. Material Variance (e.g. 100 vs 85 = 15% variance)
        _, _, stat_mat = ReconciliationEngine.compare_numeric_values(100.0, 85.0, material_threshold_pct=5.0)
        self.assertEqual(stat_mat, ReconciliationStatus.MATERIAL_VARIANCE)

        # 4. Batch Dataset Reconciliation with Domain Priority (Inventory: WMS > ERP)
        erp_data = [{"sku_id": "SKU-REC-1", "inventory_level": 1000.0}]
        wms_data = [{"sku_id": "SKU-REC-1", "inventory_level": 950.0}]  # 5% variance

        reconciled_rows, audit_records = ReconciliationEngine.reconcile_datasets(
            tenant_id="tenant_integ_alpha",
            entity_type="inventory",
            dataset_a=erp_data,
            source_a="ERP",
            dataset_b=wms_data,
            source_b="WMS",
            key_field="sku_id",
            metric_field="inventory_level",
        )
        self.assertEqual(len(reconciled_rows), 1)
        self.assertEqual(len(audit_records), 1)
        # Should resolve to WMS (950.0) based on domain priority
        self.assertEqual(reconciled_rows[0]["inventory_level"], 950.0)
        self.assertIn("WMS", audit_records[0].resolution_applied or "")

    def test_10_source_lineage_tracker_provenance(self) -> None:
        """Verifies SourceLineageTracker recording and querying source-to-canonical provenance."""
        records = [
            {"id": "ERP-ROW-991", "sku_id": "SKU-CANON-1", "date": "2026-01-01"},
            {"id": "ERP-ROW-992", "sku_id": "SKU-CANON-2", "date": "2026-01-01"},
        ]
        lineage_entries = SourceLineageTracker.track_batch(
            tenant_id="tenant_integ_alpha",
            source_system="ERP_SAP",
            connector_id="CONN-SAP-01",
            canonical_entity="demand_history",
            sync_run_id="SYNC-RUN-888",
            records=records,
            source_id_field="id",
            canonical_id_field="sku_id",
        )
        self.assertEqual(len(lineage_entries), 2)

        # Query by canonical ID
        canon_lineage = SourceLineageTracker.get_lineage_by_canonical_id(
            tenant_id="tenant_integ_alpha",
            canonical_entity="demand_history",
            canonical_record_id="SKU-CANON-1",
        )
        self.assertEqual(len(canon_lineage), 1)
        self.assertEqual(canon_lineage[0].source_record_id, "ERP-ROW-991")

        # Query by sync run ID
        run_lineage = SourceLineageTracker.get_lineage_by_sync_run(
            tenant_id="tenant_integ_alpha",
            sync_run_id="SYNC-RUN-888",
        )
        self.assertEqual(len(run_lineage), 2)

    def test_11_end_to_end_sync_to_capability_refresh(self) -> None:
        """Verifies SyncManager triggering Phase 11 quality validation and Phase 9 capability discovery."""
        config = ConnectorConfig(
            connector_id="CONN-E2E-01",
            tenant_id="tenant_integ_alpha",
            name="E2E Connector",
            family=IntegrationFamily.REST,
            adapter_type="mock",
            custom_settings={
                "mock_records": [
                    {"sku_id": "SKU-E2E-1", "date": "2026-01-01", "quantity": 100},
                    {"sku_id": "SKU-E2E-1", "date": "2026-02-01", "quantity": 120},
                    {"sku_id": "SKU-E2E-1", "date": "2026-03-01", "quantity": -10},  # Negative quantity rejected
                ]
            },
        )
        connector = MockIntegrationConnector(config)

        run_record = SyncManager.run_sync(
            connector=connector,
            mode=SyncMode.INITIAL_FULL,
            entity_name="demand_history",
            key_field="sku_id",
        )

        self.assertEqual(run_record.status, SyncStatus.PARTIAL_SUCCESS)
        self.assertEqual(run_record.records_received, 3)
        self.assertEqual(run_record.records_accepted, 2)
        self.assertEqual(run_record.records_rejected, 1)
        self.assertIn("DEMAND_CLASSIFICATION", run_record.affected_capabilities)

    def test_12_api_connector_management_and_sync(self) -> None:
        """Verifies API endpoints for connector CRUD, sync triggers, health checks, and reconciliation."""
        # 1. Register connector via API
        create_payload = {
            "name": "API Live Connector",
            "family": "REST",
            "adapter_type": "mock",
            "custom_settings": {
                "mock_records": [{"sku_id": "SKU-API-1", "date": "2026-01-01", "quantity": 250}]
            },
        }
        res_create = self.client.post(
            "/api/v1/integrations/connectors",
            json=create_payload,
            headers={"Authorization": f"Bearer {self.token_admin_alpha}"},
        )
        self.assertEqual(res_create.status_code, 200)
        connector_id = res_create.json()["data"]["connector_id"]

        # 2. Get Connector Details
        res_get = self.client.get(
            f"/api/v1/integrations/connectors/{connector_id}",
            headers={"Authorization": f"Bearer {self.token_admin_alpha}"},
        )
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["data"]["name"], "API Live Connector")

        # 3. Trigger Sync via API
        sync_payload = {"mode": "INITIAL_FULL", "entity_name": "demand_history"}
        res_sync = self.client.post(
            f"/api/v1/integrations/connectors/{connector_id}/sync",
            json=sync_payload,
            headers={"Authorization": f"Bearer {self.token_admin_alpha}"},
        )
        self.assertEqual(res_sync.status_code, 200)
        self.assertEqual(res_sync.json()["data"]["records_accepted"], 1)

        # 4. Check Health Endpoint
        res_health = self.client.get(
            f"/api/v1/integrations/connectors/{connector_id}/health",
            headers={"Authorization": f"Bearer {self.token_admin_alpha}"},
        )
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.json()["data"]["health_state"], "HEALTHY")

        # 5. Dataset Reconciliation via API
        rec_payload = {
            "entity_type": "inventory",
            "dataset_a": [{"sku_id": "SKU-API-REC", "inventory_level": 500.0}],
            "source_a": "ERP",
            "dataset_b": [{"sku_id": "SKU-API-REC", "inventory_level": 490.0}],
            "source_b": "WMS",
        }
        res_rec = self.client.post(
            "/api/v1/integrations/reconcile",
            json=rec_payload,
            headers={"Authorization": f"Bearer {self.token_admin_alpha}"},
        )
        self.assertEqual(res_rec.status_code, 200)
        self.assertEqual(res_rec.json()["data"]["total_entities_evaluated"], 1)

    def test_13_tenant_isolation_and_rbac_security(self) -> None:
        """Verifies unauthenticated rejection, viewer permission blocks, and cross-tenant isolation."""
        # 1. Unauthenticated rejection
        res_unauth = self.client.post("/api/v1/integrations/connectors", json={"name": "Test"})
        self.assertEqual(res_unauth.status_code, 401)

        # 2. Viewer role rejection for MANAGE_CONNECTORS permission
        res_viewer = self.client.post(
            "/api/v1/integrations/connectors",
            json={"name": "Forbidden Connector", "adapter_type": "mock"},
            headers={"Authorization": f"Bearer {self.token_viewer_alpha}"},
        )
        self.assertEqual(res_viewer.status_code, 403)

        # 3. Cross-Tenant Isolation: Create connector in Tenant Alpha, attempt access from Tenant Beta
        create_res = self.client.post(
            "/api/v1/integrations/connectors",
            json={"name": "Tenant Alpha Connector", "adapter_type": "mock"},
            headers={"Authorization": f"Bearer {self.token_admin_alpha}"},
        )
        alpha_conn_id = create_res.json()["data"]["connector_id"]

        # Tenant Beta gets 404 Not Found when attempting to access Tenant Alpha connector
        res_cross = self.client.get(
            f"/api/v1/integrations/connectors/{alpha_conn_id}",
            headers={"Authorization": f"Bearer {self.token_admin_beta}"},
        )
        self.assertEqual(res_cross.status_code, 404)


if __name__ == "__main__":
    unittest.main()