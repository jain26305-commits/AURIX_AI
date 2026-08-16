"""Orchestrates persistent data ingestion, hashing, and quality assurance."""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy.orm import Session

from aurix_core.data_foundation.db_mapper import CanonicalMapper
from aurix_core.data_foundation.quality_engine import DataQualityEngine
from aurix_core.database.models.ingestion import IngestionRun
from aurix_core.database.repositories.base import BaseRepository


class IngestionService:
    """
    Manages the lifecycle of operational data entering AURIX.
    Enforces hashing, idempotency, validation, and safe persistence.
    """

    def __init__(self, db: Session, tenant_id: str) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.run_repo = BaseRepository[IngestionRun](IngestionRun, db, tenant_id)
        self.mapper = CanonicalMapper(db, tenant_id)

    def _hash_dataframe(self, df: pd.DataFrame) -> str:
        """Deterministically hashes the dataframe to detect identical uploads across runs."""
        sorted_df = df.reindex(sorted(df.columns), axis=1)
        data_str = sorted_df.to_json(orient="records", date_format="iso")
        return hashlib.sha256(str(data_str).encode("utf-8")).hexdigest()

    def ingest_dataset(self, df: pd.DataFrame, domain: str, source_name: str) -> Dict[str, Any]:
        """
        Executes the full ingestion pipeline:
        Hash -> Idempotency Check -> Validation -> Canonical Map -> Commit.
        """
        if df.empty:
            return {
                "status": "FAILED",
                "run_id": None,
                "errors": ["Cannot ingest an empty dataset."],
            }

        data_hash = self._hash_dataframe(df)

        # 1. Idempotency Check
        existing_run = self.run_repo._base_query().filter_by(
            data_hash=data_hash,
            status="COMPLETED",
        ).first()

        if existing_run:
            return {
                "status": "DUPLICATE",
                "run_id": str(existing_run.id),
                "message": "Identical dataset already successfully ingested and mapped.",
            }

        run_id = str(uuid.uuid4())

        run = IngestionRun(
            id=run_id,
            source_name=source_name,
            domain=domain.lower(),
            data_hash=data_hash,
            status="VALIDATING",
            record_count=len(df),
            tenant_id=self.tenant_id,
        )
        self.run_repo.create(run)

        # 2. Quality Validation Gate
        validation_result = DataQualityEngine.validate(df, domain.lower())
        if validation_result.get("status") == "ERROR":
            setattr(run, "status", "FAILED")
            setattr(run, "validation_summary", json.dumps(validation_result.get("errors", [])))
            setattr(run, "completed_at", datetime.now(timezone.utc))
            self.db.commit()
            return {
                "status": "FAILED",
                "run_id": run_id,
                "errors": validation_result.get("errors", []),
            }

        setattr(run, "status", "PERSISTING")
        self.db.commit()

        # 3. Canonical Persistence Execution
        try:
            domain_key = domain.lower().strip()
            success_count = 0

            if domain_key == "products" and hasattr(self.mapper, "map_products"):
                success_count = self.mapper.map_products(df, run_id)
            elif domain_key == "locations" and hasattr(self.mapper, "map_locations"):
                success_count = self.mapper.map_locations(df, run_id)
            elif domain_key == "suppliers" and hasattr(self.mapper, "map_suppliers"):
                success_count = self.mapper.map_suppliers(df, run_id)
            elif domain_key == "inventory" and hasattr(self.mapper, "map_inventory"):
                success_count = self.mapper.map_inventory(df, run_id)
            elif domain_key == "demand" and hasattr(self.mapper, "map_demand"):
                success_count = self.mapper.map_demand(df, run_id)
            elif domain_key == "shipments" and hasattr(self.mapper, "map_shipments"):
                success_count = self.mapper.map_shipments(df, run_id)
            else:
                handler = getattr(self.mapper, f"map_{domain_key}", None)
                if callable(handler):
                    success_count = handler(df, run_id)
                else:
                    raise ValueError(f"Unsupported canonical ingestion domain: '{domain}'")

            setattr(run, "status", "COMPLETED")
            setattr(run, "completed_at", datetime.now(timezone.utc))
            setattr(run, "error_count", max(0, len(df) - success_count))

            warnings: List[str] = validation_result.get("warnings", [])
            if warnings:
                setattr(run, "validation_summary", json.dumps(warnings))

            self.db.commit()
            return {
                "status": "COMPLETED",
                "run_id": run_id,
                "success_count": success_count,
                "error_count": int(str(getattr(run, "error_count", 0))),
                "warnings": warnings,
            }

        except Exception as e:
            self.db.rollback()
            setattr(run, "status", "FAILED")
            setattr(run, "validation_summary", json.dumps([str(e)]))
            setattr(run, "completed_at", datetime.now(timezone.utc))
            setattr(run, "error_count", len(df))
            self.db.commit()
            return {"status": "FAILED", "run_id": run_id, "errors": [str(e)]}
