"""Centralized business policy configuration for the Phase 7B Decision Engine."""

from typing import Any, Dict, Optional


class DecisionConfiguration:
    """Centralizes thresholds, improvement gates, and solver limits for network optimization."""

    # Minimum improvement gates to prevent recommending negligible operational/financial changes
    DEFAULT_MIN_FINANCIAL_IMPROVEMENT_PCT: float = 0.02  # 2% minimum cost savings to justify action
    DEFAULT_MIN_COVERAGE_IMPROVEMENT_DAYS: float = 3.0  # Must improve stockout exposure by at least 3 days

    # Operational constraints
    DEFAULT_MIN_TRANSFER_QUANTITY: float = 1.0  # Do not recommend fractional or zero-unit transfers
    DEFAULT_MAX_RECOMMENDATIONS_PER_SKU: int = 3  # Primary recommendation + up to 2 alternatives

    def __init__(self, overrides: Optional[Dict[str, Any]] = None) -> None:
        overrides = overrides or {}

        # Financial & Service Improvement Gates
        self.min_financial_improvement_pct: float = float(
            overrides.get("min_financial_improvement_pct", self.DEFAULT_MIN_FINANCIAL_IMPROVEMENT_PCT)
        )
        self.min_coverage_improvement_days: float = float(
            overrides.get("min_coverage_improvement_days", self.DEFAULT_MIN_COVERAGE_IMPROVEMENT_DAYS)
        )

        # Execution Constraints
        self.min_transfer_quantity: float = float(
            overrides.get("min_transfer_quantity", self.DEFAULT_MIN_TRANSFER_QUANTITY)
        )
        self.max_recommendations_per_sku: int = int(
            overrides.get("max_recommendations_per_sku", self.DEFAULT_MAX_RECOMMENDATIONS_PER_SKU)
        )
