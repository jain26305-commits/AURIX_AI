"""Logistics risk scoring, freight unit economics, and inventory consequence expedite decision engine."""

from typing import Any, Dict, List, Optional
from aurix_core.logistics.config import LogisticsConfiguration
from aurix_core.schema.phase5_contract import ValueState
from aurix_core.schema.phase6_contract import SupplyRiskLevel


class FreightEconomicsCalculator:
    """Calculates freight unit economics (cost per unit, cost per kg) with zero-division safeguards."""

    @staticmethod
    def calculate_freight_economics(
        freight_cost: Optional[float],
        quantity: Optional[float],
        weight_kg: Optional[float],
        currency: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculates freight unit metrics cleanly preserving ValueState.UNAVAILABLE on missing or non-positive inputs.
        """
        unavail_str = ValueState.UNAVAILABLE.value if hasattr(ValueState.UNAVAILABLE, "value") else str(ValueState.UNAVAILABLE)

        if freight_cost is None or freight_cost < 0.0:
            return {
                "freight_cost": None,
                "cost_per_unit": None,
                "cost_per_kg": None,
                "currency": currency,
                "value_state": unavail_str,
                "reason": "MISSING_OR_INVALID_FREIGHT_COST",
            }

        cost_per_unit: Optional[float] = None
        if quantity is not None and quantity > 0.0:
            cost_per_unit = round(freight_cost / float(quantity), 4)

        cost_per_kg: Optional[float] = None
        if weight_kg is not None and weight_kg > 0.0:
            cost_per_kg = round(freight_cost / float(weight_kg), 4)

        derived_str = ValueState.DERIVED.value if hasattr(ValueState.DERIVED, "value") else str(ValueState.DERIVED)

        return {
            "freight_cost": float(freight_cost),
            "cost_per_unit": cost_per_unit,
            "cost_per_kg": cost_per_kg,
            "currency": currency,
            "value_state": derived_str,
        }


class InventoryConsequenceEngine:
    """
    Evaluates operational consequence of logistics delays against Phase 4 inventory coverage.
    Determines expedite recommendations (NORMAL_TRANSPORT, MONITOR, EXPEDITE_RECOMMENDED, EXPEDITE_CRITICAL).
    """

    @classmethod
    def evaluate_expedite_decision(
        cls,
        delay_days: float,
        inventory_coverage_days: Optional[float],
        config: Optional[LogisticsConfiguration] = None,
    ) -> Dict[str, Any]:
        """
        Calculates expedite recommendation and reason based on delay vs inventory coverage days.
        """
        cfg = config or LogisticsConfiguration()

        if delay_days <= 0.0:
            return {
                "expedite_recommendation": "NORMAL_TRANSPORT",
                "recommendation_reason": "ON_TIME_DELIVERY_EXPECTED",
                "risk_status": "LOW_RISK",
            }

        if inventory_coverage_days is None:
            return {
                "expedite_recommendation": "MONITOR",
                "recommendation_reason": "DELAY_DETECTED_BUT_INVENTORY_COVERAGE_UNAVAILABLE",
                "risk_status": "MODERATE_RISK",
            }

        cov_days = float(inventory_coverage_days)
        buffer_days = cov_days - delay_days

        if buffer_days < 0.0:
            # Estimated delay exceeds remaining inventory coverage -> Critical Stockout Exposure
            return {
                "expedite_recommendation": "EXPEDITE_CRITICAL",
                "recommendation_reason": (
                    f"ESTIMATED_DELAY_{delay_days:.1f}D_EXCEEDS_INVENTORY_COVERAGE_{cov_days:.1f}D"
                ),
                "risk_status": "CRITICAL_RISK",
            }

        if buffer_days <= cfg.stockout_critical_threshold_days:
            return {
                "expedite_recommendation": "EXPEDITE_RECOMMENDED",
                "recommendation_reason": (
                    f"INVENTORY_BUFFER_{buffer_days:.1f}D_BELOW_CRITICAL_THRESHOLD_"
                    f"{cfg.stockout_critical_threshold_days}D"
                ),
                "risk_status": "HIGH_RISK",
            }

        if buffer_days <= cfg.stockout_warning_threshold_days:
            return {
                "expedite_recommendation": "MONITOR",
                "recommendation_reason": (
                    f"INVENTORY_BUFFER_{buffer_days:.1f}D_WITHIN_WARNING_WINDOW_"
                    f"{cfg.stockout_warning_threshold_days}D"
                ),
                "risk_status": "MODERATE_RISK",
            }

        return {
            "expedite_recommendation": "NORMAL_TRANSPORT",
            "recommendation_reason": (
                f"INVENTORY_COVERAGE_{cov_days:.1f}D_SUFFICIENT_FOR_DELAY_{delay_days:.1f}D"
            ),
            "risk_status": "LOW_RISK",
        }


class LogisticsRiskEvaluator:
    """
    Deterministic logistics risk scoring engine.
    Produces bounded (0.0 - 1.0) risk score, categorical SupplyRiskLevel, and risk drivers.
    """

    @classmethod
    def evaluate_risk(
        cls,
        delay_days: float = 0.0,
        carrier_otd_rate: Optional[float] = None,
        transit_std_days: Optional[float] = None,
        inventory_coverage_days: Optional[float] = None,
        config: Optional[LogisticsConfiguration] = None,
    ) -> Dict[str, Any]:
        """
        Calculates bounded logistics risk score and risk level.
        """
        cfg = config or LogisticsConfiguration()
        score = cfg.base_risk_score
        risk_drivers: List[str] = []

        # 1. Delay Penalty
        if delay_days > 0.0:
            score += cfg.delay_penalty
            risk_drivers.append(f"SHIPMENT_DELAY_{delay_days:.1f}_DAYS")

        # 2. Carrier Performance Penalty
        if carrier_otd_rate is None:
            score += cfg.unassessed_carrier_penalty
            risk_drivers.append("UNASSESSED_CARRIER_HISTORY")
        elif carrier_otd_rate < cfg.on_time_warning_threshold:
            score += cfg.on_time_delay_penalty
            risk_drivers.append(f"POOR_CARRIER_OTD_{carrier_otd_rate:.2f}")

        # 3. Transit Volatility Penalty
        if transit_std_days is not None and transit_std_days >= cfg.transit_variability_threshold:
            score += cfg.transit_variability_penalty
            risk_drivers.append(f"HIGH_TRANSIT_VOLATILITY_STD_{transit_std_days:.1f}_DAYS")

        # 4. Inventory Exposure Penalty
        if delay_days > 0.0 and inventory_coverage_days is not None:
            if inventory_coverage_days <= delay_days:
                score += cfg.stockout_exposure_penalty
                risk_drivers.append("STOCKOUT_IMMINENT_COVERAGE_EXHAUSTED")

        # Bound Risk Score strictly between 0.0 and 1.0
        final_score = max(0.0, min(1.0, round(score, 4)))

        # Categorical Risk Level
        if final_score <= cfg.risk_low_max:
            risk_level = SupplyRiskLevel.LOW
        elif final_score <= cfg.risk_moderate_max:
            risk_level = SupplyRiskLevel.MODERATE
        elif final_score <= cfg.risk_high_max:
            risk_level = SupplyRiskLevel.HIGH
        else:
            risk_level = SupplyRiskLevel.CRITICAL

        return {
            "risk_score": final_score,
            "risk_level": risk_level,
            "risk_drivers": risk_drivers,
        }