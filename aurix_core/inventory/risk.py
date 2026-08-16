from typing import Any, Dict


class InventoryRiskEvaluator:
    """Evaluates stockout risk and excess inventory exposure deterministically."""

    @staticmethod
    def evaluate_risk(
        on_hand_qty: float,
        inventory_position: float,
        reorder_point: float,
        safety_stock: float,
        lead_time_days: float,
        daily_demand: float,
    ) -> Dict[str, Any]:
        if daily_demand <= 0.0:
            return {
                "stockout_risk": "NOT_ASSESSABLE",
                "excess_status": "NOMINAL",
                "risk_score": 0.0,
                "reason": "Daily demand is zero or uncomputable.",
            }

        on_hand_coverage = on_hand_qty / daily_demand
        is_below_rop = inventory_position <= reorder_point

        if on_hand_coverage < lead_time_days and is_below_rop:
            stockout_risk = "STOCKOUT_IMMINENT"
            risk_score = 0.95
            risk_reason = (
                f"On-hand coverage ({on_hand_coverage:.1f} days) is less than lead time "
                f"({lead_time_days:.1f} days) and position ({inventory_position:.1f}) is at or below ROP ({reorder_point:.1f})."
            )
        elif is_below_rop:
            stockout_risk = "HIGH_RISK"
            risk_score = 0.75
            risk_reason = f"Inventory position ({inventory_position:.1f}) is below ROP ({reorder_point:.1f})."
        elif inventory_position <= (reorder_point + (0.5 * safety_stock)):
            stockout_risk = "MODERATE_RISK"
            risk_score = 0.40
            risk_reason = "Inventory position is approaching reorder threshold."
        else:
            stockout_risk = "LOW_RISK"
            risk_score = 0.10
            risk_reason = "Inventory buffer is healthy."

        excess_threshold = reorder_point + (3.0 * safety_stock)
        is_excess = inventory_position > excess_threshold or on_hand_coverage > 90.0

        if is_excess:
            excess_status = "EXCESS_INVENTORY"
            excess_qty = max(0.0, inventory_position - reorder_point)
        else:
            excess_status = "NOMINAL"
            excess_qty = 0.0

        return {
            "stockout_risk": stockout_risk,
            "excess_status": excess_status,
            "excess_quantity": round(excess_qty, 2),
            "risk_score": risk_score,
            "reason": risk_reason,
        }
