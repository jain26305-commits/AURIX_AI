"""
AURIX Deterministic Decision Gate.

Maps business decisions to the evidence required to support them.

This prevents the deterministic engine from treating every missing
enterprise dataset as equally important for every question.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DecisionGate:
    decision: str
    required_sources: List[str] = field(default_factory=list)
    optional_sources: List[str] = field(default_factory=list)
    available_sources: List[str] = field(default_factory=list)
    missing_required_sources: List[str] = field(
        default_factory=list
    )
    missing_optional_sources: List[str] = field(
        default_factory=list
    )

    can_answer: bool = False
    can_recommend: bool = False
    can_establish_causality: bool = False


class DeterministicDecisionGate:
    """
    Defines evidence requirements for common enterprise decisions.
    """

    REQUIREMENTS: Dict[str, List[str]] = {
        "INVENTORY_STATUS": [
            "inventory_position",
        ],

        "INVENTORY_PROTECTION": [
            "inventory_position",
        ],

        "STOCKOUT_FORECAST": [
            "inventory_position",
            "forecast",
        ],

        "REPLENISHMENT_ADEQUACY": [
            "inventory_position",
            "replenishment_policy",
        ],

        "INBOUND_COVERAGE": [
            "inventory_position",
        ],

        "SUPPLIER_CAUSALITY": [
            "supplier_performance",
            "purchase_orders",
            "shipment_evaluation",
        ],

        "SUPPLIER_COMPARISON": [
            "supplier_performance",
            "suppliers",
        ],

        "SHIPMENT_ETA": [
            "shipments",
            "shipment_evaluation",
        ],

        "SHIPMENT_DELAY": [
            "shipments",
            "shipment_evaluation",
        ],

        "SHIPMENT_CAUSALITY": [
            "inventory_position",
            "shipments",
            "shipment_evaluation",
        ],

        "EXECUTIVE_RISK_SUMMARY": [
            "intelligence_snapshot",
        ],

        "DEMAND_CAUSALITY": [
            "inventory_position",
            "forecast",
        ],

        "WORKING_CAPITAL": [
            "inventory_position",
            "financial_baseline",
        ],

        "EXPEDITE_DECISION": [
            "inventory_position",
            "replenishment_policy",
            "forecast",
        ],
    }

    @classmethod
    def evaluate(
        cls,
        decision: str,
        available_sources: List[str],
    ) -> DecisionGate:

        decision_key = decision.upper()

        required = list(
            cls.REQUIREMENTS.get(
                decision_key,
                [],
            )
        )

        available = set(
            available_sources
        )

        missing = [
            source
            for source in required
            if source not in available
        ]

        return DecisionGate(
            decision=decision_key,
            required_sources=required,
            available_sources=list(
                available_sources
            ),
            missing_required_sources=missing,
            can_answer=(
                len(missing) == 0
            ),
            can_recommend=(
                len(missing) == 0
            ),
            can_establish_causality=(
                len(missing) == 0
            ),
        )


__all__ = [
    "DecisionGate",
    "DeterministicDecisionGate",
]
