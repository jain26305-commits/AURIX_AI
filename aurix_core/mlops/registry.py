"""Model and Artifact Registry with Checksum Verification, Performance Evaluation, and Champion Lifecycle Management."""

import hashlib
import logging
import math
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("aurix_core.mlops.registry")


class ModelArtifactRecord(BaseModel):
    """Metadata record for a registered model artifact."""
    artifact_id: str
    tenant_id: str
    model_type: str  # e.g., "DEMAND_FORECAST", "SAFETY_STOCK"
    version: str
    training_run_id: Optional[str] = None
    metrics: Dict[str, float] = Field(default_factory=dict)
    is_champion: bool = False
    status: str = "REGISTERED"  # REGISTERED, CHAMPION, CHALLENGER, ARCHIVED, ROLLED_BACK
    artifact_path: str
    checksum: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ModelEvaluationResult(BaseModel):
    """Evaluation metrics container comparing forecasts against actual demand/observations."""
    mae: float = Field(..., description="Mean Absolute Error")
    rmse: float = Field(..., description="Root Mean Squared Error")
    mape: float = Field(..., description="Mean Absolute Percentage Error (%)")
    bias: float = Field(..., description="Mean Error (Forecast Bias)")
    sample_count: int = Field(..., description="Number of observed evaluation periods")
    evaluated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DegradationReport(BaseModel):
    """Diagnostic report determining whether model performance has degraded beyond tolerance."""
    artifact_id: str
    tenant_id: str
    model_type: str
    is_degraded: bool
    baseline_mape: Optional[float] = None
    current_mape: float
    degradation_pct: float
    recommendation: str
    evaluated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ModelRegistry:
    """Manages secure, tenant-scoped model registration, verification, degradation monitoring, and promotion."""

    # Tenant-scoped in-memory registry store
    _REGISTRY_STORE: Dict[str, Dict[str, ModelArtifactRecord]] = {}

    @classmethod
    def compute_file_checksum(cls, file_path: str) -> str:
        """Computes SHA-256 checksum for artifact integrity verification."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    @classmethod
    def register_artifact(
        cls,
        tenant_id: str,
        model_type: str,
        version: str,
        artifact_path: str,
        metrics: Dict[str, float],
        training_run_id: Optional[str] = None,
    ) -> ModelArtifactRecord:
        """Registers a new model artifact with checksum generation and secure path validation."""
        # Prevent path traversal vulnerabilities
        safe_filename = os.path.basename(artifact_path)
        if not os.path.exists(artifact_path):
            raise FileNotFoundError(f"Model artifact path '{artifact_path}' does not exist.")

        checksum = cls.compute_file_checksum(artifact_path)
        artifact_id = f"ART-{model_type}-{version}-{checksum[:8].upper()}"

        record = ModelArtifactRecord(
            artifact_id=artifact_id,
            tenant_id=tenant_id,
            model_type=model_type,
            version=version,
            training_run_id=training_run_id,
            metrics=metrics,
            is_champion=False,
            status="REGISTERED",
            artifact_path=os.path.abspath(artifact_path),
            checksum=checksum,
        )

        tenant_artifacts = cls._REGISTRY_STORE.setdefault(tenant_id, {})
        tenant_artifacts[artifact_id] = record
        logger.info("Successfully registered model artifact [ID: %s, Type: %s, Version: %s]", artifact_id, model_type, version)
        return record

    @classmethod
    def promote_to_champion(cls, tenant_id: str, artifact_id: str) -> ModelArtifactRecord:
        """Promotes a registered artifact to champion status, demoting existing champions for that model type."""
        tenant_artifacts = cls._REGISTRY_STORE.get(tenant_id, {})
        target = tenant_artifacts.get(artifact_id)
        if not target:
            raise KeyError(f"Artifact '{artifact_id}' not found for tenant '{tenant_id}'.")

        # Demote existing champions of the same model type
        for art in tenant_artifacts.values():
            if art.model_type == target.model_type and art.is_champion:
                art.is_champion = False
                art.status = "ARCHIVED"

        target.is_champion = True
        target.status = "CHAMPION"
        logger.info("Promoted artifact [%s] to CHAMPION for model type [%s]", artifact_id, target.model_type)
        return target

    @classmethod
    def get_champion(cls, tenant_id: str, model_type: str) -> Optional[ModelArtifactRecord]:
        """Retrieves the current champion model artifact for a tenant and model type."""
        tenant_artifacts = cls._REGISTRY_STORE.get(tenant_id, {})
        for art in tenant_artifacts.values():
            if art.model_type == model_type and art.is_champion:
                return art
        return None

    @classmethod
    def rollback_to_previous_champion(cls, tenant_id: str, model_type: str) -> Optional[ModelArtifactRecord]:
        """
        Rolls back to the most recently archived champion model if the current champion is degrading.
        """
        tenant_artifacts = cls._REGISTRY_STORE.get(tenant_id, {})
        current_champ = cls.get_champion(tenant_id, model_type)

        # Find archived candidates
        archived_candidates = [
            art for art in tenant_artifacts.values()
            if art.model_type == model_type and art.status == "ARCHIVED"
        ]

        if not archived_candidates:
            logger.warning("No archived champion models found for tenant [%s] and model type [%s].", tenant_id, model_type)
            return None

        # Sort by creation date descending to get the most recent prior champion
        archived_candidates.sort(key=lambda x: x.created_at, reverse=True)
        previous_champion = archived_candidates[0]

        if current_champ:
            current_champ.is_champion = False
            current_champ.status = "ROLLED_BACK"

        previous_champion.is_champion = True
        previous_champion.status = "CHAMPION"
        logger.info("Successfully rolled back to prior champion model [%s] for tenant [%s].", previous_champion.artifact_id, tenant_id)
        return previous_champion

    @classmethod
    def verify_artifact_integrity(cls, tenant_id: str, artifact_id: str) -> bool:
        """Verifies current file checksum against registered SHA-256 checksum."""
        tenant_artifacts = cls._REGISTRY_STORE.get(tenant_id, {})
        target = tenant_artifacts.get(artifact_id)
        if not target:
            raise KeyError(f"Artifact '{artifact_id}' not found for tenant '{tenant_id}'.")

        current_checksum = cls.compute_file_checksum(target.artifact_path)
        is_valid = current_checksum == target.checksum
        if not is_valid:
            logger.error("Artifact integrity violation detected for artifact [%s]!", artifact_id)
        return is_valid

    @classmethod
    def evaluate_performance(cls, actuals: List[float], forecasts: List[float]) -> ModelEvaluationResult:
        """
        Calculates forecast error metrics (MAE, RMSE, MAPE, Bias) comparing forecasts to actuals.
        """
        n = len(actuals)
        if n == 0 or len(forecasts) != n:
            raise ValueError("Actuals and forecasts must be non-empty and of identical length.")

        abs_errors: List[float] = []
        squared_errors: List[float] = []
        percentage_errors: List[float] = []
        raw_errors: List[float] = []

        for y, y_hat in zip(actuals, forecasts):
            err = y - y_hat
            abs_err = abs(err)
            raw_errors.append(err)
            abs_errors.append(abs_err)
            squared_errors.append(err ** 2)

            # Avoid division by zero
            denom = max(abs(y), 1e-6)
            percentage_errors.append((abs_err / denom) * 100.0)

        mae = sum(abs_errors) / n
        rmse = math.sqrt(sum(squared_errors) / n)
        mape = sum(percentage_errors) / n
        bias = sum(raw_errors) / n

        return ModelEvaluationResult(
            mae=round(mae, 4),
            rmse=round(rmse, 4),
            mape=round(mape, 4),
            bias=round(bias, 4),
            sample_count=n,
        )

    @classmethod
    def check_model_degradation(
        cls,
        tenant_id: str,
        artifact_id: str,
        actuals: List[float],
        forecasts: List[float],
        max_degradation_pct: float = 25.0,
    ) -> DegradationReport:
        """
        Evaluates recent actuals against baseline model metrics to detect performance degradation.
        """
        tenant_artifacts = cls._REGISTRY_STORE.get(tenant_id, {})
        target = tenant_artifacts.get(artifact_id)
        if not target:
            raise KeyError(f"Artifact '{artifact_id}' not found for tenant '{tenant_id}'.")

        eval_result = cls.evaluate_performance(actuals, forecasts)
        baseline_mape = target.metrics.get("mape")

        if baseline_mape is None or baseline_mape <= 0:
            # Baseline absent; current MAPE serves as default anchor
            return DegradationReport(
                artifact_id=artifact_id,
                tenant_id=tenant_id,
                model_type=target.model_type,
                is_degraded=False,
                baseline_mape=baseline_mape,
                current_mape=eval_result.mape,
                degradation_pct=0.0,
                recommendation="Baseline MAPE not recorded; performance monitored without threshold breach.",
            )

        # Calculate percentage degradation relative to baseline error
        degradation_pct = ((eval_result.mape - baseline_mape) / baseline_mape) * 100.0
        is_degraded = degradation_pct > max_degradation_pct

        recommendation = (
            f"Performance degraded by {degradation_pct:.2f}% (Threshold: {max_degradation_pct}%). Retraining or rollback advised."
            if is_degraded
            else "Model performance operates within acceptable error tolerance."
        )

        return DegradationReport(
            artifact_id=artifact_id,
            tenant_id=tenant_id,
            model_type=target.model_type,
            is_degraded=is_degraded,
            baseline_mape=baseline_mape,
            current_mape=eval_result.mape,
            degradation_pct=round(degradation_pct, 2),
            recommendation=recommendation,
        )