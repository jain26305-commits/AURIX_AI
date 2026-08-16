from typing import Any, Dict, List, Tuple


class InventoryReadinessGate:
    """Audits whether sufficient inputs exist to perform inventory calculations."""

    @staticmethod
    def evaluate(sku_inputs: Dict[str, Any]) -> Tuple[bool, List[Dict[str, str]]]:
        missing: List[Dict[str, str]] = []

        if sku_inputs.get("lead_time_days") is None:
            missing.append(
                {
                    "field": "lead_time_days",
                    "state": "USER_INPUT_REQUIRED",
                    "domain": "inventory",
                    "severity": "CRITICAL",
                    "prompt": "Enter the typical supplier lead time in days.",
                }
            )

        if sku_inputs.get("expected_daily_demand") is None:
            missing.append(
                {
                    "field": "expected_daily_demand",
                    "state": "USER_INPUT_REQUIRED",
                    "domain": "demand",
                    "severity": "CRITICAL",
                    "prompt": "Expected daily demand is required (via Phase 3 forecast or Phase 2 history).",
                }
            )

        if sku_inputs.get("unit_cost") is None:
            missing.append(
                {
                    "field": "unit_cost",
                    "state": "USER_INPUT_REQUIRED",
                    "domain": "finance",
                    "severity": "MODERATE",
                    "prompt": "Unit cost is required for financial exposure and EOQ modeling.",
                }
            )

        is_computable = len([m for m in missing if m["severity"] == "CRITICAL"]) == 0
        return is_computable, missing
