"""Supplier evaluation engine implementing multi-criteria risk scoring and eligibility checks."""

from typing import Optional
from aurix_core.schema.phase6_contract import (
    CapacityStatus,
    SupplierCandidate,
    SupplierEvaluation,
    SupplyRiskLevel,
)
from aurix_core.supply.config import SupplyConfiguration

__all__ = ["SupplierEvaluator", "SupplierCandidate"]


class SupplierEvaluator:
    """Evaluates individual supplier candidates against inventory requirements and policy thresholds."""

    @classmethod
    def evaluate_supplier(
        cls,
        candidate: SupplierCandidate,
        required_quantity: float,
        config: Optional[SupplyConfiguration] = None,
    ) -> SupplierEvaluation:
        cfg = config or SupplyConfiguration()

        supplier_id = candidate.supplier_id
        supplier_name = candidate.supplier_name
        currency = candidate.currency

        # 1. Price Validation & Eligibility
        unit_price_obj = candidate.unit_price
        if not unit_price_obj or unit_price_obj.value is None or float(unit_price_obj.value) <= 0.0:
            return SupplierEvaluation(
                supplier_id=supplier_id,
                supplier_name=supplier_name,
                is_eligible=False,
                rejection_reason="INVALID_OR_MISSING_UNIT_PRICE",
                unit_price=0.0,
                currency=currency,
                raw_order_quantity=required_quantity,
                constrained_order_quantity=0.0,
                moq_applied=False,
                pack_size_applied=False,
                total_purchase_cost=None,
                capacity_status=CapacityStatus.CAPACITY_UNKNOWN,
                supply_risk_level=SupplyRiskLevel.CRITICAL,
                supply_risk_score=1.0,
                selection_status="REJECTED",
                preference_reasons=["INELIGIBLE_PRICE"],
            )

        unit_price = float(unit_price_obj.value)

        # 2. MOQ & Pack Size Constraints
        moq_val = float(candidate.moq.value) if (candidate.moq and candidate.moq.value is not None) else 0.0
        pack_size_val = (
            float(candidate.pack_size.value) if (candidate.pack_size and candidate.pack_size.value is not None) else 1.0
        )

        constrained_qty = max(required_quantity, moq_val)
        moq_applied = constrained_qty > required_quantity

        if pack_size_val > 0.0 and constrained_qty % pack_size_val != 0.0:
            remainder = constrained_qty % pack_size_val
            constrained_qty += pack_size_val - remainder
            pack_size_applied = True
        else:
            pack_size_applied = False

        total_purchase_cost = round(constrained_qty * unit_price, 2)

        # 3. Capacity Evaluation
        cap_obj = candidate.capacity_units
        if cap_obj and cap_obj.value is not None:
            capacity_units = float(cap_obj.value)
            if capacity_units < constrained_qty:
                capacity_status = CapacityStatus.CAPACITY_CONSTRAINED
            else:
                capacity_status = CapacityStatus.CAPACITY_SUFFICIENT
        else:
            capacity_status = CapacityStatus.CAPACITY_UNKNOWN

        # 4. Supply Risk Scoring
        risk_score = cfg.base_risk_score
        risk_drivers = []

        perf = candidate.performance
        if perf:
            otif_obj = perf.otif_rate
            if otif_obj and otif_obj.value is not None:
                otif_val = float(otif_obj.value)
                if otif_val < cfg.otif_threshold:
                    risk_score += cfg.otif_penalty
                    risk_drivers.append(f"POOR_OTIF({otif_val * 100:.1f}%)")

            fill_obj = perf.fill_rate
            if fill_obj and fill_obj.value is not None:
                fill_val = float(fill_obj.value)
                if fill_val < cfg.fill_rate_threshold:
                    risk_score += cfg.fill_rate_penalty
                    risk_drivers.append(f"POOR_FILL_RATE({fill_val * 100:.1f}%)")

            std_obj = perf.lead_time_std_days
            mean_obj = perf.mean_lead_time_days
            if std_obj and std_obj.value is not None and mean_obj and mean_obj.value is not None:
                std_val = float(std_obj.value)
                mean_val = float(mean_obj.value)
                if mean_val > 0.0 and (std_val / mean_val) > cfg.lead_time_var_threshold:
                    risk_score += cfg.variability_penalty
                    risk_drivers.append(f"HIGH_LT_VARIABILITY({std_val / mean_val:.2f})")

            defect_obj = perf.defect_rate
            if defect_obj and defect_obj.value is not None:
                defect_val = float(defect_obj.value)
                if defect_val > cfg.defect_rate_threshold:
                    risk_score += cfg.defect_penalty
                    risk_drivers.append(f"HIGH_DEFECT_RATE({defect_val * 100:.1f}%)")
        else:
            risk_score += cfg.unassessed_supplier_penalty
            risk_drivers.append("UNASSESSED_SUPPLIER_HISTORY")

        if capacity_status == CapacityStatus.CAPACITY_CONSTRAINED:
            risk_score += cfg.capacity_constrained_penalty
            risk_drivers.append("CAPACITY_CONSTRAINED")

        risk_score = min(1.0, round(risk_score, 2))

        # Map Risk Score to Risk Level
        if risk_score < cfg.risk_low_max:
            risk_level = SupplyRiskLevel.LOW
        elif risk_score < cfg.risk_moderate_max:
            risk_level = SupplyRiskLevel.MODERATE
        elif risk_score < cfg.risk_high_max:
            risk_level = SupplyRiskLevel.HIGH
        else:
            risk_level = SupplyRiskLevel.CRITICAL

        if not risk_drivers:
            risk_drivers.append("STABLE_PERFORMANCE")

        return SupplierEvaluation(
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            is_eligible=True,
            rejection_reason=None,
            unit_price=unit_price,
            currency=currency,
            raw_order_quantity=required_quantity,
            constrained_order_quantity=constrained_qty,
            moq_applied=moq_applied,
            pack_size_applied=pack_size_applied,
            total_purchase_cost=total_purchase_cost,
            capacity_status=capacity_status,
            supply_risk_level=risk_level,
            supply_risk_score=risk_score,
            selection_status="CANDIDATE",
            preference_reasons=risk_drivers,
        )
