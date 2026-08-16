"""Centralized policy configuration for Financial Intelligence & Scenario Simulation (Phase 8)."""

from typing import Any, Dict, Optional, Tuple


class EconomicsConfiguration:
    """Centralizes financial risk thresholds, holding rates, and simulation defaults."""

    DEFAULT_ANNUAL_HOLDING_RATE: float = 0.15
    DEFAULT_CURRENCY: str = "USD"

    # Working Capital & Financial Risk Thresholds
    DEFAULT_FINANCIAL_RISK_LOW_MAX: float = 10000.0
    DEFAULT_FINANCIAL_RISK_MODERATE_MAX: float = 50000.0
    DEFAULT_FINANCIAL_RISK_HIGH_MAX: float = 250000.0

    # Sensitivity Analysis Default Ranges
    DEFAULT_DEMAND_SENSITIVITY_RANGE: Tuple[float, ...] = (-0.20, -0.10, 0.0, 0.10, 0.20)
    DEFAULT_LEAD_TIME_SENSITIVITY_RANGE: Tuple[float, ...] = (-0.20, -0.10, 0.0, 0.10, 0.20)

    # Concentration Limits
    DEFAULT_TOP_CONCENTRATION_COUNT: int = 5

    def __init__(self, overrides: Optional[Dict[str, Any]] = None) -> None:
        overrides = overrides or {}

        # Holding Cost Rate Policy (clamped >= 0.0)
        self.annual_holding_rate: float = max(
            0.0,
            float(overrides.get("annual_holding_rate", self.DEFAULT_ANNUAL_HOLDING_RATE)),
        )

        # Default Currency
        self.default_currency: str = str(
            overrides.get("default_currency", self.DEFAULT_CURRENCY)
        ).upper().strip()

        # Risk Classification Thresholds
        self.financial_risk_low_max: float = float(
            overrides.get("financial_risk_low_max", self.DEFAULT_FINANCIAL_RISK_LOW_MAX)
        )
        self.financial_risk_moderate_max: float = float(
            overrides.get("financial_risk_moderate_max", self.DEFAULT_FINANCIAL_RISK_MODERATE_MAX)
        )
        self.financial_risk_high_max: float = float(
            overrides.get("financial_risk_high_max", self.DEFAULT_FINANCIAL_RISK_HIGH_MAX)
        )

        # Concentration Analysis
        self.top_concentration_count: int = max(
            1, int(overrides.get("top_concentration_count", self.DEFAULT_TOP_CONCENTRATION_COUNT))
        )