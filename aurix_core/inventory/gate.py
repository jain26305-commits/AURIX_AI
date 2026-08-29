import math
from typing import Any, Dict, List, Tuple


class InventoryReadinessGate:
    """
    Audits whether sufficient and valid inputs exist for inventory
    planning calculations.

    This gate distinguishes planning prerequisites from state-dependent
    inventory observations. Missing on-hand inventory does not block
    planning, but supplied malformed values fail closed.
    """

    @staticmethod
    def _is_finite_number(value: Any) -> bool:
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value))
        )

    @classmethod
    def evaluate(
        cls,
        sku_inputs: Dict[str, Any],
    ) -> Tuple[bool, List[Dict[str, str]]]:

        issues: List[Dict[str, str]] = []

        # --------------------------------------------------------
        # Planning-critical inputs
        # --------------------------------------------------------

        lead_time = sku_inputs.get("lead_time_days")

        if lead_time is None:
            issues.append(
                {
                    "field": "lead_time_days",
                    "state": "USER_INPUT_REQUIRED",
                    "domain": "inventory",
                    "severity": "CRITICAL",
                    "prompt": "Enter the typical supplier lead time in days.",
                }
            )
        elif (
            not cls._is_finite_number(lead_time)
            or float(lead_time) <= 0.0
        ):
            issues.append(
                {
                    "field": "lead_time_days",
                    "state": "INVALID_INPUT",
                    "domain": "inventory",
                    "severity": "CRITICAL",
                    "prompt": "Lead time must be a finite positive number of days.",
                }
            )

        demand = sku_inputs.get("expected_daily_demand")

        if demand is None:
            issues.append(
                {
                    "field": "expected_daily_demand",
                    "state": "USER_INPUT_REQUIRED",
                    "domain": "demand",
                    "severity": "CRITICAL",
                    "prompt": "Expected daily demand is required (via Phase 3 forecast or Phase 2 history).",
                }
            )
        elif (
            not cls._is_finite_number(demand)
            or float(demand) <= 0.0
        ):
            issues.append(
                {
                    "field": "expected_daily_demand",
                    "state": "INVALID_INPUT",
                    "domain": "demand",
                    "severity": "CRITICAL",
                    "prompt": "Expected daily demand must be a finite positive quantity.",
                }
            )

        unit_cost = sku_inputs.get("unit_cost")

        if unit_cost is None:
            issues.append(
                {
                    "field": "unit_cost",
                    "state": "USER_INPUT_REQUIRED",
                    "domain": "finance",
                    "severity": "MODERATE",
                    "prompt": "Unit cost is required for financial exposure and EOQ modeling.",
                }
            )
        elif (
            not cls._is_finite_number(unit_cost)
            or float(unit_cost) < 0.0
        ):
            issues.append(
                {
                    "field": "unit_cost",
                    "state": "INVALID_INPUT",
                    "domain": "finance",
                    "severity": "CRITICAL",
                    "prompt": "Unit cost must be a finite non-negative value.",
                }
            )

        # --------------------------------------------------------
        # Optional inventory observations
        #
        # Absence does not block planning.
        # Supplied invalid values DO block execution.
        # --------------------------------------------------------

        on_hand = sku_inputs.get("on_hand_qty")

        if on_hand is not None and (
            not cls._is_finite_number(on_hand)
            or float(on_hand) < 0.0
        ):
            issues.append(
                {
                    "field": "on_hand_qty",
                    "state": "INVALID_INPUT",
                    "domain": "inventory",
                    "severity": "CRITICAL",
                    "prompt": "On-hand inventory must be a finite non-negative quantity.",
                }
            )

        inbound = sku_inputs.get("inbound_qty")

        if inbound is not None and (
            not cls._is_finite_number(inbound)
            or float(inbound) < 0.0
        ):
            issues.append(
                {
                    "field": "inbound_qty",
                    "state": "INVALID_INPUT",
                    "domain": "inventory",
                    "severity": "CRITICAL",
                    "prompt": "Inbound inventory must be a finite non-negative quantity.",
                }
            )

        committed = sku_inputs.get("committed_qty")

        if committed is not None and (
            not cls._is_finite_number(committed)
            or float(committed) < 0.0
        ):
            issues.append(
                {
                    "field": "committed_qty",
                    "state": "INVALID_INPUT",
                    "domain": "inventory",
                    "severity": "CRITICAL",
                    "prompt": "Committed inventory must be a finite non-negative quantity.",
                }
            )

        is_computable = not any(
            issue["severity"] == "CRITICAL"
            for issue in issues
        )

        return is_computable, issues
