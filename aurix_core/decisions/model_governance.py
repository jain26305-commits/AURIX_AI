"""
AURIX Deterministic Decision Engine 2.0 — Model Governance & Registry Engine
Phase 27 Core Implementation.
Manages model versions, Champion/Challenger framework, shadow mode evaluations, and fitness checks.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from aurix_core.decisions.contracts import (
    ModelFitnessRating,
    ModelRegistryEntry,
    ShadowEvaluationResult,
)


class ModelGovernanceEngine:
    """Manages machine learning and solver registry lifecycles."""

    _model_registry: Dict[str, ModelRegistryEntry] = {
        "AURIX_SUPPLIER_ALLOC_V2": ModelRegistryEntry(
            model_id="AURIX_SUPPLIER_ALLOC_V2",
            model_name="Supplier Allocation Optimizer",
            version="v2.0",
            model_type="OPTIMIZER",
            is_champion=True,
            status="PRODUCTION",
            accuracy_metrics={"WAPE": 7.84, "FITNESS": 0.95},
        ),
        "AURIX_SUPPLIER_ALLOC_EXP": ModelRegistryEntry(
            model_id="AURIX_SUPPLIER_ALLOC_EXP",
            model_name="Experimental Allocation Model",
            version="v2.1-RC",
            model_type="OPTIMIZER",
            is_champion=False,
            status="SHADOW",
            accuracy_metrics={"WAPE": 6.92, "FITNESS": 0.96},
        ),
    }

    @classmethod
    def evaluate_model_fitness(cls, model_id: str) -> ModelFitnessRating:
        """Evaluate whether a model is fit for authoritative production decision generation."""
        entry = cls._model_registry.get(model_id)
        if not entry:
            return ModelFitnessRating.INSUFFICIENT_DATA

        fitness_score = entry.accuracy_metrics.get("FITNESS", 0.0)
        if fitness_score >= 0.85:
            return ModelFitnessRating.HIGH
        elif fitness_score >= 0.60:
            return ModelFitnessRating.PARTIAL
        else:
            return ModelFitnessRating.LOW

    @classmethod
    def evaluate_shadow_challenger(
        cls,
        tenant_id: str,
        decision_id: str,
        champion_rec: str,
        challenger_rec: str,
        champion_ev: float,
        challenger_ev: float,
    ) -> ShadowEvaluationResult:
        """Execute non-blocking shadow evaluation comparing champion vs challenger outputs."""
        variance = abs(challenger_ev - champion_ev) / max(1.0, champion_ev) * 100.0

        return ShadowEvaluationResult(
            tenant_id=tenant_id,
            decision_id=decision_id,
            champion_model_id="AURIX_SUPPLIER_ALLOC_V2",
            challenger_model_id="AURIX_SUPPLIER_ALLOC_EXP",
            champion_recommendation=champion_rec,
            challenger_recommendation=challenger_rec,
            output_variance_pct=round(variance, 2),
            champion_expected_value_usd=champion_ev,
            challenger_expected_value_usd=challenger_ev,
        )
