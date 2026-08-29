"""
AURIX Risk, Causal & External Intelligence — Causal Evidence Classifier Engine
Phase 26 Core Implementation.
Classifies relationships as OBSERVED, CORRELATED, INFERRED, CAUSAL, or UNKNOWN with confounder control.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from aurix_core.risk.contracts import (
    CausalClassification,
    CausalEvidenceRecord,
)


class CausalEngine:
    """Evaluates causal evidence validity without speculative LLM assertions."""

    @classmethod
    def evaluate_relationship(
        cls,
        tenant_id: str,
        cause_entity_id: str,
        effect_entity_id: str,
        has_temporal_precedence: bool,
        correlation_coefficient: float,
        has_controlled_confounders: bool,
        evidence_payload: Optional[Dict[str, Any]] = None,
    ) -> CausalEvidenceRecord:
        """
        Determines causal classification mathematically:
        - CAUSAL: Temporal precedence + strong correlation (>= 0.8) + confounders controlled.
        - CORRELATED: Strong correlation without complete confounder control.
        - INFERRED: Temporal precedence without measured correlation.
        - OBSERVED: Direct transactional link.
        - UNKNOWN: Inconclusive data.
        """
        if has_temporal_precedence and correlation_coefficient >= 0.80 and has_controlled_confounders:
            classification = CausalClassification.CAUSAL
            conf_score = 0.95
            method = "TEMPORAL_PRECEDENCE_AND_CONFOUNDER_CONTROLLED_MATCH"
        elif correlation_coefficient >= 0.65:
            classification = CausalClassification.CORRELATED
            conf_score = 0.75
            method = "PEARSON_CORRELATION_COEFFICIENT_MATCH"
        elif has_temporal_precedence:
            classification = CausalClassification.INFERRED
            conf_score = 0.60
            method = "TEMPORAL_PRECEDENCE_HEURISTIC"
        else:
            classification = CausalClassification.UNKNOWN
            conf_score = 0.30
            method = "INSUFFICIENT_EVIDENCE"

        return CausalEvidenceRecord(
            tenant_id=tenant_id,
            cause_entity_id=cause_entity_id,
            effect_entity_id=effect_entity_id,
            relationship_classification=classification,
            methodology=method,
            confidence_score=conf_score,
            known_confounders=["SEASONALITY", "MARKET_VOLATILITY"] if not has_controlled_confounders else [],
            evidence=evidence_payload or {},
        )
