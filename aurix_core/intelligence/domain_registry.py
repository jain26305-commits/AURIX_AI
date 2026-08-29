"""
AURIX Master Intelligence Domain Registry.

Single authoritative mapping between:
    semantic domain
    canonical business decision
    evidence contract
    expert engine
    allowed reasoning
    answer mode

This module must not contain domain mathematics.
Existing domain engines remain authoritative.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class DecisionSpec:
    name: str
    domain: str

    intents: Tuple[str, ...]

    required_evidence: Tuple[str, ...] = ()
    optional_evidence: Tuple[str, ...] = ()

    supports_answer: bool = True
    supports_recommendation: bool = False
    supports_causality: bool = False
    supports_prediction: bool = False
    supports_comparison: bool = False
    supports_simulation: bool = False

    engine: str | None = None

    answer_style: str = "BUSINESS_ASSESSMENT"

    description: str = ""


class DomainRegistry:

    INVENTORY_STATUS = DecisionSpec(
        name="INVENTORY_STATUS",
        domain="INVENTORY",
        intents=("READ", "DIAGNOSE", "SUMMARIZE"),
        required_evidence=("inventory_position",),
        optional_evidence=(
            "product",
            "inventory_transactions",
            "orders",
        ),
        supports_answer=True,
        supports_recommendation=False,
        supports_causality=True,
        engine="DeterministicReasoningEngine._reason_inventory",
        answer_style="INVENTORY_ASSESSMENT",
        description="Current inventory position and protection state.",
    )

    STOCKOUT_FORECAST = DecisionSpec(
        name="STOCKOUT_FORECAST",
        domain="INVENTORY",
        intents=("READ", "DIAGNOSE"),
        required_evidence=(
            "inventory_position",
            "forecast",
        ),
        optional_evidence=(
            "orders",
            "order_lines",
            "inventory_transactions",
        ),
        supports_prediction=True,
        supports_causality=False,
        engine="Forecasting",
        answer_style="FORECAST_ASSESSMENT",
        description="Projected depletion or stockout assessment.",
    )

    REPLENISHMENT_ADEQUACY = DecisionSpec(
        name="REPLENISHMENT_ADEQUACY",
        domain="INVENTORY",
        intents=("READ", "DIAGNOSE", "RECOMMEND"),
        required_evidence=(
            "inventory_position",
            "replenishment_policy",
        ),
        optional_evidence=(
            "forecast",
            "orders",
            "order_lines",
            "supplier_performance",
        ),
        supports_recommendation=True,
        supports_causality=True,
        engine="InventoryPolicyEngine",
        answer_style="REPLENISHMENT_ASSESSMENT",
        description="Whether replenishment settings adequately protect demand.",
    )

    SUPPLIER_STATUS = DecisionSpec(
        name="SUPPLIER_STATUS",
        domain="SUPPLY",
        intents=("READ", "SUMMARIZE"),
        required_evidence=("supplier_performance",),
        optional_evidence=(
            "suppliers",
            "purchase_orders",
            "shipments",
        ),
        engine="SupplierPerformance",
        answer_style="SUPPLIER_ASSESSMENT",
        description="Supplier performance and reliability.",
    )

    SUPPLIER_COMPARISON = DecisionSpec(
        name="SUPPLIER_COMPARISON",
        domain="SUPPLY",
        intents=("COMPARE", "RANK"),
        required_evidence=(
            "supplier_performance",
            "suppliers",
        ),
        supports_comparison=True,
        engine="SupplierPerformance",
        answer_style="COMPARISON",
        description="Deterministic supplier comparison.",
    )

    SUPPLIER_CAUSALITY = DecisionSpec(
        name="SUPPLIER_CAUSALITY",
        domain="SUPPLY",
        intents=("DIAGNOSE",),
        required_evidence=(
            "supplier_performance",
            "purchase_orders",
            "shipment_evaluation",
        ),
        supports_causality=True,
        engine="DeterministicCausalEngine",
        answer_style="CAUSAL_ASSESSMENT",
        description="Whether supplier behavior can be established as a cause.",
    )

    SHIPMENT_ETA = DecisionSpec(
        name="SHIPMENT_ETA",
        domain="LOGISTICS",
        intents=("READ", "SUMMARIZE"),
        required_evidence=(
            "shipments",
        ),
        optional_evidence=(
            "shipment_evaluation",
        ),
        engine="DeterministicETAEngine",
        answer_style="SHIPMENT_ASSESSMENT",
        description="Authoritative shipment ETA.",
    )

    SHIPMENT_DELAY = DecisionSpec(
        name="SHIPMENT_DELAY",
        domain="LOGISTICS",
        intents=("READ", "DIAGNOSE"),
        required_evidence=(
            "shipments",
        ),
        optional_evidence=(
            "shipment_evaluation",
        ),
        supports_causality=True,
        engine="DeterministicETAEngine",
        answer_style="SHIPMENT_DELAY",
        description="Shipment lateness and delivery exception.",
    )

    WORKING_CAPITAL = DecisionSpec(
        name="WORKING_CAPITAL",
        domain="ECONOMICS",
        intents=("READ", "DIAGNOSE", "SUMMARIZE"),
        required_evidence=("financial_baseline",),
        optional_evidence=(
            "inventory_position",
            "product",
        ),
        engine="WorkingCapitalEngine",
        answer_style="FINANCIAL_ASSESSMENT",
        description="Working-capital exposure and its financial drivers.",
    )

    OPERATING_CASH = DecisionSpec(
        name="OPERATING_CASH",
        domain="ECONOMICS",
        intents=("READ", "ANALYZE", "SUMMARIZE"),
        required_evidence=(
            "financial_baseline",
        ),
        optional_evidence=(
            "accounts_receivable",
            "accounts_payable",
        ),
        engine="CashIntelligenceEngine",
        answer_style="FINANCIAL_ASSESSMENT",
        description="Projected operating cash position.",
    )

    MARGIN_ANALYSIS = DecisionSpec(
        name="MARGIN_ANALYSIS",
        domain="ECONOMICS",
        intents=("READ", "ANALYZE", "COMPARE", "SUMMARIZE"),
        required_evidence=(
            "financial_baseline",
        ),
        optional_evidence=(
            "product",
            "orders",
        ),
        supports_comparison=True,
        engine="MarginEngine",
        answer_style="FINANCIAL_ASSESSMENT",
        description="Gross margin and profitability assessment.",
    )

    CAPACITY_STATUS = DecisionSpec(
        name="CAPACITY_STATUS",
        domain="MANUFACTURING",
        intents=("READ", "SUMMARIZE", "DIAGNOSE"),
        required_evidence=(
            "work_centers",
            "work_orders",
        ),
        optional_evidence=(
            "inventory_position",
            "orders",
            "capacity_checks",
        ),
        engine="CapacityEngine",
        answer_style="MANUFACTURING_ASSESSMENT",
        description="Manufacturing capacity and utilization.",
    )

    OEE_STATUS = DecisionSpec(
        name="OEE_STATUS",
        domain="MANUFACTURING",
        intents=("READ", "SUMMARIZE", "DIAGNOSE"),
        required_evidence=(
            "oee_metrics",
        ),
        optional_evidence=(
            "production_events",
            "work_centers",
        ),
        engine="OEEEngine",
        answer_style="MANUFACTURING_ASSESSMENT",
        description="Availability, performance, quality and OEE.",
    )

    QUALITY_STATUS = DecisionSpec(
        name="QUALITY_STATUS",
        domain="MANUFACTURING",
        intents=("READ", "SUMMARIZE", "DIAGNOSE"),
        required_evidence=(
            "production_events",
        ),
        optional_evidence=(
            "quality_events",
        ),
        engine="QualityEngine",
        answer_style="QUALITY_ASSESSMENT",
        description="Production yield, scrap and quality performance.",
    )

    MRP_PLAN = DecisionSpec(
        name="MRP_PLAN",
        domain="MANUFACTURING",
        intents=("READ", "ANALYZE", "RECOMMEND"),
        required_evidence=(
            "demand_schedule",
            "bom_relationships",
            "inventory_position",
        ),
        optional_evidence=(
            "purchase_orders",
            "work_orders",
            "product",
        ),
        supports_recommendation=True,
        engine="MRPEngine",
        answer_style="MRP_ASSESSMENT",
        description="Gross-to-net MRP planning and material requirements.",
    )

    BOTTLENECK_DIAGNOSIS = DecisionSpec(
        name="BOTTLENECK_DIAGNOSIS",
        domain="MANUFACTURING",
        intents=("DIAGNOSE",),
        required_evidence=(
            "capacity_checks",
            "work_centers",
        ),
        supports_causality=True,
        engine="CapacityEngine",
        answer_style="CAUSAL_ASSESSMENT",
        description="Manufacturing bottleneck identification.",
    )

    EXECUTIVE_RISK_SUMMARY = DecisionSpec(
        name="EXECUTIVE_RISK_SUMMARY",
        domain="RISK",
        intents=("SUMMARIZE", "READ"),
        required_evidence=("intelligence_snapshot",),
        supports_causality=True,
        engine="RiskEngine",
        answer_style="EXECUTIVE_RISK",
        description="Enterprise-level risk posture and priorities.",
    )

    PROCESS_BOTTLENECK = DecisionSpec(
        name="PROCESS_BOTTLENECK",
        domain="PROCESS",
        intents=("READ", "DIAGNOSE", "SUMMARIZE"),
        required_evidence=(
            "process_events",
        ),
        optional_evidence=(
            "process_metrics",
        ),
        supports_causality=True,
        engine="BottleneckEngine",
        answer_style="PROCESS_ASSESSMENT",
        description="Process bottlenecks and operational impact.",
    )

    SCENARIO_RESULT = DecisionSpec(
        name="SCENARIO_RESULT",
        domain="SCENARIO",
        intents=("SIMULATE", "COMPARE", "SUMMARIZE"),
        required_evidence=("scenario_baseline",),
        supports_prediction=True,
        supports_comparison=True,
        supports_simulation=True,
        engine="DeterministicScenarioEngine",
        answer_style="SCENARIO_ASSESSMENT",
        description="What-if and scenario analysis.",
    )

    DECISION_READINESS = DecisionSpec(
        name="DECISION_READINESS",
        domain="DECISION",
        intents=("READ", "DIAGNOSE", "RECOMMEND"),
        required_evidence=("decision_candidate",),
        supports_recommendation=True,
        engine="DecisionReadinessEngine",
        answer_style="DECISION_ASSESSMENT",
        description="Whether a decision is ready for controlled execution.",
    )

    DEFINITIONS: Dict[str, DecisionSpec] = {
        spec.name: spec
        for spec in (
            INVENTORY_STATUS,
            STOCKOUT_FORECAST,
            REPLENISHMENT_ADEQUACY,
            SUPPLIER_STATUS,
            SUPPLIER_COMPARISON,
            SUPPLIER_CAUSALITY,
            SHIPMENT_ETA,
            SHIPMENT_DELAY,
            WORKING_CAPITAL,
            OPERATING_CASH,
            MARGIN_ANALYSIS,
            CAPACITY_STATUS,
            OEE_STATUS,
            QUALITY_STATUS,
            MRP_PLAN,
            BOTTLENECK_DIAGNOSIS,
            EXECUTIVE_RISK_SUMMARY,
            PROCESS_BOTTLENECK,
            SCENARIO_RESULT,
            DECISION_READINESS,
        )
    }

    @classmethod
    def get(cls, decision: str) -> DecisionSpec:
        key = decision.strip().upper()

        if key not in cls.DEFINITIONS:
            raise KeyError(
                f"Unknown AURIX business decision: {decision}"
            )

        return cls.DEFINITIONS[key]

    @classmethod
    def all(cls) -> List[DecisionSpec]:
        return list(cls.DEFINITIONS.values())