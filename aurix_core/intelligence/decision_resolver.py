"""
AURIX deterministic business-decision resolver.
"""

from __future__ import annotations

from typing import Any, Optional

from aurix_core.intelligence.domain_registry import (
    DecisionSpec,
    DomainRegistry,
)


class DeterministicDecisionResolver:

    @classmethod
    def resolve(
        cls,
        *,
        query: str,
        domain: Optional[str],
        intent: Optional[str],
        concepts: Optional[list[str]] = None,
        explicit_decision: Optional[str] = None,
    ) -> Optional[DecisionSpec]:

        if explicit_decision:
            return DomainRegistry.get(
                explicit_decision
            )

        q = query.lower()
        concepts_upper = {
            str(value).upper()
            for value in (concepts or [])
        }

        domain_upper = (
            (domain or "").upper()
        )
        intent_upper = (
            (intent or "").upper()
        )

        # --------------------------------------------------
        # Highly specific business decisions first.
        # --------------------------------------------------

        if (
            domain_upper == "INVENTORY"
            and (
                "stock out" in q
                or "stockout" in q
                or "run out" in q
                or "run out of" in q
                or "deplete" in q
                or "depleted" in q
            )
        ):
            return DomainRegistry.STOCKOUT_FORECAST

        if (
            domain_upper == "INVENTORY"
            and (
                "replenish" in q
                or "replenishment" in q
                or "reorder" in q
                or "buy more" in q
                or "refill" in q
            )
        ):
            return DomainRegistry.REPLENISHMENT_ADEQUACY

        if (
            domain_upper == "SUPPLY"
            and intent_upper in {
                "COMPARE",
                "RANK",
            }
        ):
            return DomainRegistry.SUPPLIER_COMPARISON

        if (
            domain_upper == "SUPPLY"
            and intent_upper == "DIAGNOSE"
        ):
            return DomainRegistry.SUPPLIER_CAUSALITY

        if (
            domain_upper == "LOGISTICS"
            and (
                "eta" in q
                or "when will" in q
                or "when should" in q
                or "arrive" in q
            )
        ):
            return DomainRegistry.SHIPMENT_ETA

        if (
            domain_upper == "LOGISTICS"
            and (
                "late" in q
                or "delay" in q
                or "delayed" in q
                or "behind" in q
                or "slipped" in q
            )
        ):
            return DomainRegistry.SHIPMENT_DELAY

        if (
            domain_upper == "ECONOMICS"
            and (
                "working capital" in q
                or "cash tied" in q
                or "cash locked" in q
                or "capital tied" in q
                or "capital locked" in q
            )
        ):
            return DomainRegistry.WORKING_CAPITAL

        if (
            domain_upper == "MANUFACTURING"
            and (
                "bottleneck" in q
                or "constrained" in q
                or "constraint" in q
            )
        ):
            return DomainRegistry.BOTTLENECK_DIAGNOSIS

        if (
            domain_upper == "MANUFACTURING"
            and (
                "capacity" in q
                or "utilization" in q
            )
        ):
            return DomainRegistry.CAPACITY_STATUS

        if (
            domain_upper in {
                "RISK",
                "NETWORK",
                "OVERVIEW",
            }
            and (
                "executive" in q
                or "risk summary" in q
                or "enterprise risk" in q
            )
        ):
            return DomainRegistry.EXECUTIVE_RISK_SUMMARY

        if (
            domain_upper == "PROCESS"
            and (
                "bottleneck" in q
                or "cycle time" in q
                or "sla" in q
            )
        ):
            return DomainRegistry.PROCESS_BOTTLENECK

        if (
            intent_upper == "SIMULATE"
        ):
            return DomainRegistry.SCENARIO_RESULT

        # --------------------------------------------------
        # Conservative domain fallbacks.
        # --------------------------------------------------

        if domain_upper == "INVENTORY":
            return DomainRegistry.INVENTORY_STATUS

        if domain_upper == "SUPPLY":
            return DomainRegistry.SUPPLIER_STATUS

        return None