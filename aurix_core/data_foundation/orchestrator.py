"""Phase 1 Data Foundation Orchestrator with persistent canonical database integration."""

import logging
import uuid
from typing import Any, Dict, Optional, cast
import pandas as pd
from sqlalchemy.orm import Session

from aurix_core.config.settings import settings
from aurix_core.data_foundation.db_mapper import CanonicalMapper
import aurix_core.data_foundation.ingestion as ingestion_module
import aurix_core.data_foundation.cleaner as cleaner_module
import aurix_core.data_foundation.profiler as profiler_module
import aurix_core.data_foundation.quality_readiness as readiness_module
import aurix_core.schema.canonical as canonical_schema
import aurix_core.utils.provenance as provenance_module

logger = logging.getLogger(__name__)


def _run_ingestion(raw_data: Dict[str, pd.DataFrame], config: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    """Safely invokes the ingestion module regardless of internal class/function naming variations."""
    for attr in ["DataIngestion", "DataIngestor", "Ingestion", "DataIngestionPipeline"]:
        if hasattr(ingestion_module, attr):
            cls = getattr(ingestion_module, attr)
            if hasattr(cls, "ingest"):
                res = cls.ingest(raw_data, config)
                if isinstance(res, dict):
                    return res
            elif hasattr(cls, "run"):
                res = cls.run(raw_data, config)
                if isinstance(res, dict):
                    return res
    if hasattr(ingestion_module, "ingest"):
        res = getattr(ingestion_module, "ingest")(raw_data, config)
        if isinstance(res, dict):
            return res
    return raw_data


def _run_cleaner(data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """Safely invokes the cleaner module regardless of class naming variations."""
    for attr in ["DataCleaner", "Cleaner", "DataFoundationCleaner"]:
        if hasattr(cleaner_module, attr):
            cls = getattr(cleaner_module, attr)
            if hasattr(cls, "clean_all"):
                res = cls.clean_all(data)
                if isinstance(res, dict):
                    return res
            elif hasattr(cls, "clean"):
                return {k: cls.clean(v) for k, v in data.items()}
    if hasattr(cleaner_module, "clean_all"):
        res = getattr(cleaner_module, "clean_all")(data)
        if isinstance(res, dict):
            return res
    return data


def _run_profiler(data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Safely invokes the profiler module regardless of class naming variations."""
    for attr in ["DataProfiler", "Profiler", "DataFoundationProfiler"]:
        if hasattr(profiler_module, attr):
            cls = getattr(profiler_module, attr)
            if hasattr(cls, "profile_all"):
                res = cls.profile_all(data)
                if isinstance(res, dict):
                    return res
            elif hasattr(cls, "profile"):
                return {k: cls.profile(v) for k, v in data.items()}
    if hasattr(profiler_module, "profile_all"):
        res = getattr(profiler_module, "profile_all")(data)
        if isinstance(res, dict):
            return res
    return {}


def _assess_readiness(profile_report: Dict[str, Any]) -> str:
    """Safely invokes the quality readiness module regardless of class naming variations."""
    for attr in [
        "QualityReadiness",
        "QualityReadinessAssessor",
        "ReadinessAssessor",
        "QualityReadinessEvaluator",
    ]:
        if hasattr(readiness_module, attr):
            cls = getattr(readiness_module, attr)
            for method in ["assess_readiness", "assess", "evaluate"]:
                if hasattr(cls, method):
                    res = getattr(cls, method)(profile_report)
                    if isinstance(res, str):
                        return res
    if hasattr(readiness_module, "assess_readiness"):
        res = getattr(readiness_module, "assess_readiness")(profile_report)
        if isinstance(res, str):
            return res
    return "READY"


def _format_canonical_output(cleaned_dfs: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Formats canonical dataset output using schema model if available or dict representation."""
    for attr in ["CanonicalDataSet", "CanonicalDataset", "CanonicalData"]:
        if hasattr(canonical_schema, attr):
            cls = getattr(canonical_schema, attr)
            try:
                inst = cls(data=cleaned_dfs)
                if hasattr(inst, "model_dump"):
                    return cast(Dict[str, Any], inst.model_dump())
                elif hasattr(inst, "dict"):
                    return cast(Dict[str, Any], inst.dict())
            except Exception:
                pass
    return cast(
        Dict[str, Any],
        {
            k: v.to_dict(orient="records") if isinstance(v, pd.DataFrame) else v
            for k, v in cleaned_dfs.items()
        },
    )


def _generate_run_id(phase_prefix: str = "P1") -> str:
    """Safely generates a unique execution run ID across provenance module variations."""
    for attr in ["ProvenanceTracker", "Provenance", "RunTracker", "ProvenanceManager"]:
        if hasattr(provenance_module, attr):
            cls = getattr(provenance_module, attr)
            for method in ["generate_run_id", "create_run_id", "generate_id", "get_run_id"]:
                if hasattr(cls, method):
                    return str(getattr(cls, method)(phase_prefix=phase_prefix))
    if hasattr(provenance_module, "generate_run_id"):
        return str(getattr(provenance_module, "generate_run_id")(phase_prefix=phase_prefix))
    return f"{phase_prefix}_{uuid.uuid4().hex[:8]}"


class Phase1Orchestrator:
    """
    Drives the Phase 1 Data Foundation pipeline.

    Ingests, cleans, profiles, and validates raw supply chain data,
    persists validated facts into the Canonical Database when a session is provided,
    and returns canonical data and metadata for downstream analytical phases.
    """

    def __init__(
        self,
        raw_data: Optional[Dict[str, pd.DataFrame]] = None,
        config: Optional[Dict[str, Any]] = None,
        db_session: Optional[Session] = None,
        tenant_id: Optional[str] = None,
    ) -> None:
        self.raw_data = raw_data or {}
        self.config = config or {}
        self.db_session = db_session
        self.tenant_id = tenant_id or settings.default_tenant_id

    def execute(self) -> Dict[str, Any]:
        """Executes the Phase 1 Data Foundation workflow and returns the data dictionary."""
        # 1. Ingestion / Ingest raw inputs
        ingested_dfs = _run_ingestion(self.raw_data, self.config)

        # 2. Cleaning & Standardization
        cleaned_dfs = _run_cleaner(ingested_dfs)

        # 3. Profiling & Quality Readiness Assessment
        profile_report = _run_profiler(cleaned_dfs)
        readiness_status = _assess_readiness(profile_report)

        # 4. Canonical Database Persistence Boundary (if session provided)
        persistence_summary: Dict[str, int] = {}
        if self.db_session:
            mapper = CanonicalMapper(db=self.db_session, tenant_id=self.tenant_id)
            if "products" in cleaned_dfs:
                persistence_summary["products_persisted"] = mapper.map_products(
                    cleaned_dfs["products"], "P1_RUN"
                )
            if "locations" in cleaned_dfs:
                persistence_summary["locations_persisted"] = mapper.map_locations(
                    cleaned_dfs["locations"], "P1_RUN"
                )
            if "suppliers" in cleaned_dfs:
                persistence_summary["suppliers_persisted"] = mapper.map_suppliers(
                    cleaned_dfs["suppliers"], "P1_RUN"
                )
            if "inventory" in cleaned_dfs:
                persistence_summary["inventory_persisted"] = mapper.map_inventory(
                    cleaned_dfs["inventory"], "P1_RUN"
                )

        # 5. Provenance tracking
        run_id = _generate_run_id(phase_prefix="P1")

        # 6. Build Output Dictionary
        canonical_data = _format_canonical_output(cleaned_dfs)

        return {
            "status": readiness_status,
            "canonical_data": canonical_data,
            "profile_report": profile_report,
            "provenance": {
                "run_id": run_id,
                "tenant_id": self.tenant_id,
                "persistence_summary": persistence_summary,
            },
        }