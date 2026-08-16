"""Comprehensive Disaster Recovery, Backup, Restore, and State Integrity Verification Test Suite."""

import os
import shutil
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from aurix_api.runs.manager import RunManager, RunStatus
from aurix_core.actions.contracts import ActionCategory, ActionState, ActionType
from aurix_core.actions.executor import ActionExecutor
from aurix_core.database.engine import Base
from aurix_core.mlops.registry import ModelRegistry


class TestPhase15DisasterRecovery(unittest.TestCase):
    """Validates database snapshot backup, isolated restore, and state integrity across tenant boundaries."""

    temp_dir: str
    source_db_path: str
    backup_db_path: str
    restore_db_path: str

    def setUp(self) -> None:
        """Sets up isolated temporary databases and clears operational stores."""
        self.temp_dir = tempfile.mkdtemp(prefix="aurix_dr_test_")
        self.source_db_path = os.path.join(self.temp_dir, "source_aurix.db")
        self.backup_db_path = os.path.join(self.temp_dir, "backup_aurix.db")
        self.restore_db_path = os.path.join(self.temp_dir, "restored_aurix.db")

        ActionExecutor._ACTIONS_STORE.clear()
        ActionExecutor._AUDIT_STORE.clear()
        RunManager._RUNS_STORE.clear()
        ModelRegistry._REGISTRY_STORE.clear()

    def tearDown(self) -> None:
        """Cleans up temporary directory and files."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_database_snapshot_backup_and_restore_integrity(self) -> None:
        """
        Simulates primary database snapshot creation, external restore into an isolated environment,
        and validates that tenant data, table schemas, and relational records survive intact.
        """
        # 1. Initialize Source Database Engine
        source_engine = create_engine(f"sqlite:///{self.source_db_path}")
        Base.metadata.create_all(bind=source_engine)
        SourceSession = sessionmaker(bind=source_engine)

        # 2. Populate Source Database with Mock Operational Records
        with SourceSession() as session:
            session.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS tenant_audit_log ("
                    "id INTEGER PRIMARY KEY, "
                    "tenant_id TEXT, "
                    "event_type TEXT, "
                    "created_at TEXT)"
                )
            )
            session.execute(
                text(
                    "INSERT INTO tenant_audit_log (tenant_id, event_type, created_at) "
                    "VALUES ('tenant_alpha', 'INVENTORY_REBALANCE', '2026-08-14T12:00:00Z')"
                )
            )
            session.execute(
                text(
                    "INSERT INTO tenant_audit_log (tenant_id, event_type, created_at) "
                    "VALUES ('tenant_beta', 'STOCK_TRANSFER', '2026-08-14T12:05:00Z')"
                )
            )
            session.commit()

        # 3. Perform Consistent Backup (SQLite Backup API simulation)
        src_conn = sqlite3.connect(self.source_db_path)
        dst_conn = sqlite3.connect(self.backup_db_path)
        with dst_conn:
            src_conn.backup(dst_conn)
        src_conn.close()
        dst_conn.close()

        self.assertTrue(os.path.exists(self.backup_db_path))
        self.assertGreater(os.path.getsize(self.backup_db_path), 0)

        # 4. Restore into a Completely Isolated Target Database Environment
        shutil.copyfile(self.backup_db_path, self.restore_db_path)
        self.assertTrue(os.path.exists(self.restore_db_path))

        # 5. Connect to Restored Database and Validate State Integrity
        restore_engine = create_engine(f"sqlite:///{self.restore_db_path}")
        RestoreSession = sessionmaker(bind=restore_engine)

        with RestoreSession() as session:
            result = session.execute(
                text("SELECT tenant_id, event_type FROM tenant_audit_log ORDER BY id ASC")
            ).fetchall()

            self.assertEqual(len(result), 2)
            self.assertEqual(result[0][0], "tenant_alpha")
            self.assertEqual(result[0][1], "INVENTORY_REBALANCE")
            self.assertEqual(result[1][0], "tenant_beta")
            self.assertEqual(result[1][1], "STOCK_TRANSFER")

    def test_02_operational_state_and_worker_recovery(self) -> None:
        """
        Simulates worker crash reconciliation across active analytical runs.
        """
        # Create active runs in tenant_alpha
        run1 = RunManager.create_run(tenant_id="tenant_alpha", capability_name="DEMAND_FORECAST")
        RunManager.start_run(tenant_id="tenant_alpha", run_id=run1.run_id)

        run2 = RunManager.create_run(tenant_id="tenant_alpha", capability_name="SAFETY_STOCK")

        # Artificially age the heartbeat of run1 and creation timestamp of run2
        run1_record = RunManager.get_run("tenant_alpha", run1.run_id)
        run1_record.heartbeat_at = "2026-01-01T00:00:00Z"

        run2_record = RunManager.get_run("tenant_alpha", run2.run_id)
        run2_record.created_at = "2026-01-01T00:00:00Z"
        run2_record.heartbeat_at = None

        # Execute worker crash reconciliation
        reconcile_res = RunManager.reconcile_crashed_runs(stuck_timeout_seconds=60)
        self.assertEqual(reconcile_res["reconciled_runs"], 2)

        # Verify state transition to INTERRUPTED
        updated_run1 = RunManager.get_run("tenant_alpha", run1.run_id)
        self.assertEqual(updated_run1.status, RunStatus.INTERRUPTED)
        self.assertIn("interrupted", (updated_run1.error_message or "").lower())

        updated_run2 = RunManager.get_run("tenant_alpha", run2.run_id)
        self.assertEqual(updated_run2.status, RunStatus.INTERRUPTED)

    def test_03_artifact_restoration_and_checksum_revalidation(self) -> None:
        """
        Validates model artifact backup, restore, and SHA-256 integrity revalidation.
        """
        # Create dummy model file
        model_file = os.path.join(self.temp_dir, "champion_model_v1.bin")
        with open(model_file, "wb") as f:
            f.write(b"ML_MODEL_WEIGHTS_SERIALIZED_DATA_2026")

        # Register artifact
        artifact = ModelRegistry.register_artifact(
            tenant_id="tenant_alpha",
            model_type="DEMAND_FORECAST",
            version="1.0.0",
            artifact_path=model_file,
            metrics={"mape": 3.8, "rmse": 1.1},
        )
        ModelRegistry.promote_to_champion("tenant_alpha", artifact.artifact_id)

        # Backup artifact
        backup_model_file = os.path.join(self.temp_dir, "backup_champion_model_v1.bin")
        shutil.copyfile(model_file, backup_model_file)

        # Simulate primary storage corruption
        with open(model_file, "wb") as f:
            f.write(b"CORRUPTED_FILE_DATA")

        self.assertFalse(ModelRegistry.verify_artifact_integrity("tenant_alpha", artifact.artifact_id))

        # Restore artifact from backup
        shutil.copyfile(backup_model_file, model_file)

        # Revalidate integrity
        self.assertTrue(ModelRegistry.verify_artifact_integrity("tenant_alpha", artifact.artifact_id))
        champion = ModelRegistry.get_champion("tenant_alpha", "DEMAND_FORECAST")
        self.assertIsNotNone(champion)
        assert champion is not None
        self.assertEqual(champion.status, "CHAMPION")


if __name__ == "__main__":
    unittest.main()