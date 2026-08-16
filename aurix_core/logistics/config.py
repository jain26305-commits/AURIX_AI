"""Centralized business policy configuration for Logistics Risk and Expedite Decision Engine."""

from typing import Any, Dict, Optional


class LogisticsConfiguration:
    """Centralizes risk weights, carrier thresholds, and inventory coverage penalties for logistics evaluation."""

    DEFAULT_BASE_RISK_SCORE: float = 0.10
    DEFAULT_DELAY_PENALTY: float = 0.35
    DEFAULT_UNASSESSED_CARRIER_PENALTY: float = 0.20

    DEFAULT_ON_TIME_WARNING_THRESHOLD: float = 0.90
    DEFAULT_ON_TIME_DELAY_PENALTY: float = 0.25

    DEFAULT_TRANSIT_VARIABILITY_THRESHOLD: float = 2.0
    DEFAULT_TRANSIT_VARIABILITY_PENALTY: float = 0.15

    DEFAULT_STOCKOUT_CRITICAL_THRESHOLD_DAYS: float = 3.0
    DEFAULT_STOCKOUT_WARNING_THRESHOLD_DAYS: float = 7.0
    DEFAULT_STOCKOUT_EXPOSURE_PENALTY: float = 0.30

    DEFAULT_RISK_LOW_MAX: float = 0.25
    DEFAULT_RISK_MODERATE_MAX: float = 0.50
    DEFAULT_RISK_HIGH_MAX: float = 0.75

    DEFAULT_MIN_SAMPLE_SIZE: int = 3

    def __init__(self, overrides: Optional[Dict[str, Any]] = None) -> None:
        overrides = overrides or {}

        self.base_risk_score: float = float(overrides.get("base_risk_score", self.DEFAULT_BASE_RISK_SCORE))
        self.delay_penalty: float = float(overrides.get("delay_penalty", self.DEFAULT_DELAY_PENALTY))
        self.unassessed_carrier_penalty: float = float(
            overrides.get("unassessed_carrier_penalty", self.DEFAULT_UNASSESSED_CARRIER_PENALTY)
        )

        self.on_time_warning_threshold: float = float(
            overrides.get("on_time_warning_threshold", self.DEFAULT_ON_TIME_WARNING_THRESHOLD)
        )
        self.on_time_delay_penalty: float = float(
            overrides.get("on_time_delay_penalty", self.DEFAULT_ON_TIME_DELAY_PENALTY)
        )

        self.transit_variability_threshold: float = float(
            overrides.get("transit_variability_threshold", self.DEFAULT_TRANSIT_VARIABILITY_THRESHOLD)
        )
        self.transit_variability_penalty: float = float(
            overrides.get("transit_variability_penalty", self.DEFAULT_TRANSIT_VARIABILITY_PENALTY)
        )

        self.stockout_critical_threshold_days: float = float(
            overrides.get("stockout_critical_threshold_days", self.DEFAULT_STOCKOUT_CRITICAL_THRESHOLD_DAYS)
        )
        self.stockout_warning_threshold_days: float = float(
            overrides.get("stockout_warning_threshold_days", self.DEFAULT_STOCKOUT_WARNING_THRESHOLD_DAYS)
        )
        self.stockout_exposure_penalty: float = float(
            overrides.get("stockout_exposure_penalty", self.DEFAULT_STOCKOUT_EXPOSURE_PENALTY)
        )

        self.risk_low_max: float = float(overrides.get("risk_low_max", self.DEFAULT_RISK_LOW_MAX))
        self.risk_moderate_max: float = float(overrides.get("risk_moderate_max", self.DEFAULT_RISK_MODERATE_MAX))
        self.risk_high_max: float = float(overrides.get("risk_high_max", self.DEFAULT_RISK_HIGH_MAX))

        self.min_sample_size: int = int(overrides.get("min_sample_size", self.DEFAULT_MIN_SAMPLE_SIZE))