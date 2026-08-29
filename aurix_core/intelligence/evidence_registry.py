
"""
AURIX Canonical Evidence Registry.

This registry describes the evidence vocabulary used by the
intelligence control plane.

It deliberately does NOT retrieve data and does NOT perform
business calculations.

Evidence states:

    FABRIC
        Currently retrievable through EvidenceFabric.

    DERIVED
        Produced from another deterministic subsystem or from
        multiple evidence sources.

    UNIMPLEMENTED
        Referenced by business contracts but not currently
        retrievable through EvidenceFabric.

This distinction prevents AURIX from treating a named source as
available merely because a decision contract mentions it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple


class EvidenceKind(str, Enum):
    FABRIC = "FABRIC"
    DERIVED = "DERIVED"
    UNIMPLEMENTED = "UNIMPLEMENTED"


class EvidenceAuthority(str, Enum):
    AUTHORITATIVE = "AUTHORITATIVE"
    SUPPORTING = "SUPPORTING"
    DERIVED = "DERIVED"


@dataclass(frozen=True)
class EvidenceSourceSpec:
    name: str
    kind: EvidenceKind
    authority: EvidenceAuthority

    domain: str

    tenant_scoped: bool = True
    freshness_required: bool = False

    handler_name: str | None = None

    description: str = ""


class EvidenceRegistry:
    """
    Canonical registry for AURIX evidence sources.
    """

    SOURCES: Dict[str, EvidenceSourceSpec] = {

        # ======================================================
        # CURRENT EVIDENCE FABRIC SOURCES
        # ======================================================

        "product": EvidenceSourceSpec(
            name="product",
            kind=EvidenceKind.FABRIC,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="MASTER_DATA",
            tenant_scoped=True,
            freshness_required=True,
            handler_name="EvidenceFabric.product",
            description=(
                "Product and SKU master data."
            ),
        ),

        "inventory_position": EvidenceSourceSpec(
            name="inventory_position",
            kind=EvidenceKind.FABRIC,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="INVENTORY",
            tenant_scoped=True,
            freshness_required=True,
            handler_name="EvidenceFabric.inventory_position",
            description=(
                "Current inventory position including on-hand, "
                "safety stock and inbound position."
            ),
        ),

        "orders": EvidenceSourceSpec(
            name="orders",
            kind=EvidenceKind.FABRIC,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="DEMAND",
            tenant_scoped=True,
            freshness_required=True,
            handler_name="EvidenceFabric.orders",
            description=(
                "Order-level demand evidence."
            ),
        ),

        "order_lines": EvidenceSourceSpec(
            name="order_lines",
            kind=EvidenceKind.FABRIC,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="DEMAND",
            tenant_scoped=True,
            freshness_required=True,
            handler_name="EvidenceFabric.order_lines",
            description=(
                "Order-line demand detail."
            ),
        ),

        "suppliers": EvidenceSourceSpec(
            name="suppliers",
            kind=EvidenceKind.FABRIC,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="SUPPLY",
            tenant_scoped=True,
            freshness_required=True,
            handler_name="EvidenceFabric.suppliers",
            description=(
                "Supplier master data."
            ),
        ),

        "supplier_performance": EvidenceSourceSpec(
            name="supplier_performance",
            kind=EvidenceKind.FABRIC,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="SUPPLY",
            tenant_scoped=True,
            freshness_required=True,
            handler_name="EvidenceFabric.supplier_performance",
            description=(
                "Supplier performance measurements."
            ),
        ),

        "shipments": EvidenceSourceSpec(
            name="shipments",
            kind=EvidenceKind.FABRIC,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="LOGISTICS",
            tenant_scoped=True,
            freshness_required=True,
            handler_name="EvidenceFabric.shipments",
            description=(
                "Shipment records and delivery state."
            ),
        ),

        "replenishment_policy": EvidenceSourceSpec(
            name="replenishment_policy",
            kind=EvidenceKind.FABRIC,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="INVENTORY",
            tenant_scoped=True,
            freshness_required=False,
            handler_name="EvidenceFabric.replenishment_policy",
            description=(
                "Configured inventory replenishment policy."
            ),
        ),

        "forecast": EvidenceSourceSpec(
            name="forecast",
            kind=EvidenceKind.FABRIC,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="FORECASTING",
            tenant_scoped=True,
            freshness_required=True,
            handler_name="EvidenceFabric.forecast",
            description=(
                "Forecast and projected demand evidence."
            ),
        ),

        "inventory_transactions": EvidenceSourceSpec(
            name="inventory_transactions",
            kind=EvidenceKind.FABRIC,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="INVENTORY",
            tenant_scoped=True,
            freshness_required=True,
            handler_name="EvidenceFabric.inventory_transactions",
            description=(
                "Historical inventory movement evidence."
            ),
        ),

        # ======================================================
        # REFERENCED BUT NOT CURRENTLY PROVIDED BY FABRIC
        # ======================================================

        "shipment_evaluation": EvidenceSourceSpec(
            name="shipment_evaluation",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.SUPPORTING,
            domain="LOGISTICS",
            tenant_scoped=True,
            freshness_required=True,
            description=(
                "Shipment performance evaluation. Referenced by "
                "decision contracts but not currently exposed "
                "as an EvidenceFabric handler."
            ),
        ),

        "carrier_performance": EvidenceSourceSpec(
            name="carrier_performance",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.SUPPORTING,
            domain="LOGISTICS",
            tenant_scoped=True,
            freshness_required=True,
            description=(
                "Carrier performance metrics."
            ),
        ),

        "lane_performance": EvidenceSourceSpec(
            name="lane_performance",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.SUPPORTING,
            domain="LOGISTICS",
            tenant_scoped=True,
            freshness_required=True,
            description=(
                "Lane-level transportation performance."
            ),
        ),

        "purchase_orders": EvidenceSourceSpec(
            name="purchase_orders",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="PROCUREMENT",
            tenant_scoped=True,
            freshness_required=True,
            description=(
                "Purchase-order evidence."
            ),
        ),

        "financial_baseline": EvidenceSourceSpec(
            name="financial_baseline",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="ECONOMICS",
            tenant_scoped=True,
            freshness_required=True,
            description=(
                "Financial baseline used for working-capital, "
                "cash and margin calculations."
            ),
        ),

        "intelligence_snapshot": EvidenceSourceSpec(
            name="intelligence_snapshot",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.DERIVED,
            domain="EXECUTIVE",
            tenant_scoped=True,
            freshness_required=True,
            description=(
                "Derived enterprise intelligence snapshot."
            ),
        ),

        "work_centers": EvidenceSourceSpec(
            name="work_centers",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="MANUFACTURING",
            tenant_scoped=True,
            freshness_required=True,
            description=(
                "Manufacturing work-center master/capacity data."
            ),
        ),

        "work_orders": EvidenceSourceSpec(
            name="work_orders",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="MANUFACTURING",
            tenant_scoped=True,
            freshness_required=True,
            description=(
                "Manufacturing work-order evidence."
            ),
        ),

        "capacity_checks": EvidenceSourceSpec(
            name="capacity_checks",
            kind=EvidenceKind.DERIVED,
            authority=EvidenceAuthority.DERIVED,
            domain="MANUFACTURING",
            tenant_scoped=True,
            freshness_required=True,
            description=(
                "Derived capacity evaluation results."
            ),
        ),

        "oee_metrics": EvidenceSourceSpec(
            name="oee_metrics",
            kind=EvidenceKind.DERIVED,
            authority=EvidenceAuthority.DERIVED,
            domain="MANUFACTURING",
            tenant_scoped=True,
            freshness_required=True,
            description=(
                "Derived OEE calculation input/output structure."
            ),
        ),

        "production_events": EvidenceSourceSpec(
            name="production_events",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="MANUFACTURING",
            tenant_scoped=True,
            freshness_required=True,
            description=(
                "Production event evidence."
            ),
        ),

        "quality_events": EvidenceSourceSpec(
            name="quality_events",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="MANUFACTURING",
            tenant_scoped=True,
            freshness_required=True,
            description=(
                "Quality event evidence."
            ),
        ),

        "demand_schedule": EvidenceSourceSpec(
            name="demand_schedule",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="PLANNING",
            tenant_scoped=True,
            freshness_required=True,
            description=(
                "Planning demand schedule used by MRP."
            ),
        ),

        "bom_relationships": EvidenceSourceSpec(
            name="bom_relationships",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="MANUFACTURING",
            tenant_scoped=True,
            freshness_required=False,
            description=(
                "Bill-of-material relationships."
            ),
        ),

        "process_events": EvidenceSourceSpec(
            name="process_events",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="PROCESS",
            tenant_scoped=True,
            freshness_required=True,
            description=(
                "Process execution events."
            ),
        ),

        "process_metrics": EvidenceSourceSpec(
            name="process_metrics",
            kind=EvidenceKind.DERIVED,
            authority=EvidenceAuthority.DERIVED,
            domain="PROCESS",
            tenant_scoped=True,
            freshness_required=True,
            description=(
                "Derived process performance metrics."
            ),
        ),

        "decision_candidate": EvidenceSourceSpec(
            name="decision_candidate",
            kind=EvidenceKind.DERIVED,
            authority=EvidenceAuthority.DERIVED,
            domain="DECISION",
            tenant_scoped=True,
            freshness_required=True,
            description=(
                "Structured candidate decision produced by "
                "the decision layer."
            ),
        ),

        "scenario_baseline": EvidenceSourceSpec(
            name="scenario_baseline",
            kind=EvidenceKind.DERIVED,
            authority=EvidenceAuthority.DERIVED,
            domain="SCENARIO",
            tenant_scoped=True,
            freshness_required=True,
            description=(
                "Baseline state used for deterministic scenario analysis."
            ),
        ),

        "accounts_receivable": EvidenceSourceSpec(
            name="accounts_receivable",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="FINANCE",
            tenant_scoped=True,
            freshness_required=True,
            description=(
                "Accounts receivable balance/input."
            ),
        ),

        "accounts_payable": EvidenceSourceSpec(
            name="accounts_payable",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="FINANCE",
            tenant_scoped=True,
            freshness_required=True,
            description=(
                "Accounts payable balance/input."
            ),
        ),
    }

    @classmethod
    def get(
        cls,
        source: str,
    ) -> EvidenceSourceSpec:
        key = source.strip().lower()

        if key not in cls.SOURCES:
            raise KeyError(
                f"Unknown AURIX evidence source: {source}"
            )

        return cls.SOURCES[key]

    @classmethod
    def has(
        cls,
        source: str,
    ) -> bool:
        return source.strip().lower() in cls.SOURCES

    @classmethod
    def fabric_sources(
        cls,
    ) -> List[str]:
        return [
            spec.name
            for spec in cls.SOURCES.values()
            if spec.kind == EvidenceKind.FABRIC
        ]

    @classmethod
    def derived_sources(
        cls,
    ) -> List[str]:
        return [
            spec.name
            for spec in cls.SOURCES.values()
            if spec.kind == EvidenceKind.DERIVED
        ]

    @classmethod
    def unimplemented_sources(
        cls,
    ) -> List[str]:
        return [
            spec.name
            for spec in cls.SOURCES.values()
            if spec.kind == EvidenceKind.UNIMPLEMENTED
        ]

    @classmethod
    def all(
        cls,
    ) -> List[EvidenceSourceSpec]:
        return list(cls.SOURCES.values())

    @classmethod
    def validate_source_list(
        cls,
        sources: List[str],
    ) -> List[str]:
        return [
            source
            for source in sources
            if not cls.has(source)
        ]


__all__ = [
    "EvidenceKind",
    "EvidenceAuthority",
    "EvidenceSourceSpec",
    "EvidenceRegistry",
]
