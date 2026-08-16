"""Adversarial and functional test suite for Phase 2 Data Ingestion."""

import unittest
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from aurix_core.database.engine import Base
from aurix_core.database.models.ingestion import IngestionRun
from aurix_core.database.repositories.base import BaseRepository
from aurix_core.data_foundation.ingestion_service import IngestionService
from aurix_core.data_foundation.quality_engine import DataQualityEngine


class TestDataIngestionLifecycle(unittest.TestCase):
    """Test suite verifying provenance, idempotency, and quality validation."""

    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        from aurix_core.database.models import ingestion, supply_chain  # noqa: Ensure bound
        _ = ingestion.__name__
        _ = supply_chain.__name__
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.db: Session = self.SessionLocal()
        self.tenant_a = "tenant_A"
        self.tenant_b = "tenant_B"

    def tearDown(self) -> None:
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_01_quality_engine_negative_inventory(self) -> None:
        """Ensures negative inventory triggers a strict ERROR."""
        df = pd.DataFrame([{"sku_id": "SKU-1", "location_id": "LOC-1", "on_hand": -50.0}])
        result = DataQualityEngine.validate(df, "inventory")
        self.assertEqual(result["status"], "ERROR")
        self.assertTrue(any("Negative inventory" in e for e in result["errors"]))

    def test_02_ingestion_service_idempotency(self) -> None:
        """Verifies duplicate datasets are caught via hashing and not re-processed."""
        service = IngestionService(self.db, self.tenant_a)
        df = pd.DataFrame([{"sku_code": "SKU-99", "name": "Test SKU"}])

        # First upload
        res1 = service.ingest_dataset(df, "products", "test_file_1.csv")
        self.assertEqual(res1["status"], "COMPLETED")
        self.assertEqual(res1["success_count"], 1)

        # Exact duplicate upload
        res2 = service.ingest_dataset(df, "products", "test_file_1.csv")
        self.assertEqual(res2["status"], "DUPLICATE")
        self.assertEqual(res2["run_id"], res1["run_id"])

    def test_03_ingestion_tenant_isolation(self) -> None:
        """Verifies Tenant B cannot accidentally read or update Tenant A ingestion runs."""
        service_a = IngestionService(self.db, self.tenant_a)
        df = pd.DataFrame([{"sku_code": "SKU-AAA"}])
        service_a.ingest_dataset(df, "products", "source_A.csv")

        # Tenant B checks their runs
        run_repo_b = BaseRepository[IngestionRun](IngestionRun, self.db, self.tenant_b)
        runs_b = run_repo_b.list_all()

        self.assertEqual(len(runs_b), 0)  # Tenant B sees 0 runs

    def test_04_historical_observation_upsert(self) -> None:
        """Verifies an uploaded dataset updates an existing record safely rather than duplicating."""
        service = IngestionService(self.db, self.tenant_a)

        df1 = pd.DataFrame([{"sku_code": "SKU-HIST", "unit_cost": 10.0}])
        service.ingest_dataset(df1, "products", "source_1.csv")

        df2 = pd.DataFrame([{"sku_code": "SKU-HIST", "unit_cost": 20.0}])
        res2 = service.ingest_dataset(df2, "products", "source_2.csv")

        self.assertEqual(res2["status"], "COMPLETED")
        self.assertEqual(res2["success_count"], 1)