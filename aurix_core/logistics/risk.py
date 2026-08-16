"""Logistics risk evaluation and expedite decision engine with config-driven thresholds and zero fabrication."""

from typing import Optional, Tuple
from aurix_core.logistics.config import LogisticsConfiguration
from aurix_core.schema.phase5_contract import ValueState
from aurix_core.schema.phase7_contract import (
    CarrierPerformanceMetrics,
    ETADetails,
    ExpediteDecision,
    ExpediteRecommendation,
    LogisticsRiskLevel,
    LogisticsRiskSummary,
    ShipmentStatus,
)


class LogisticsRiskEvaluator:
    """Evaluates logistics risk scores, delay probabilities, and expedite actions based on empirical evidence."""

    @classmethod
    def evaluate_risk_and_expedite(
        cls,
        shipment_status: ShipmentStatus,
        eta_details: ETADetails,
        performance_metrics: Optional[CarrierPerformanceMetrics],
        inventory_coverage_days: float,
        replenishment_urgency: str,
        config: Optional[LogisticsConfiguration] = None,
    ) -> Tuple[LogisticsRiskSummary, ExpediteDecision]:
        cfg = config or LogisticsConfiguration()

        risk_score = cfg.base_risk_score
        risk_drivers = []
        delay_probability = 0.10

        # 1. Shipment Status Penalty
        if shipment_status == ShipmentStatus.DELAYED:
            risk_score += cfg.delay_penalty
            risk_drivers.append("SHIPMENT_DELAYED")
            delay_probability = max(delay_probability, 0.85)
        elif shipment_status == ShipmentStatus.EXCEPTION:
            risk_score += cfg.delay_penalty * 1.2
            risk_drivers.append("SHIPMENT_EXCEPTION")
            delay_probability = max(delay_probability, 0.95)
        elif shipment_status in (ShipmentStatus.NOT_DISPATCHED, ShipmentStatus.UNKNOWN):
            risk_score += cfg.unassessed_carrier_penalty
            risk_drivers.append("SHIPMENT_NOT_DISPATCHED")

        # 2. ETA Evidence Quality Evaluation
        if eta_details.eta_method == "INSUFFICIENT_TRANSIT_EVIDENCE":
            risk_score += cfg.unassessed_carrier_penalty
            risk_drivers.append("INSUFFICIENT_TRANSIT_EVIDENCE")

        # 3. Carrier Performance Penalties
        if performance_metrics and performance_metrics.sample_size > 0:
            otd_obj = performance_metrics.on_time_delivery_rate
            if otd_obj and otd_obj.value is not None:
                otd_val = float(otd_obj.value)
                if otd_val < cfg.on_time_warning_threshold:
                    risk_score += cfg.on_time_delay_penalty
                    risk_drivers.append(f"POOR_CARRIER_OTD({otd_val * 100:.1f}%)")
                    delay_probability = max(delay_probability, 1.0 - otd_val)

            std_obj = performance_metrics.transit_std_days
            if std_obj and std_obj.value is not None:
                std_val = float(std_obj.value)
                if std_val > cfg.transit_variability_threshold:
                    risk_score += cfg.transit_variability_penalty
                    risk_drivers.append(f"HIGH_TRANSIT_VOLATILITY({std_val:.1f}d)")
        else:
            risk_score += cfg.unassessed_carrier_penalty
            risk_drivers.append("UNASSESSED_CARRIER_HISTORY")

        # 4. Inventory Coverage Exhaustion Penalty
        if inventory_coverage_days <= cfg.stockout_critical_threshold_days:
            risk_score += cfg.stockout_exposure_penalty
            risk_drivers.append(f"CRITICAL_INVENTORY_COVERAGE({inventory_coverage_days:.1f}d)")
        elif inventory_coverage_days <= cfg.stockout_warning_threshold_days:
            risk_score += cfg.stockout_exposure_penalty * 0.5
            risk_drivers.append(f"LOW_INVENTORY_COVERAGE({inventory_coverage_days:.1f}d)")

        # Clamp Risk Score strictly between 0.0 and 1.0
        risk_score = max(0.0, min(1.0, round(risk_score, 2)))
        delay_probability = max(0.0, min(1.0, round(delay_probability, 2)))

        # 5. Deterministic Risk Level Mapping
        if (
            shipment_status in (ShipmentStatus.NOT_DISPATCHED, ShipmentStatus.UNKNOWN)
            and eta_details.value_state == ValueState.UNAVAILABLE
        ):
            risk_level = LogisticsRiskLevel.NOT_ASSESSABLE
        elif risk_score < cfg.risk_low_max:
            risk_level = LogisticsRiskLevel.LOW
        elif risk_score < cfg.risk_moderate_max:
            risk_level = LogisticsRiskLevel.MODERATE
        elif risk_score < cfg.risk_high_max:
            risk_level = LogisticsRiskLevel.HIGH
        else:
            risk_level = LogisticsRiskLevel.CRITICAL

        if not risk_drivers:
            risk_drivers.append("STABLE_LOGISTICS_FLOW")

        risk_summary = LogisticsRiskSummary(
            risk_level=risk_level,
            risk_score=risk_score,
            delay_probability=delay_probability,
            primary_risk_drivers=risk_drivers,
        )

        # 6. Expedite Decision Policy
        recommendation, justification, urgency_score = cls._determine_expedite_action(
            risk_level=risk_level,
            shipment_status=shipment_status,
            inventory_coverage_days=inventory_coverage_days,
            replenishment_urgency=replenishment_urgency,
            config=cfg,
        )

        expedite_decision = ExpediteDecision(
            recommendation=recommendation,
            justification=justification,
            urgency_score=urgency_score,
        )

        return risk_summary, expedite_decision

    @classmethod
    def _determine_expedite_action(
        cls,
        risk_level: LogisticsRiskLevel,
        shipment_status: ShipmentStatus,
        inventory_coverage_days: float,
        replenishment_urgency: str,
        config: LogisticsConfiguration,
    ) -> Tuple[ExpediteRecommendation, str, float]:
        critical_cov = config.stockout_critical_threshold_days
        warning_cov = config.stockout_warning_threshold_days

        if inventory_coverage_days <= critical_cov or (
            shipment_status in (ShipmentStatus.DELAYED, ShipmentStatus.EXCEPTION)
            and inventory_coverage_days <= (critical_cov * 2)
        ):
            return (
                ExpediteRecommendation.EXPEDITED_CRITICAL,
                f"Critical inventory coverage ({inventory_coverage_days:.1f}d) under shipment disruption. "
                "Immediate expedited shipping required.",
                0.95,
            )

        if risk_level == LogisticsRiskLevel.CRITICAL or replenishment_urgency == "EXPEDITED_REPLENISHMENT":
            return (
                ExpediteRecommendation.EXPEDITED_SHIPPING_REQUIRED,
                f"Critical logistics risk or urgent replenishment required (Coverage: {inventory_coverage_days:.1f}d).",
                0.80,
            )

        if risk_level == LogisticsRiskLevel.HIGH or shipment_status == ShipmentStatus.DELAYED:
            if inventory_coverage_days > warning_cov:
                return (
                    ExpediteRecommendation.MONITOR,
                    f"Shipment delayed or high risk, but inventory buffer is robust "
                    f"({inventory_coverage_days:.1f}d). Monitor situation.",
                    0.50,
                )
            return (
                ExpediteRecommendation.EXPEDITED_REPLENISHMENT,
                f"Elevated logistics risk with moderate inventory buffer ({inventory_coverage_days:.1f}d). "
                "Plan expedited replenishment.",
                0.65,
            )

        if risk_level in (LogisticsRiskLevel.MODERATE, LogisticsRiskLevel.NOT_ASSESSABLE):
            return (
                ExpediteRecommendation.MONITOR,
                "Moderate logistics friction or unassessed active transit. Monitor situation.",
                0.30,
            )

        return (
            ExpediteRecommendation.NORMAL_TRANSPORT,
            "Logistics operations stable. Proceed with normal transport.",
            0.10,
        )