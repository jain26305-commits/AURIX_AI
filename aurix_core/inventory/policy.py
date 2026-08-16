from typing import Any, Dict, Optional
from .mathematics import InventoryMathematics


class InventoryPolicyEngine:
    """Determines replenishment policy triggers and recommended order quantities."""

    @staticmethod
    def evaluate_policy(
        inventory_position: float,
        reorder_point: float,
        eoq: Optional[float],
        daily_demand: float,
        lead_time_days: float,
        moq: Optional[float] = None,
        pack_size: Optional[float] = None,
    ) -> Dict[str, Any]:
        is_triggered = inventory_position <= reorder_point
        policy_name = "REORDER_POINT_CONTINUOUS_REVIEW"

        if not is_triggered:
            return {
                "policy": policy_name,
                "triggered": False,
                "raw_order_quantity": 0.0,
                "constrained_order_quantity": 0.0,
                "constraint_applied": False,
                "constraint_reason": None,
                "recommendation": "DO_NOT_ORDER",
                "reason": f"Inventory position ({inventory_position:.1f}) is above ROP ({reorder_point:.1f}).",
            }

        target_buffer = max(reorder_point, daily_demand * lead_time_days)
        base_deficit = max(0.0, target_buffer - inventory_position)

        if eoq is not None and eoq > 0.0:
            raw_qty = max(eoq, base_deficit)
        else:
            raw_qty = base_deficit if base_deficit > 0.0 else daily_demand * lead_time_days

        constrained_qty, constraint_applied, constraint_reason = InventoryMathematics.apply_order_constraints(
            raw_quantity=raw_qty,
            moq=moq,
            pack_size=pack_size,
        )

        return {
            "policy": policy_name,
            "triggered": True,
            "raw_order_quantity": round(raw_qty, 2),
            "constrained_order_quantity": round(constrained_qty, 2),
            "constraint_applied": constraint_applied,
            "constraint_reason": constraint_reason,
            "recommendation": "REPLENISH",
            "reason": (
                f"Inventory position ({inventory_position:.1f}) is at or below ROP ({reorder_point:.1f}). "
                f"Recommending order quantity of {constrained_qty:.1f} units."
            ),
        }
