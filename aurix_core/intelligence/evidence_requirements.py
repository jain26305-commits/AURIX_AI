"""
AURIX deterministic evidence requirement planner.

Determines which evidence sources are relevant to the semantic meaning of
the user's question. Missing sources reduce evidence coverage but do not
automatically prevent an answer.
"""

from __future__ import annotations

from typing import Dict, List


SOURCE_PRIORITY: Dict[str, int] = {
    "product": 100,
    "inventory_position": 100,
    "replenishment_policy": 95,
    "forecast": 95,
    "inventory_transactions": 80,
    "order_lines": 85,
    "orders": 80,
    "suppliers": 80,
    "supplier_performance": 90,
    "shipments": 80,
    "shipment_evaluation": 90,
    "carrier_performance": 75,
    "lane_performance": 75,
    "financial_baseline": 80,
    "intelligence_snapshot": 100,
}


class EvidenceRequirementPlanner:
    """Maps semantic intent to deterministic evidence requirements."""

    @classmethod
    def required_sources(
        cls,
        concepts: List[str],
        dimensions: List[str],
        question_type: str,
    ) -> List[str]:

        sources: List[str] = []

        def add(*names: str) -> None:
            for name in names:
                if name not in sources:
                    sources.append(name)

        concept_set = set(concepts)
        dimension_set = set(dimensions)

        # ------------------------------------
        # INVENTORY
        # ------------------------------------
        if "INVENTORY_POSITION" in dimension_set:
            add("product", "inventory_position")

            if question_type in {
                "DIAGNOSE",
                "RECOMMEND",
                "TREND",
                "SIMULATE",
            }:
                add(
                    "replenishment_policy",
                    "forecast",
                    "inventory_transactions",
                    "order_lines",
                    "orders",
                )

            if "INBOUND" in concept_set:
                add("orders", "order_lines")

        # ------------------------------------
        # SUPPLIER
        # ------------------------------------
        if "SUPPLIER_PERFORMANCE" in dimension_set:
            add(
                "suppliers",
                "supplier_performance",
            )

            if question_type in {"DIAGNOSE", "RECOMMEND", "TREND"}:
                add(
                    "purchase_orders",
                    "shipments",
                    "shipment_evaluation",
                )

        # ------------------------------------
        # LOGISTICS
        # ------------------------------------
        if "LOGISTICS" in dimension_set:
            add("shipments", "shipment_evaluation")

            if question_type in {"DIAGNOSE", "RECOMMEND", "TREND"}:
                add("carrier_performance", "lane_performance")

        # ------------------------------------
        # DEMAND
        # ------------------------------------
        if "DEMAND" in dimension_set:
            add(
                "order_lines",
                "orders",
                "forecast",
            )

        # ------------------------------------
        # MANUFACTURING
        # ------------------------------------
        if "MANUFACTURING" in dimension_set:
            add(
                "product",
                "inventory_position",
            )

            if "MRP" in concept_set:
                add("bom", "bom_lines")

            if "CAPACITY" in concept_set:
                add("work_centers", "capacity_checks")

        # ------------------------------------
        # ECONOMICS
        # ------------------------------------
        if "ECONOMICS" in dimension_set:
            add(
                "financial_baseline",
                "product",
                "inventory_position",
            )

        # ------------------------------------
        # NETWORK / PORTFOLIO
        # ------------------------------------
        if "NETWORK" in dimension_set or question_type == "SUMMARIZE":
            add("intelligence_snapshot")

        # Risk questions get broader evidence.
        if "RISK" in concept_set:
            if "INVENTORY_POSITION" in dimension_set:
                add(
                    "inventory_position",
                    "replenishment_policy",
                    "forecast",
                )

            if "SUPPLIER_PERFORMANCE" in dimension_set:
                add(
                    "supplier_performance",
                    "shipments",
                )

            if "LOGISTICS" in dimension_set:
                add(
                    "shipment_evaluation",
                    "carrier_performance",
                    "lane_performance",
                )

        # Diagnostic questions need supporting evidence, not just the primary table.
        if question_type == "DIAGNOSE":
            add(
                "inventory_transactions",
                "orders",
                "order_lines",
            )

        # Recommendation questions need enough evidence to justify direction.
        if question_type == "RECOMMEND":
            add(
                "replenishment_policy",
                "forecast",
                "supplier_performance",
                "shipment_evaluation",
                "financial_baseline",
            )

        return sorted(
            sources,
            key=lambda source: SOURCE_PRIORITY.get(source, 0),
            reverse=True,
        )
