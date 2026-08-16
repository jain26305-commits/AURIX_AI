"""Deterministic constraint-satisfaction solver for supply chain allocations and rebalancing."""

import math
from typing import List, Optional, Tuple
from aurix_core.schema.phase9_contract import FeasibilityStatus


class ConstraintSatisfactionSolver:
    """Solves allocation and rebalancing problems while strictly enforcing operational physics."""

    @classmethod
    def solve_rebalancing_quantity(
        cls,
        source_available_excess: float,
        destination_shortage: float,
        destination_available_capacity: Optional[float] = None,
        pack_size: Optional[float] = None,
        min_transfer_quantity: float = 1.0,
    ) -> Tuple[float, FeasibilityStatus, List[str]]:
        """
        Determines the transfer quantity between two nodes based on excesses, shortages, and physical constraints.
        Enforces Rule 7: Always attempt to fully satisfy the requirement (ceil) before constraining.
        """
        constraints_evaluated: List[str] = []

        if destination_shortage <= 0.0:
            constraints_evaluated.append("Destination shortage is zero or negative. No transfer needed.")
            return 0.0, FeasibilityStatus.UNCONSTRAINED, constraints_evaluated

        if source_available_excess <= 0.0:
            constraints_evaluated.append("Source excess is zero or negative. Cannot fulfill transfer.")
            return 0.0, FeasibilityStatus.INSUFFICIENT_INVENTORY, constraints_evaluated

        # 1. Base Requirement to satisfy the shortage
        proposed_qty = destination_shortage
        constraints_evaluated.append(f"Initial target quantity set to shortage: {proposed_qty:.2f}.")

        # 2. Apply Pack Size (Round UP to ensure requirement satisfaction)
        if pack_size is not None and pack_size > 0.0:
            packs_required = math.ceil(proposed_qty / pack_size)
            proposed_qty = float(packs_required * pack_size)
            constraints_evaluated.append(
                f"Quantity rounded up to {proposed_qty:.2f} to satisfy pack size of {pack_size:.2f} "
                f"({packs_required} packs)."
            )

        # 3. Apply Physical Bounds (Capacity and Excess)
        limiting_factor = min(
            source_available_excess,
            destination_available_capacity if destination_available_capacity is not None else float('inf')
        )

        # Check if proposed quantity violates bounds
        if proposed_qty > limiting_factor:
            # We cannot send the full proposed amount. We must scale back.
            cap_str = (
                f"{destination_available_capacity:.2f}"
                if destination_available_capacity is not None
                else "UNCONSTRAINED"
            )
            constraints_evaluated.append(
                f"Proposed quantity {proposed_qty:.2f} violates physical bounds "
                f"(Excess: {source_available_excess:.2f}, Capacity: {cap_str})."
            )

            if pack_size is not None and pack_size > 0.0:
                # Scale back by flooring based on the limiting factor
                packs_allowed = math.floor(limiting_factor / pack_size)
                proposed_qty = float(packs_allowed * pack_size)
                constraints_evaluated.append(
                    f"Quantity scaled down to {proposed_qty:.2f} ({packs_allowed} packs) "
                    "to respect limiting constraint while honoring pack size."
                )
            else:
                proposed_qty = limiting_factor
                constraints_evaluated.append(
                    f"Quantity scaled down to {proposed_qty:.2f} to respect limiting constraint."
                )

        if proposed_qty <= 0.0:
            # Scaled down to zero because constraints are too tight compared to pack size
            p_size = pack_size if (pack_size is not None and pack_size > 0.0) else 0.0
            if source_available_excess < p_size:
                status = FeasibilityStatus.INSUFFICIENT_INVENTORY
            elif destination_available_capacity is not None and destination_available_capacity < p_size:
                status = FeasibilityStatus.INSUFFICIENT_CAPACITY
            else:
                status = FeasibilityStatus.PACK_SIZE_VIOLATION

            constraints_evaluated.append("Proposed quantity fell to zero after applying constraints.")
            return 0.0, status, constraints_evaluated

        # 4. MOQ Check
        if proposed_qty < min_transfer_quantity:
            constraints_evaluated.append(
                f"Proposed quantity {proposed_qty:.2f} is below the Minimum Order Quantity "
                f"(MOQ) of {min_transfer_quantity:.2f}."
            )
            return 0.0, FeasibilityStatus.MOQ_VIOLATION, constraints_evaluated

        constraints_evaluated.append(f"Final validated transfer quantity: {proposed_qty:.2f}.")
        return proposed_qty, FeasibilityStatus.FEASIBLE, constraints_evaluated