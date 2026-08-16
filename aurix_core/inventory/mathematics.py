import math
from typing import Optional, Tuple


class InventoryMathematics:
    """Pure mathematical functions for inventory modeling with zero-division protection."""

    @staticmethod
    def calculate_combined_std(
        daily_demand_mean: float,
        daily_demand_std: float,
        lead_time_days: float,
        lead_time_std: float = 0.0,
    ) -> float:
        d = max(0.0, daily_demand_mean)
        sigma_d = max(0.0, daily_demand_std)
        L = max(0.0, lead_time_days)
        sigma_L = max(0.0, lead_time_std)

        variance_dlt = (L * (sigma_d**2)) + ((d**2) * (sigma_L**2))
        return math.sqrt(max(0.0, variance_dlt))

    @staticmethod
    def calculate_safety_stock(z_score: float, combined_std: float) -> float:
        z = max(0.0, z_score)
        sigma = max(0.0, combined_std)
        return round(z * sigma, 2)

    @staticmethod
    def calculate_reorder_point(
        daily_demand_mean: float,
        lead_time_days: float,
        safety_stock: float,
    ) -> float:
        d = max(0.0, daily_demand_mean)
        L = max(0.0, lead_time_days)
        ss = max(0.0, safety_stock)
        return round((d * L) + ss, 2)

    @staticmethod
    def calculate_eoq(
        annual_demand: float,
        ordering_cost: float,
        holding_cost_per_unit_year: float,
    ) -> Optional[float]:
        D = max(0.0, annual_demand)
        S = max(0.0, ordering_cost)
        H = max(0.0, holding_cost_per_unit_year)

        if D <= 0.0 or S <= 0.0 or H <= 0.0:
            return None

        eoq_raw = math.sqrt((2.0 * D * S) / H)
        return round(eoq_raw, 2)

    @staticmethod
    def apply_order_constraints(
        raw_quantity: float,
        moq: Optional[float] = None,
        pack_size: Optional[float] = None,
    ) -> Tuple[float, bool, Optional[str]]:
        qty = max(0.0, raw_quantity)
        if qty == 0.0:
            return 0.0, False, None

        constraint_applied = False
        reasons = []

        if moq is not None and moq > 0.0:
            if qty < moq:
                qty = moq
                constraint_applied = True
                reasons.append(f"MOQ_APPLIED({moq})")

        if pack_size is not None and pack_size > 0.0:
            remainder = qty % pack_size
            if remainder > 1e-6:
                qty = math.ceil(qty / pack_size) * pack_size
                constraint_applied = True
                reasons.append(f"PACK_SIZE_MULTIPLE({pack_size})")

        reason_str = ", ".join(reasons) if constraint_applied else None
        return round(qty, 2), constraint_applied, reason_str

    @staticmethod
    def calculate_inventory_position(on_hand: float, inbound: float = 0.0, committed: float = 0.0) -> float:
        oh = float(on_hand)
        ib = max(0.0, float(inbound))
        cm = max(0.0, float(committed))
        return round(oh + ib - cm, 2)

    @staticmethod
    def calculate_coverage_days(inventory_qty: float, daily_demand_mean: float) -> Optional[float]:
        d = max(0.0, daily_demand_mean)
        if d <= 0.0:
            return None
        inv = float(inventory_qty)
        return round(inv / d, 1)
