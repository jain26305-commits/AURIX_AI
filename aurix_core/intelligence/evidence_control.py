
"""
AURIX Evidence Control Plane.

Single control module for:

    - evidence source registry
    - canonical field mappings
    - evidence availability
    - expert input contracts
    - fail-closed expert input preparation

This module does not perform business calculations.
Existing expert engines remain authoritative.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Tuple
from aurix_core.intelligence.expert_contracts import (
    ExpertContract,
    ExpertContractRegistry,
    ExpertField,
)



# ============================================================
# EVIDENCE SOURCE CONTRACTS
# ============================================================


class EvidenceKind(str, Enum):
    FABRIC = "FABRIC"
    DERIVED = "DERIVED"
    UNIMPLEMENTED = "UNIMPLEMENTED"


class EvidenceAuthority(str, Enum):
    AUTHORITATIVE = "AUTHORITATIVE"
    SUPPORTING = "SUPPORTING"
    DERIVED = "DERIVED"


@dataclass(frozen=True)
class EvidenceFieldSpec:
    source: str
    field: str
    canonical_name: str

    aliases: Tuple[str, ...] = ()

    required_for: Tuple[str, ...] = ()

    collection: bool = False


@dataclass(frozen=True)
class EvidenceSourceSpec:
    name: str
    kind: EvidenceKind
    authority: EvidenceAuthority
    domain: str

    fields: Tuple[str, ...] = ()

    tenant_scoped: bool = True
    freshness_required: bool = False

    handler_name: Optional[str] = None

    description: str = ""


# ============================================================
# EXPERT CONTRACTS
# ============================================================


@dataclass(frozen=True)
class ExpertPreparation:
    """
    Fail-closed expert input preparation result.
    """

    decision: str
    ready: bool = False

    inputs: Dict[str, Any] = field(
        default_factory=dict
    )

    missing_sources: List[str] = field(
        default_factory=list
    )

    missing_fields: List[str] = field(
        default_factory=list
    )

    unavailable_sources: List[str] = field(
        default_factory=list
    )

    warnings: List[str] = field(
        default_factory=list
    )

    provenance: Dict[str, Any] = field(
        default_factory=dict
    )


# ============================================================
# SOURCE REGISTRY
# ============================================================


class EvidenceRegistry:

    SOURCES: Dict[str, EvidenceSourceSpec] = {

        "product": EvidenceSourceSpec(
            name="product",
            kind=EvidenceKind.FABRIC,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="MASTER_DATA",
            fields=(
                "id",
                "sku_code",
                "name",
                "category",
                "unit_cost",
                "created_at",
            ),
            freshness_required=True,
            handler_name="EvidenceFabric.product",
        ),

        "inventory_position": EvidenceSourceSpec(
            name="inventory_position",
            kind=EvidenceKind.FABRIC,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="INVENTORY",
            fields=(
                "id",
                "sku_id",
                "location_id",
                "on_hand",
                "on_order",
                "safety_stock",
                "updated_at",
            ),
            freshness_required=True,
            handler_name="EvidenceFabric.inventory_position",
        ),

        "orders": EvidenceSourceSpec(
            name="orders",
            kind=EvidenceKind.FABRIC,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="DEMAND",
            fields=(
                "id",
                "order_number",
                "customer_id",
                "order_status",
                "channel",
                "total_amount",
                "discount_amount",
                "currency",
                "order_date",
                "promised_delivery_date",
                "delivered_date",
            ),
            freshness_required=True,
            handler_name="EvidenceFabric.orders",
        ),

        "order_lines": EvidenceSourceSpec(
            name="order_lines",
            kind=EvidenceKind.FABRIC,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="DEMAND",
            fields=(
                "id",
                "order_id",
                "sku_id",
                "quantity",
                "unit_price",
                "discount_amount",
                "sales_channel",
                "line_total",
            ),
            freshness_required=True,
            handler_name="EvidenceFabric.order_lines",
        ),

        "suppliers": EvidenceSourceSpec(
            name="suppliers",
            kind=EvidenceKind.FABRIC,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="SUPPLY",
            fields=(
                "id",
                "supplier_name",
                "country",
                "lead_time_days",
                "created_at",
            ),
            freshness_required=True,
            handler_name="EvidenceFabric.suppliers",
        ),

        "supplier_performance": EvidenceSourceSpec(
            name="supplier_performance",
            kind=EvidenceKind.FABRIC,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="SUPPLY",
            fields=(
                "supplier_id",
                "evaluated_order_count",
                "otd_rate",
                "in_full_rate",
                "otif_rate",
                "mean_lead_time_days",
                "lead_time_std_days",
                "risk_score",
                "risk_level",
                "risk_drivers",
                "value_state",
                "created_at",
            ),
            freshness_required=True,
            handler_name="EvidenceFabric.supplier_performance",
        ),

        "shipments": EvidenceSourceSpec(
            name="shipments",
            kind=EvidenceKind.FABRIC,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="LOGISTICS",
            fields=(
                "id",
                "shipment_number",
                "origin_location_id",
                "destination_location_id",
                "carrier",
                "status",
                "shipped_date",
                "estimated_arrival_date",
                "actual_arrival_date",
            ),
            freshness_required=True,
            handler_name="EvidenceFabric.shipments",
        ),

        "replenishment_policy": EvidenceSourceSpec(
            name="replenishment_policy",
            kind=EvidenceKind.FABRIC,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="INVENTORY",
            fields=(
                "id",
                "run_id",
                "sku_id",
                "location_id",
                "expected_daily_demand",
                "lead_time_days",
                "safety_stock",
                "reorder_point",
                "eoq",
                "reorder_triggered",
                "reorder_reason",
                "raw_order_quantity",
                "constrained_order_quantity",
                "risk_status",
                "holding_cost_exposure",
                "value_state",
                "created_at",
            ),
            freshness_required=True,
            handler_name="EvidenceFabric.replenishment_policy",
        ),

        "forecast": EvidenceSourceSpec(
            name="forecast",
            kind=EvidenceKind.FABRIC,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="FORECASTING",
            fields=(
                "forecast_run_id",
                "sku_id",
                "location_id",
                "target_date",
                "horizon_step",
                "point_forecast",
                "raw_model_forecast",
                "lower_bound",
                "upper_bound",
                "model_id",
                "value_state",
            ),
            freshness_required=True,
            handler_name="EvidenceFabric.forecast",
        ),

        "inventory_transactions": EvidenceSourceSpec(
            name="inventory_transactions",
            kind=EvidenceKind.FABRIC,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="INVENTORY",
            fields=(
                "id",
                "sku_id",
                "location_id",
                "transaction_type",
                "quantity",
                "reference_document",
                "transaction_date",
            ),
            freshness_required=True,
            handler_name="EvidenceFabric.inventory_transactions",
        ),

        # --------------------------------------------------------
        # Derived intelligence objects
        # --------------------------------------------------------

        "capacity_checks": EvidenceSourceSpec(
            name="capacity_checks",
            kind=EvidenceKind.DERIVED,
            authority=EvidenceAuthority.DERIVED,
            domain="MANUFACTURING",
            freshness_required=True,
        ),

        "oee_metrics": EvidenceSourceSpec(
            name="oee_metrics",
            kind=EvidenceKind.DERIVED,
            authority=EvidenceAuthority.DERIVED,
            domain="MANUFACTURING",
            freshness_required=True,
        ),

        "customers": EvidenceSourceSpec(
            name="customers",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="COMMERCIAL",
            freshness_required=True,
        ),

        "inventory_items": EvidenceSourceSpec(
            name="inventory_items",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="INVENTORY",
            freshness_required=True,
        ),

        "assurance_findings": EvidenceSourceSpec(
            name="assurance_findings",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="ASSURANCE",
            freshness_required=True,
        ),

        "executive_context": EvidenceSourceSpec(
            name="executive_context",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.DERIVED,
            domain="EXECUTIVE",
            freshness_required=True,
        ),

        "simulation_input": EvidenceSourceSpec(
            name="simulation_input",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.DERIVED,
            domain="SCENARIO",
            freshness_required=True,
        ),

        "process_type_context": EvidenceSourceSpec(
            name="process_type_context",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.DERIVED,
            domain="PROCESS",
            freshness_required=False,
        ),

        "process_bottlenecks": EvidenceSourceSpec(
            name="process_bottlenecks",
            kind=EvidenceKind.DERIVED,
            authority=EvidenceAuthority.DERIVED,
            domain="PROCESS",
            freshness_required=True,
        ),

        "external_signal_mappings": EvidenceSourceSpec(
            name="external_signal_mappings",
            kind=EvidenceKind.DERIVED,
            authority=EvidenceAuthority.DERIVED,
            domain="RISK",
            freshness_required=True,
        ),

        "scenario_definition": EvidenceSourceSpec(
            name="scenario_definition",
            kind=EvidenceKind.DERIVED,
            authority=EvidenceAuthority.DERIVED,
            domain="SCENARIO",
            freshness_required=True,
        ),

        "process_metrics": EvidenceSourceSpec(
            name="process_metrics",
            kind=EvidenceKind.DERIVED,
            authority=EvidenceAuthority.DERIVED,
            domain="PROCESS",
            freshness_required=True,
        ),

        "decision_candidate": EvidenceSourceSpec(
            name="decision_candidate",
            kind=EvidenceKind.DERIVED,
            authority=EvidenceAuthority.DERIVED,
            domain="DECISION",
            freshness_required=True,
        ),

        "scenario_baseline": EvidenceSourceSpec(
            name="scenario_baseline",
            kind=EvidenceKind.DERIVED,
            authority=EvidenceAuthority.DERIVED,
            domain="SCENARIO",
            freshness_required=True,
        ),

        # --------------------------------------------------------
        # Referenced by contracts but not currently retrievable
        # --------------------------------------------------------

        "shipment_evaluation": EvidenceSourceSpec(
            name="shipment_evaluation",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.SUPPORTING,
            domain="LOGISTICS",
            freshness_required=True,
        ),

        "carrier_performance": EvidenceSourceSpec(
            name="carrier_performance",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.SUPPORTING,
            domain="LOGISTICS",
            freshness_required=True,
        ),

        "lane_performance": EvidenceSourceSpec(
            name="lane_performance",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.SUPPORTING,
            domain="LOGISTICS",
            freshness_required=True,
        ),

        "purchase_orders": EvidenceSourceSpec(
            name="purchase_orders",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="PROCUREMENT",
            freshness_required=True,
        ),

        "financial_baseline": EvidenceSourceSpec(
            name="financial_baseline",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="ECONOMICS",
            freshness_required=True,
        ),

        "intelligence_snapshot": EvidenceSourceSpec(
            name="intelligence_snapshot",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.DERIVED,
            domain="EXECUTIVE",
            freshness_required=True,
        ),

        "work_centers": EvidenceSourceSpec(
            name="work_centers",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="MANUFACTURING",
            freshness_required=True,
        ),

        "work_orders": EvidenceSourceSpec(
            name="work_orders",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="MANUFACTURING",
            freshness_required=True,
        ),

        "production_events": EvidenceSourceSpec(
            name="production_events",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="MANUFACTURING",
            freshness_required=True,
        ),

        "quality_events": EvidenceSourceSpec(
            name="quality_events",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="MANUFACTURING",
            freshness_required=True,
        ),

        "demand_schedule": EvidenceSourceSpec(
            name="demand_schedule",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="PLANNING",
            freshness_required=True,
        ),

        "bom_relationships": EvidenceSourceSpec(
            name="bom_relationships",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="MANUFACTURING",
        ),

        "process_events": EvidenceSourceSpec(
            name="process_events",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="PROCESS",
            freshness_required=True,
        ),

        "accounts_receivable": EvidenceSourceSpec(
            name="accounts_receivable",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="FINANCE",
            freshness_required=True,
        ),

        "accounts_payable": EvidenceSourceSpec(
            name="accounts_payable",
            kind=EvidenceKind.UNIMPLEMENTED,
            authority=EvidenceAuthority.AUTHORITATIVE,
            domain="FINANCE",
            freshness_required=True,
        ),
    }

    @classmethod
    def get(cls, source: str) -> EvidenceSourceSpec:
        key = source.strip().lower()

        if key not in cls.SOURCES:
            raise KeyError(
                f"Unknown AURIX evidence source: {source}"
            )

        return cls.SOURCES[key]

    @classmethod
    def all(cls) -> List[EvidenceSourceSpec]:
        return list(cls.SOURCES.values())

    @classmethod
    def fabric_sources(cls) -> List[str]:
        return [
            item.name
            for item in cls.SOURCES.values()
            if item.kind == EvidenceKind.FABRIC
        ]

    @classmethod
    def derived_sources(cls) -> List[str]:
        return [
            item.name
            for item in cls.SOURCES.values()
            if item.kind == EvidenceKind.DERIVED
        ]

    @classmethod
    def unimplemented_sources(cls) -> List[str]:
        return [
            item.name
            for item in cls.SOURCES.values()
            if item.kind == EvidenceKind.UNIMPLEMENTED
        ]

    @classmethod
    def fields_for(cls, source: str) -> Tuple[str, ...]:
        return cls.get(source).fields


# ============================================================
# FIELD MAPPINGS
# ============================================================


FIELD_MAPPINGS: Tuple[EvidenceFieldSpec, ...] = (

    # Inventory
    EvidenceFieldSpec(
        source="inventory_position",
        field="on_hand",
        canonical_name="inventory.on_hand",
        required_for=(
            "INVENTORY_STATUS",
            "INVENTORY_PROTECTION",
            "STOCKOUT_FORECAST",
            "REPLENISHMENT_ADEQUACY",
        ),
    ),
    EvidenceFieldSpec(
        source="inventory_position",
        field="on_order",
        canonical_name="inventory.on_order",
        required_for=(
            "INBOUND_COVERAGE",
            "INVENTORY_STATUS",
        ),
    ),
    EvidenceFieldSpec(
        source="inventory_position",
        field="safety_stock",
        canonical_name="inventory.safety_stock",
        required_for=(
            "INVENTORY_STATUS",
            "INVENTORY_PROTECTION",
            "STOCKOUT_FORECAST",
            "REPLENISHMENT_ADEQUACY",
        ),
    ),
    EvidenceFieldSpec(
        source="inventory_position",
        field="sku_id",
        canonical_name="inventory.sku_id",
    ),
    EvidenceFieldSpec(
        source="inventory_position",
        field="location_id",
        canonical_name="inventory.location_id",
    ),
    EvidenceFieldSpec(
        source="inventory_position",
        field="updated_at",
        canonical_name="inventory.updated_at",
    ),

    # Product
    EvidenceFieldSpec(
        source="product",
        field="sku_code",
        canonical_name="product.sku_code",
    ),
    EvidenceFieldSpec(
        source="product",
        field="name",
        canonical_name="product.name",
    ),
    EvidenceFieldSpec(
        source="product",
        field="category",
        canonical_name="product.category",
    ),
    EvidenceFieldSpec(
        source="product",
        field="unit_cost",
        canonical_name="product.unit_cost",
    ),

    # Orders
    EvidenceFieldSpec(
        source="orders",
        field="id",
        canonical_name="order.id",
    ),
    EvidenceFieldSpec(
        source="orders",
        field="order_number",
        canonical_name="order.number",
    ),
    EvidenceFieldSpec(
        source="orders",
        field="customer_id",
        canonical_name="order.customer_id",
    ),
    EvidenceFieldSpec(
        source="orders",
        field="total_amount",
        canonical_name="order.total_amount",
    ),
    EvidenceFieldSpec(
        source="orders",
        field="discount_amount",
        canonical_name="order.discount_amount",
    ),
    EvidenceFieldSpec(
        source="orders",
        field="promised_delivery_date",
        canonical_name="order.promised_delivery_date",
    ),
    EvidenceFieldSpec(
        source="orders",
        field="delivered_date",
        canonical_name="order.delivered_date",
    ),

    # Order lines
    EvidenceFieldSpec(
        source="order_lines",
        field="sku_id",
        canonical_name="order_line.sku_id",
    ),
    EvidenceFieldSpec(
        source="order_lines",
        field="quantity",
        canonical_name="order_line.quantity",
    ),
    EvidenceFieldSpec(
        source="order_lines",
        field="unit_price",
        canonical_name="order_line.unit_price",
    ),
    EvidenceFieldSpec(
        source="order_lines",
        field="discount_amount",
        canonical_name="order_line.discount_amount",
    ),
    EvidenceFieldSpec(
        source="order_lines",
        field="line_total",
        canonical_name="order_line.line_total",
    ),

    # Suppliers
    EvidenceFieldSpec(
        source="suppliers",
        field="id",
        canonical_name="supplier.id",
    ),
    EvidenceFieldSpec(
        source="suppliers",
        field="supplier_name",
        canonical_name="supplier.name",
    ),
    EvidenceFieldSpec(
        source="suppliers",
        field="country",
        canonical_name="supplier.country",
    ),
    EvidenceFieldSpec(
        source="suppliers",
        field="lead_time_days",
        canonical_name="supplier.lead_time_days",
    ),

    # Supplier performance
    EvidenceFieldSpec(
        source="supplier_performance",
        field="otd_rate",
        canonical_name="supplier.otd_rate",
    ),
    EvidenceFieldSpec(
        source="supplier_performance",
        field="in_full_rate",
        canonical_name="supplier.in_full_rate",
    ),
    EvidenceFieldSpec(
        source="supplier_performance",
        field="otif_rate",
        canonical_name="supplier.otif_rate",
    ),
    EvidenceFieldSpec(
        source="supplier_performance",
        field="mean_lead_time_days",
        canonical_name="supplier.mean_lead_time_days",
    ),
    EvidenceFieldSpec(
        source="supplier_performance",
        field="lead_time_std_days",
        canonical_name="supplier.lead_time_std_days",
    ),
    EvidenceFieldSpec(
        source="supplier_performance",
        field="risk_score",
        canonical_name="supplier.risk_score",
    ),
    EvidenceFieldSpec(
        source="supplier_performance",
        field="risk_level",
        canonical_name="supplier.risk_level",
    ),
    EvidenceFieldSpec(
        source="supplier_performance",
        field="risk_drivers",
        canonical_name="supplier.risk_drivers",
    ),

    # Shipments
    EvidenceFieldSpec(
        source="shipments",
        field="shipment_number",
        canonical_name="shipment.number",
    ),
    EvidenceFieldSpec(
        source="shipments",
        field="origin_location_id",
        canonical_name="shipment.origin",
    ),
    EvidenceFieldSpec(
        source="shipments",
        field="destination_location_id",
        canonical_name="shipment.destination",
    ),
    EvidenceFieldSpec(
        source="shipments",
        field="carrier",
        canonical_name="shipment.carrier",
    ),
    EvidenceFieldSpec(
        source="shipments",
        field="status",
        canonical_name="shipment.status",
    ),
    EvidenceFieldSpec(
        source="shipments",
        field="shipped_date",
        canonical_name="shipment.shipped_date",
    ),
    EvidenceFieldSpec(
        source="shipments",
        field="estimated_arrival_date",
        canonical_name="shipment.estimated_arrival_date",
    ),
    EvidenceFieldSpec(
        source="shipments",
        field="actual_arrival_date",
        canonical_name="shipment.actual_arrival_date",
    ),

    # Replenishment
    EvidenceFieldSpec(
        source="replenishment_policy",
        field="expected_daily_demand",
        canonical_name="replenishment.expected_daily_demand",
    ),
    EvidenceFieldSpec(
        source="replenishment_policy",
        field="lead_time_days",
        canonical_name="replenishment.lead_time_days",
    ),
    EvidenceFieldSpec(
        source="replenishment_policy",
        field="safety_stock",
        canonical_name="replenishment.safety_stock",
    ),
    EvidenceFieldSpec(
        source="replenishment_policy",
        field="reorder_point",
        canonical_name="replenishment.reorder_point",
    ),
    EvidenceFieldSpec(
        source="replenishment_policy",
        field="eoq",
        canonical_name="replenishment.eoq",
    ),
    EvidenceFieldSpec(
        source="replenishment_policy",
        field="reorder_triggered",
        canonical_name="replenishment.reorder_triggered",
    ),
    EvidenceFieldSpec(
        source="replenishment_policy",
        field="reorder_reason",
        canonical_name="replenishment.reorder_reason",
    ),
    EvidenceFieldSpec(
        source="replenishment_policy",
        field="risk_status",
        canonical_name="replenishment.risk_status",
    ),
    EvidenceFieldSpec(
        source="replenishment_policy",
        field="holding_cost_exposure",
        canonical_name="replenishment.holding_cost_exposure",
    ),

    # Forecast
    EvidenceFieldSpec(
        source="forecast",
        field="sku_id",
        canonical_name="forecast.sku_id",
    ),
    EvidenceFieldSpec(
        source="forecast",
        field="location_id",
        canonical_name="forecast.location_id",
    ),
    EvidenceFieldSpec(
        source="forecast",
        field="target_date",
        canonical_name="forecast.target_date",
    ),
    EvidenceFieldSpec(
        source="forecast",
        field="horizon_step",
        canonical_name="forecast.horizon_step",
    ),
    EvidenceFieldSpec(
        source="forecast",
        field="point_forecast",
        canonical_name="forecast.point_forecast",
        required_for=("STOCKOUT_FORECAST",),
    ),
    EvidenceFieldSpec(
        source="forecast",
        field="lower_bound",
        canonical_name="forecast.lower_bound",
    ),
    EvidenceFieldSpec(
        source="forecast",
        field="upper_bound",
        canonical_name="forecast.upper_bound",
    ),
    EvidenceFieldSpec(
        source="forecast",
        field="model_id",
        canonical_name="forecast.model_id",
    ),

    # Inventory transactions
    EvidenceFieldSpec(
        source="inventory_transactions",
        field="sku_id",
        canonical_name="inventory_transaction.sku_id",
    ),
    EvidenceFieldSpec(
        source="inventory_transactions",
        field="location_id",
        canonical_name="inventory_transaction.location_id",
    ),
    EvidenceFieldSpec(
        source="inventory_transactions",
        field="transaction_type",
        canonical_name="inventory_transaction.type",
    ),
    EvidenceFieldSpec(
        source="inventory_transactions",
        field="quantity",
        canonical_name="inventory_transaction.quantity",
    ),
    EvidenceFieldSpec(
        source="inventory_transactions",
        field="transaction_date",
        canonical_name="inventory_transaction.date",
    ),
)


class EvidenceControl:

    @staticmethod
    def source_status(
        source: str,
    ) -> EvidenceKind:
        return EvidenceRegistry.get(source).kind

    @staticmethod
    def validate_sources(
        sources: Iterable[str],
    ) -> Dict[str, List[str]]:

        output = {
            "fabric": [],
            "derived": [],
            "unimplemented": [],
            "unknown": [],
        }

        for source in sources:
            try:
                kind = EvidenceRegistry.get(source).kind
            except KeyError:
                output["unknown"].append(source)
                continue

            if kind == EvidenceKind.FABRIC:
                output["fabric"].append(source)
            elif kind == EvidenceKind.DERIVED:
                output["derived"].append(source)
            elif kind == EvidenceKind.UNIMPLEMENTED:
                output["unimplemented"].append(source)

        return output

    @staticmethod
    def prepare_expert_inputs(
        *,
        decision: str,
        evidence: Dict[str, List[Dict[str, Any]]],
        tenant_id: Optional[str] = None,
    ) -> ExpertPreparation:

        decision_key = decision.strip().upper()

        # --------------------------------------------------------
        # Specialist-engine path.
        #
        # These decisions have an explicit ExpertContract and
        # therefore require field-level expert input preparation.
        # --------------------------------------------------------

        try:
            contract = ExpertContractRegistry.get(
                decision_key
            )
        except KeyError:

            # ----------------------------------------------------
            # Deterministic-reasoning path.
            #
            # Some canonical decisions are handled directly by
            # DeterministicReasoningEngine rather than a dedicated
            # specialist engine. Their evidence requirements come
            # from the canonical DomainRegistry.
            #
            # Do not invent expert fields for these decisions.
            # Simply validate that their required evidence is
            # genuinely available.
            # ----------------------------------------------------
            from aurix_core.intelligence.domain_registry import (
                DomainRegistry,
            )

            decision_spec = DomainRegistry.get(
                decision_key
            )

            missing_sources: List[str] = []
            unavailable_sources: List[str] = []

            for source in decision_spec.required_evidence:

                source_spec = EvidenceRegistry.get(
                    source
                )

                if (
                    source_spec.kind
                    == EvidenceKind.UNIMPLEMENTED
                ):
                    unavailable_sources.append(
                        source
                    )
                    continue

                if not evidence.get(source):
                    missing_sources.append(
                        source
                    )

            if unavailable_sources:
                return ExpertPreparation(
                    decision=decision_key,
                    ready=False,
                    inputs={},
                    missing_sources=missing_sources,
                    unavailable_sources=unavailable_sources,
                    provenance={
                        "tenant_id": tenant_id,
                        "path": "DETERMINISTIC_REASONING",
                        "reason": (
                            "required_evidence_unimplemented"
                        ),
                    },
                )

            if missing_sources:
                return ExpertPreparation(
                    decision=decision_key,
                    ready=False,
                    inputs={},
                    missing_sources=missing_sources,
                    provenance={
                        "tenant_id": tenant_id,
                        "path": "DETERMINISTIC_REASONING",
                        "reason": (
                            "required_evidence_missing"
                        ),
                    },
                )

            return ExpertPreparation(
                decision=decision_key,
                ready=True,
                inputs={
                    source: evidence[source]
                    for source in decision_spec.required_evidence
                },
                provenance={
                    "tenant_id": tenant_id,
                    "path": "DETERMINISTIC_REASONING",
                    "decision": decision_key,
                    "reason": (
                        "required_evidence_ready"
                    ),
                },
            )

        # --------------------------------------------------------
        # Specialist-engine field preparation.
        # --------------------------------------------------------

        missing_sources: List[str] = []
        unavailable_sources: List[str] = []
        missing_fields: List[str] = []

        for source in contract.required_sources:
            spec = EvidenceRegistry.get(source)

            if (
                spec.kind
                == EvidenceKind.UNIMPLEMENTED
            ):
                unavailable_sources.append(
                    source
                )
                continue

            if (
                spec.kind
                == EvidenceKind.DERIVED
                and source not in evidence
            ):
                missing_sources.append(
                    source
                )
                continue

            if (
                spec.kind
                == EvidenceKind.FABRIC
                and not evidence.get(source)
            ):
                missing_sources.append(
                    source
                )

        if unavailable_sources:
            return ExpertPreparation(
                decision=decision_key,
                ready=False,
                missing_sources=missing_sources,
                unavailable_sources=unavailable_sources,
                provenance={
                    "tenant_id": tenant_id,
                    "path": "SPECIALIST_ENGINE",
                    "reason": (
                        "required_evidence_unimplemented"
                    ),
                },
            )

        if missing_sources:
            return ExpertPreparation(
                decision=decision_key,
                ready=False,
                missing_sources=missing_sources,
                provenance={
                    "tenant_id": tenant_id,
                    "path": "SPECIALIST_ENGINE",
                    "reason": (
                        "required_evidence_missing"
                    ),
                },
            )

        inputs: Dict[str, Any] = {}

        for field_spec in contract.fields:

            source_records = evidence.get(
                field_spec.source,
                [],
            )

            if not source_records:

                if field_spec.required:
                    missing_fields.append(
                        field_spec.name
                    )

                continue

            if field_spec.collection:
                inputs[
                    field_spec.name
                ] = source_records
                continue

            record = source_records[0]

            # Some expert contracts expect the entire source record
            # as a structured object rather than one scalar field.
            #
            # Example:
            #     SHIPMENT_ETA -> shipment
            #     source       -> shipments
            #
            # The ETA engine expects:
            #     shipment: Dict[str, Any]
            #
            # Therefore the complete shipment record is the expert
            # input, not record["shipment"].
            if (
                field_spec.name == "shipment"
                and field_spec.source == "shipments"
            ):
                inputs[
                    field_spec.name
                ] = record
                continue

            value = None

            aliases = (
                field_spec.aliases
                or (field_spec.name,)
            )

            for alias in aliases:
                if alias in record:
                    value = record[alias]
                    break

            if (
                value is None
                and field_spec.required
            ):
                missing_fields.append(
                    field_spec.name
                )
                continue

            if value is not None:
                inputs[
                    field_spec.name
                ] = value

        if missing_fields:
            return ExpertPreparation(
                decision=decision_key,
                ready=False,
                inputs=inputs,
                missing_fields=missing_fields,
                provenance={
                    "tenant_id": tenant_id,
                    "path": "SPECIALIST_ENGINE",
                    "reason": (
                        "required_expert_fields_missing"
                    ),
                },
            )

        if tenant_id is not None:
            inputs["tenant_id"] = tenant_id

        return ExpertPreparation(
            decision=decision_key,
            ready=True,
            inputs=inputs,
            provenance={
                "tenant_id": tenant_id,
                "path": "SPECIALIST_ENGINE",
                "reason": "expert_inputs_ready",
                "decision": decision_key,
            },
        )


__all__ = [
    "EvidenceKind",
    "EvidenceAuthority",
    "EvidenceFieldSpec",
    "EvidenceSourceSpec",
    "EvidenceFieldSpec",
    "ExpertField",
    "ExpertContract",
    "ExpertPreparation",
    "EvidenceRegistry",
    "ExpertContractRegistry",
    "EvidenceControl",
    "FIELD_MAPPINGS",
]
