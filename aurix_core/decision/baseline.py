"""Current state baseline evaluation engine for optimization comparisons."""

from typing import Optional
from aurix_core.schema.phase5_contract import TrackedValue, ValueState
from aurix_core.schema.phase8_contract import NodeIdentity
from aurix_core.schema.phase9_contract import BaselineState


class BaselineEngine:
    """Evaluates the current operational and financial state of a node or sub-network."""

    @classmethod
    def evaluate_node_baseline(
        cls,
        node: NodeIdentity,
        unit_cost: Optional[float] = None,
        target_coverage_days: Optional[float] = None,
    ) -> BaselineState:
        """
        Establishes the current ground truth for a node before any optimization is applied.
        Strictly prevents fabrication if financial or operational targets are missing.
        """
        # 1. Inventory Value (Financial)
        inv_val = float(node.inventory.value) if (node.inventory and node.inventory.value is not None) else None

        if inv_val is not None and unit_cost is not None and unit_cost >= 0.0:
            total_val = round(inv_val * unit_cost, 2)
            inv_tv = TrackedValue(
                value=total_val,
                state=ValueState.DERIVED,
                source="BASELINE_INVENTORY_VALUE",
            )
        else:
            inv_tv = TrackedValue(
                value=None,
                state=ValueState.UNAVAILABLE,
                source="MISSING_UNIT_COST_OR_INVENTORY",
            )

        # 2. Coverage Days (Operational)
        demand_val = float(node.demand.value) if (node.demand and node.demand.value is not None) else None
        cov_days: Optional[float] = None

        if inv_val is not None and demand_val is not None and demand_val > 0.0:
            cov_days = round(inv_val / demand_val, 2)
            cov_tv = TrackedValue(
                value=cov_days,
                state=ValueState.DERIVED,
                source="BASELINE_COVERAGE_CALCULATION",
            )
        elif inv_val is not None and demand_val == 0.0:
            cov_days = float("inf")
            cov_tv = TrackedValue(
                value=float("inf"),
                state=ValueState.DERIVED,
                source="ZERO_DEMAND_INFINITE_COVERAGE",
            )
        else:
            cov_tv = TrackedValue(
                value=None,
                state=ValueState.UNAVAILABLE,
                source="MISSING_INVENTORY_OR_DEMAND",
            )

        # 3. Service Exposure Risk
        if cov_days is not None and target_coverage_days is not None and target_coverage_days > 0.0:
            if cov_days == float("inf"):
                risk_val = 0.0
            else:
                risk_val = round(max(0.0, min(1.0, 1.0 - (cov_days / target_coverage_days))), 2)

            risk_tv = TrackedValue(
                value=risk_val,
                state=ValueState.DERIVED,
                source="COVERAGE_DEFICIT_RISK",
            )
        else:
            risk_tv = TrackedValue(
                value=None,
                state=ValueState.UNAVAILABLE,
                source="MISSING_TARGET_COVERAGE_OR_INVENTORY",
            )

        # 4. Bottleneck Active
        cap_val = float(node.capacity.value) if (node.capacity and node.capacity.value is not None) else None
        bottleneck_active = False

        if cap_val is not None and demand_val is not None and cap_val > 0.0:
            bottleneck_active = demand_val > cap_val

        return BaselineState(
            inventory_value=inv_tv,
            coverage_days=cov_tv,
            service_exposure_risk=risk_tv,
            bottleneck_active=bottleneck_active,
        )
