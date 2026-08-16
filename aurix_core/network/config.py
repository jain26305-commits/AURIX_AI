"""Centralized business policy configuration for Phase 7 Network Intelligence."""

from typing import Any, Dict, Optional


class NetworkConfiguration:
    """
    Centralizes policy parameters governing network topology analysis, flow calculations,
    Bullwhip amplification ratios, supplier concentration limits, high-flow thresholds,
    inventory imbalances, and network risk weights.
    """

    DEFAULT_MIN_SAMPLE_SIZE: int = 3

    # Bullwhip Effect Thresholds
    DEFAULT_BULLWHIP_AMPLIFICATION_THRESHOLD: float = 1.05
    DEFAULT_BULLWHIP_HIGH_AMPLIFICATION_THRESHOLD: float = 1.50

    # Capacity Utilization Thresholds
    DEFAULT_CAPACITY_ELEVATED_THRESHOLD: float = 0.75
    DEFAULT_CAPACITY_BOTTLENECK_THRESHOLD: float = 0.95

    # Supplier Concentration Thresholds (HHI or Share)
    DEFAULT_SINGLE_SOURCE_SHARE: float = 1.00
    DEFAULT_HIGH_CONCENTRATION_SHARE: float = 0.80

    # Inventory Coverage Imbalance Thresholds (Days)
    DEFAULT_IMBALANCE_RATIO_THRESHOLD: float = 5.0  # Upstream vs Downstream coverage disparity factor

    # High-Flow / Concentration Thresholds (Units)
    DEFAULT_HIGH_FLOW_THRESHOLD: float = 10000.0

    # Default Risk Component Weights
    DEFAULT_RISK_WEIGHTS: Dict[str, float] = {
        "single_source": 0.35,
        "capacity_bottleneck": 0.25,
        "bullwhip_amplification": 0.20,
        "inventory_imbalance": 0.20,
    }

    def __init__(self, overrides: Optional[Dict[str, Any]] = None) -> None:
        overrides = overrides or {}

        self.min_sample_size: int = int(overrides.get("min_sample_size", self.DEFAULT_MIN_SAMPLE_SIZE))
        self.min_bullwhip_sample_size: int = int(
            overrides.get("min_bullwhip_sample_size", self.min_sample_size)
        )

        self.bullwhip_amplification_threshold: float = float(
            overrides.get("bullwhip_amplification_threshold", self.DEFAULT_BULLWHIP_AMPLIFICATION_THRESHOLD)
        )
        self.bullwhip_high_amplification_threshold: float = float(
            overrides.get("bullwhip_high_amplification_threshold", self.DEFAULT_BULLWHIP_HIGH_AMPLIFICATION_THRESHOLD)
        )

        self.capacity_elevated_threshold: float = float(
            overrides.get("capacity_elevated_threshold", self.DEFAULT_CAPACITY_ELEVATED_THRESHOLD)
        )
        self.capacity_bottleneck_threshold: float = float(
            overrides.get("capacity_bottleneck_threshold", self.DEFAULT_CAPACITY_BOTTLENECK_THRESHOLD)
        )
        self.capacity_utilization_bottleneck_threshold: float = float(
            overrides.get("capacity_utilization_bottleneck_threshold", self.capacity_bottleneck_threshold)
        )

        self.single_source_share: float = float(
            overrides.get("single_source_share", self.DEFAULT_SINGLE_SOURCE_SHARE)
        )
        self.high_concentration_share: float = float(
            overrides.get("high_concentration_share", self.DEFAULT_HIGH_CONCENTRATION_SHARE)
        )
        self.top_supplier_share_threshold: float = float(
            overrides.get("top_supplier_share_threshold", self.single_source_share)
        )

        self.imbalance_ratio_threshold: float = float(
            overrides.get("imbalance_ratio_threshold", self.DEFAULT_IMBALANCE_RATIO_THRESHOLD)
        )
        self.imbalance_coverage_ratio_threshold: float = float(
            overrides.get("imbalance_coverage_ratio_threshold", self.imbalance_ratio_threshold)
        )

        self.high_flow_threshold: float = float(
            overrides.get("high_flow_threshold", self.DEFAULT_HIGH_FLOW_THRESHOLD)
        )
        self.high_flow_percentile_threshold: float = float(
            overrides.get("high_flow_percentile_threshold", 0.90)
        )

        raw_weights = overrides.get("risk_weights", self.DEFAULT_RISK_WEIGHTS)
        self.risk_weights: Dict[str, float] = {str(k): float(v) for k, v in raw_weights.items()}