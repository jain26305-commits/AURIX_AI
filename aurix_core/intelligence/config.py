"""Centralized policy configuration for Executive & AI Intelligence (Phase 9)."""

from typing import Any, Dict, Optional


class IntelligenceConfiguration:
    """Centralizes signal extraction thresholds, action prioritization weights, and AI grounding limits."""

    # Default Prioritization Dimension Weights
    DEFAULT_SEVERITY_WEIGHT: float = 0.35
    DEFAULT_FINANCIAL_EXPOSURE_WEIGHT: float = 0.35
    DEFAULT_OPERATIONAL_URGENCY_WEIGHT: float = 0.20
    DEFAULT_SERVICE_IMPACT_WEIGHT: float = 0.10

    # Limits and Display Controls
    DEFAULT_MAX_SIGNALS_PER_DOMAIN: int = 10
    DEFAULT_MAX_PRIORITIZED_ACTIONS: int = 5
    DEFAULT_MAX_EVIDENCE_CHAINS: int = 5

    # AI Grounding & Interpretation Controls
    DEFAULT_ENABLE_AI_INTERPRETATION: bool = False
    DEFAULT_AI_STRICT_GROUNDING: bool = True

    def __init__(self, overrides: Optional[Dict[str, Any]] = None) -> None:
        overrides = overrides or {}

        # Prioritization Weights (Clamped >= 0.0)
        self.severity_weight: float = max(
            0.0, float(overrides.get("severity_weight", self.DEFAULT_SEVERITY_WEIGHT))
        )
        self.financial_exposure_weight: float = max(
            0.0, float(overrides.get("financial_exposure_weight", self.DEFAULT_FINANCIAL_EXPOSURE_WEIGHT))
        )
        self.operational_urgency_weight: float = max(
            0.0, float(overrides.get("operational_urgency_weight", self.DEFAULT_OPERATIONAL_URGENCY_WEIGHT))
        )
        self.service_impact_weight: float = max(
            0.0, float(overrides.get("service_impact_weight", self.DEFAULT_SERVICE_IMPACT_WEIGHT))
        )

        # Max Output Limits (Clamped >= 1)
        self.max_signals_per_domain: int = max(
            1, int(overrides.get("max_signals_per_domain", self.DEFAULT_MAX_SIGNALS_PER_DOMAIN))
        )
        self.max_prioritized_actions: int = max(
            1, int(overrides.get("max_prioritized_actions", self.DEFAULT_MAX_PRIORITIZED_ACTIONS))
        )
        self.max_evidence_chains: int = max(
            1, int(overrides.get("max_evidence_chains", self.DEFAULT_MAX_EVIDENCE_CHAINS))
        )

        # AI Grounding Controls
        self.enable_ai_interpretation: bool = bool(
            overrides.get("enable_ai_interpretation", self.DEFAULT_ENABLE_AI_INTERPRETATION)
        )
        self.ai_strict_grounding: bool = bool(
            overrides.get("ai_strict_grounding", self.DEFAULT_AI_STRICT_GROUNDING)
        )