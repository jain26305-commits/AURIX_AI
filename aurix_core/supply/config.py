"""Centralized business policy configuration for Supply Intelligence and Procurement Sourcing."""

from typing import Any, Dict, Optional


class SupplyConfiguration:
    """
    Centralizes business policy thresholds, warning criteria,
    and risk penalty weights for supply chain evaluation and supplier selection.
    """

    DEFAULT_BASE_RISK_SCORE: float = 0.10
    DEFAULT_OTIF_THRESHOLD: float = 0.80
    DEFAULT_FILL_RATE_THRESHOLD: float = 0.85
    DEFAULT_LEAD_TIME_VAR_THRESHOLD: float = 0.40
    DEFAULT_DEFECT_RATE_THRESHOLD: float = 0.02

    DEFAULT_OTIF_PENALTY: float = 0.25
    DEFAULT_FILL_RATE_PENALTY: float = 0.20
    DEFAULT_VARIABILITY_PENALTY: float = 0.20
    DEFAULT_DEFECT_PENALTY: float = 0.25
    DEFAULT_UNASSESSED_PENALTY: float = 0.15
    DEFAULT_CAPACITY_CONSTRAINED_PENALTY: float = 0.30

    DEFAULT_RISK_LOW_MAX: float = 0.25
    DEFAULT_RISK_MODERATE_MAX: float = 0.50
    DEFAULT_RISK_HIGH_MAX: float = 0.75

    def __init__(self, overrides: Optional[Dict[str, Any]] = None) -> None:
        overrides = overrides or {}

        self.base_risk_score: float = float(overrides.get("base_risk_score", self.DEFAULT_BASE_RISK_SCORE))

        # OTIF
        otif_val = float(
            overrides.get(
                "otif_warning_threshold",
                overrides.get("otif_threshold", self.DEFAULT_OTIF_THRESHOLD),
            )
        )
        self.otif_threshold = otif_val
        self.otif_warning_threshold = otif_val

        # Fill Rate
        fill_val = float(
            overrides.get(
                "fill_rate_warning_threshold",
                overrides.get("fill_rate_threshold", self.DEFAULT_FILL_RATE_THRESHOLD),
            )
        )
        self.fill_rate_threshold = fill_val
        self.fill_rate_warning_threshold = fill_val

        # Lead Time Variability
        lt_var_val = float(
            overrides.get(
                "lead_time_variability_threshold",
                overrides.get(
                    "lead_time_var_threshold",
                    self.DEFAULT_LEAD_TIME_VAR_THRESHOLD,
                ),
            )
        )
        self.lead_time_var_threshold = lt_var_val
        self.lead_time_variability_threshold = lt_var_val

        # Defect Rate
        defect_val = float(
            overrides.get(
                "defect_rate_warning_threshold",
                overrides.get("defect_rate_threshold", self.DEFAULT_DEFECT_RATE_THRESHOLD),
            )
        )
        self.defect_rate_threshold = defect_val
        self.defect_rate_warning_threshold = defect_val

        # Penalties
        self.otif_penalty: float = float(overrides.get("otif_penalty", self.DEFAULT_OTIF_PENALTY))
        self.fill_rate_penalty: float = float(overrides.get("fill_rate_penalty", self.DEFAULT_FILL_RATE_PENALTY))
        var_pen = float(
            overrides.get(
                "variability_penalty",
                overrides.get("lead_time_var_penalty", self.DEFAULT_VARIABILITY_PENALTY),
            )
        )
        self.variability_penalty = var_pen
        self.lead_time_var_penalty = var_pen

        def_pen = float(
            overrides.get(
                "defect_penalty",
                overrides.get("defect_rate_penalty", self.DEFAULT_DEFECT_PENALTY),
            )
        )
        self.defect_penalty = def_pen
        self.defect_rate_penalty = def_pen

        unassessed_pen = float(
            overrides.get(
                "unassessed_supplier_penalty",
                overrides.get(
                    "unassessed_history_penalty",
                    self.DEFAULT_UNASSESSED_PENALTY,
                ),
            )
        )
        self.unassessed_supplier_penalty = unassessed_pen
        self.unassessed_history_penalty = unassessed_pen

        self.capacity_constrained_penalty: float = float(
            overrides.get(
                "capacity_constrained_penalty",
                self.DEFAULT_CAPACITY_CONSTRAINED_PENALTY,
            )
        )

        # Risk Score Boundaries
        self.risk_low_max: float = float(overrides.get("risk_low_max", self.DEFAULT_RISK_LOW_MAX))
        self.risk_moderate_max: float = float(overrides.get("risk_moderate_max", self.DEFAULT_RISK_MODERATE_MAX))
        self.risk_high_max: float = float(overrides.get("risk_high_max", self.DEFAULT_RISK_HIGH_MAX))
