"""Comprehensive Test Suite for Phase 15 Production Hardening, MLOps Registry, and Telemetry."""

import logging
import os
import tempfile
import unittest
from datetime import datetime, timezone
from typing import Any, Dict, List

from aurix_core.database.engine import Base, SessionLocal, engine
from aurix_core.maintenance.retention import DataRetentionEngine
from aurix_core.mlops.registry import ModelRegistry
from aurix_core.observability.logging import StructuredJsonFormatter
from aurix_core.observability.metrics import MetricsRegistry


class TestPhase15ProductionHardening(unittest.TestCase):
    """Test suite covering Phase 15 hardening: logging, metrics, MLOps, degradation, and retention."""

    @classmethod
    def setUpClass(cls) -> None:
        """Initializes database tables for retention tests."""
        Base.metadata.create_all(bind=engine)

    def setUp(self) -> None:
        """Resets metrics registry before each test."""
        MetricsRegistry.reset()

    def test_01_structured_logging_and_scrubbing(self) -> None:
        """Verifies structured JSON log formatting and recursive secret scrubbing across nested structures."""
        formatter = StructuredJsonFormatter()
        record = logging.LogRecord(
            name="aurix.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="Test authentication attempt",
            args={
                "username": "admin",
                "password": "super-secret-password-123",
                "token": "jwt-token-xyz",
                "nested": {"api_key": "secret-api-key-999", "public_info": "safe_data"},
            },
            exc_info=None,
        )
        setattr(record, "tenant_id", "tenant_alpha")
        setattr(record, "correlation_id", "corr-12345")

        formatted_json = formatter.format(record)
        self.assertIn("tenant_alpha", formatted_json)
        self.assertIn("corr-12345", formatted_json)
        self.assertIn("[REDACTED]", formatted_json)
        self.assertIn("safe_data", formatted_json)
        self.assertNotIn("super-secret-password-123", formatted_json)
        self.assertNotIn("jwt-token-xyz", formatted_json)
        self.assertNotIn("secret-api-key-999", formatted_json)

    def test_02_metrics_collector(self) -> None:
        """Verifies thread-safe metrics collector incrementing and cost calculations."""
        MetricsRegistry.increment_api_request(is_error=False, latency_seconds=0.05)
        MetricsRegistry.increment_api_request(is_error=True, latency_seconds=0.20)
        MetricsRegistry.record_ai_usage(input_tokens=1000, output_tokens=500, provider="gemini")
        MetricsRegistry.record_action_lifecycle("APPROVED")

        snapshot = MetricsRegistry.get_snapshot()
        self.assertGreaterEqual(snapshot.api_requests_total, 2)
        self.assertGreaterEqual(snapshot.api_errors_total, 1)
        self.assertEqual(snapshot.ai_tokens_input_total, 1000)
        self.assertEqual(snapshot.ai_tokens_output_total, 500)
        self.assertGreater(snapshot.ai_estimated_cost_usd, 0.0)
        self.assertEqual(snapshot.actions_approved_total, 1)

    def test_03_model_registry_lifecycle_and_integrity(self) -> None:
        """Verifies model artifact registration, checksum hashing, champion promotion, and integrity checks."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".bin") as tmp:
            tmp.write("dummy model weights content for testing")
            tmp_path = tmp.name

        try:
            # Register artifact
            artifact = ModelRegistry.register_artifact(
                tenant_id="tenant_alpha",
                model_type="DEMAND_FORECAST",
                version="1.0.0",
                artifact_path=tmp_path,
                metrics={"mape": 4.5, "rmse": 1.2},
                training_run_id="RUN-999",
            )
            self.assertEqual(artifact.status, "REGISTERED")
            self.assertFalse(artifact.is_champion)
            self.assertEqual(len(artifact.checksum), 64)  # SHA-256 hex length

            # Promote to champion
            promoted = ModelRegistry.promote_to_champion("tenant_alpha", artifact.artifact_id)
            self.assertTrue(promoted.is_champion)
            self.assertEqual(promoted.status, "CHAMPION")

            champ = ModelRegistry.get_champion("tenant_alpha", "DEMAND_FORECAST")
            self.assertIsNotNone(champ)
            assert champ is not None
            self.assertEqual(champ.artifact_id, artifact.artifact_id)

            # Verify integrity
            is_valid = ModelRegistry.verify_artifact_integrity("tenant_alpha", artifact.artifact_id)
            self.assertTrue(is_valid)

            # Tamper file and check integrity violation
            with open(tmp_path, "w") as f:
                f.write("tampered malicious model weights")

            is_valid_after_tamper = ModelRegistry.verify_artifact_integrity("tenant_alpha", artifact.artifact_id)
            self.assertFalse(is_valid_after_tamper)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_04_model_evaluation_and_degradation_monitoring(self) -> None:
        """Verifies forecast error calculations and automated model degradation detection."""
        actuals = [100.0, 120.0, 110.0, 130.0, 105.0]
        forecasts = [102.0, 118.0, 112.0, 128.0, 106.0]

        # 1. Performance Evaluation
        eval_res = ModelRegistry.evaluate_performance(actuals, forecasts)
        self.assertGreater(eval_res.mae, 0.0)
        self.assertGreater(eval_res.rmse, 0.0)
        self.assertGreater(eval_res.mape, 0.0)
        self.assertEqual(eval_res.sample_count, 5)

        # 2. Degradation Detection
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".bin") as tmp:
            tmp.write("model_data")
            tmp_path = tmp.name

        try:
            artifact = ModelRegistry.register_artifact(
                tenant_id="tenant_alpha",
                model_type="DEMAND_FORECAST",
                version="1.0.0",
                artifact_path=tmp_path,
                metrics={"mape": 1.5},  # Baseline 1.5% MAPE
            )

            # Severely degraded forecasts
            degraded_forecasts = [160.0, 190.0, 175.0, 210.0, 170.0]
            deg_report = ModelRegistry.check_model_degradation(
                tenant_id="tenant_alpha",
                artifact_id=artifact.artifact_id,
                actuals=actuals,
                forecasts=degraded_forecasts,
                max_degradation_pct=25.0,
            )

            self.assertTrue(deg_report.is_degraded)
            self.assertGreater(deg_report.degradation_pct, 25.0)
            self.assertIn("Retraining or rollback advised", deg_report.recommendation)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_05_champion_rollback_workflow(self) -> None:
        """Verifies automated rollback to prior champion model when active model degrades."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".bin") as tmp1:
            tmp1.write("v1_weights")
            path1 = tmp1.name

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".bin") as tmp2:
            tmp2.write("v2_weights")
            path2 = tmp2.name

        try:
            # Register v1 and promote to Champion
            art1 = ModelRegistry.register_artifact(
                tenant_id="tenant_alpha",
                model_type="DEMAND_FORECAST",
                version="1.0.0",
                artifact_path=path1,
                metrics={"mape": 2.5},
            )
            ModelRegistry.promote_to_champion("tenant_alpha", art1.artifact_id)

            # Register v2 and promote to Champion (v1 becomes ARCHIVED)
            art2 = ModelRegistry.register_artifact(
                tenant_id="tenant_alpha",
                model_type="DEMAND_FORECAST",
                version="2.0.0",
                artifact_path=path2,
                metrics={"mape": 1.8},
            )
            ModelRegistry.promote_to_champion("tenant_alpha", art2.artifact_id)

            champ_now = ModelRegistry.get_champion("tenant_alpha", "DEMAND_FORECAST")
            self.assertIsNotNone(champ_now)
            assert champ_now is not None
            self.assertEqual(champ_now.artifact_id, art2.artifact_id)

            # Execute Rollback
            restored_champion = ModelRegistry.rollback_to_previous_champion("tenant_alpha", "DEMAND_FORECAST")
            self.assertIsNotNone(restored_champion)
            assert restored_champion is not None
            self.assertEqual(restored_champion.artifact_id, art1.artifact_id)
            self.assertTrue(restored_champion.is_champion)
            self.assertEqual(restored_champion.status, "CHAMPION")

            # Verify art2 was marked as ROLLED_BACK
            art2_record = ModelRegistry._REGISTRY_STORE["tenant_alpha"][art2.artifact_id]
            self.assertFalse(art2_record.is_champion)
            self.assertEqual(art2_record.status, "ROLLED_BACK")
        finally:
            for p in [path1, path2]:
                if os.path.exists(p):
                    os.unlink(p)

    def test_06_data_retention_and_minimization_sweep(self) -> None:
        """Verifies that data retention sweeps prune aged archived artifacts while strictly protecting champions."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".bin") as tmp_archived:
            tmp_archived.write("archived_old_model")
            path_archived = tmp_archived.name

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".bin") as tmp_champ:
            tmp_champ.write("active_champion_model")
            path_champ = tmp_champ.name

        try:
            # 1. Register archived model aged 200 days ago (threshold is 180 days)
            art_old = ModelRegistry.register_artifact(
                tenant_id="tenant_alpha",
                model_type="DEMAND_FORECAST",
                version="0.9.0",
                artifact_path=path_archived,
                metrics={"mape": 5.0},
            )
            art_old.created_at = "2020-01-01T00:00:00Z"
            art_old.status = "ARCHIVED"

            # 2. Register champion model
            art_champ = ModelRegistry.register_artifact(
                tenant_id="tenant_alpha",
                model_type="DEMAND_FORECAST",
                version="1.0.0",
                artifact_path=path_champ,
                metrics={"mape": 2.0},
            )
            ModelRegistry.promote_to_champion("tenant_alpha", art_champ.artifact_id)

            # 3. Execute retention sweep
            db = SessionLocal()
            try:
                report = DataRetentionEngine.execute_retention_sweep(db, "tenant_alpha", dry_run=False)
                self.assertEqual(report.artifacts_pruned, 1)
                self.assertGreater(report.freed_disk_bytes, 0)

                # Confirm old artifact was removed from filesystem and registry
                self.assertFalse(os.path.exists(path_archived))
                self.assertNotIn(art_old.artifact_id, ModelRegistry._REGISTRY_STORE.get("tenant_alpha", {}))

                # Confirm champion model was strictly preserved
                self.assertTrue(os.path.exists(path_champ))
                self.assertIn(art_champ.artifact_id, ModelRegistry._REGISTRY_STORE.get("tenant_alpha", {}))
            finally:
                db.close()
        finally:
            for p in [path_archived, path_champ]:
                if os.path.exists(p):
                    os.unlink(p)


if __name__ == "__main__":
    unittest.main()