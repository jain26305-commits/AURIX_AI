"""
AURIX Expert Contract Layer.

Canonical source of specialist execution contracts.

This module defines: 
    - normalized expert-engine inputs
    - field-level requirements
    - execution modes
    - execution permission

Business mathematics remains in the registered domain engines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class ExpertField:
    name: str
    source: str
    aliases: Tuple[str, ...] = ()
    required: bool = True
    collection: bool = False


@dataclass(frozen=True)
class ExpertContract:
    decision: str
    execution_mode: str
    required_sources: Tuple[str, ...] = ()
    optional_sources: Tuple[str, ...] = ()
    fields: Tuple[ExpertField, ...] = ()
    output_description: str = ""
    execution_allowed: bool = True


class ExpertContractRegistry:

    CONTRACTS: Dict[str, ExpertContract] = {

        "WORKING_CAPITAL": ExpertContract(
            decision="WORKING_CAPITAL",
            execution_mode="CALCULATION",
            required_sources=("financial_baseline",),
            optional_sources=(
                "inventory_position",
                "product",
            ),
            fields=(
                ExpertField(
                    name="inventory_valuation",
                    source="financial_baseline",
                    required=True,
                ),
                ExpertField(
                    name="accounts_receivable",
                    source="financial_baseline",
                    required=True,
                ),
                ExpertField(
                    name="accounts_payable",
                    source="financial_baseline",
                    required=True,
                ),
                ExpertField(
                    name="annual_revenue",
                    source="financial_baseline",
                    required=True,
                ),
                ExpertField(
                    name="annual_cogs",
                    source="financial_baseline",
                    required=True,
                ),
            ),
        ),

        "DECISION_READINESS": ExpertContract(
            decision="DECISION_READINESS",
            execution_mode="DECISION_OBJECT",
            required_sources=(
                "decision_candidate",
            ),
            optional_sources=(
                "suppliers",
                "customers",
                "work_orders",
                "orders",
            ),
            fields=(
                ExpertField(
                    name="suppliers_count",
                    source="derived_decision_context",
                    required=True,
                ),
                ExpertField(
                    name="customers_count",
                    source="derived_decision_context",
                    required=True,
                ),
                ExpertField(
                    name="work_orders_count",
                    source="derived_decision_context",
                    required=True,
                ),
                ExpertField(
                    name="invoices_count",
                    source="derived_decision_context",
                    required=True,
                ),
            ),
            output_description=(
                "Readiness assessment for controlled decision execution."
            ),
        ),

        "DECISION_CONSTRAINTS": ExpertContract(
            decision="DECISION_CONSTRAINTS",
            execution_mode="DECISION_OBJECT",
            required_sources=(
                "decision_candidate",
            ),
            optional_sources=(),
            fields=(
                ExpertField(
                    name="candidate",
                    source="decision_candidate",
                    required=True,
                ),
            ),
            output_description=(
                "Constraint validation for a decision candidate."
            ),
        ),

        "EXPECTED_VALUE": ExpertContract(
            decision="EXPECTED_VALUE",
            execution_mode="DECISION_OBJECT",
            required_sources=(
                "decision_candidate",
            ),
            optional_sources=(),
            fields=(
                ExpertField(
                    name="benefit_usd",
                    source="decision_candidate",
                    aliases=(
                        "benefit_usd",
                        "gross_benefit_usd",
                    ),
                    required=True,
                ),
                ExpertField(
                    name="cost_usd",
                    source="decision_candidate",
                    aliases=(
                        "cost_usd",
                    ),
                    required=True,
                ),
                ExpertField(
                    name="risk_penalty_usd",
                    source="decision_candidate",
                    aliases=(
                        "risk_penalty_usd",
                        "risk_usd",
                    ),
                    required=True,
                ),
                ExpertField(
                    name="probability_of_success",
                    source="decision_candidate",
                    aliases=(
                        "probability_of_success",
                        "success_probability",
                    ),
                    required=False,
                ),
            ),
            output_description=(
                "Expected economic value of a decision candidate."
            ),
        ),

        "DECISION_RANKING": ExpertContract(
            decision="DECISION_RANKING",
            execution_mode="DECISION_OBJECT",
            required_sources=(
                "decision_candidate",
            ),
            optional_sources=(),
            fields=(
                ExpertField(
                    name="candidates",
                    source="decision_candidate",
                    collection=True,
                    required=True,
                ),
            ),
            output_description=(
                "Deterministic ranking of candidate decisions by utility."
            ),
        ),

        "PROCESS_BOTTLENECK": ExpertContract(
            decision="PROCESS_BOTTLENECK",
            execution_mode="MULTI_RECORD_ANALYSIS",
            required_sources=(
                "process_events",
                "process_type_context",
            ),
            optional_sources=(
                "process_metrics",
            ),
            fields=(
                ExpertField(
                    name="process_type",
                    source="process_type_context",
                    required=True,
                ),
                ExpertField(
                    name="events",
                    source="process_events",
                    collection=True,
                    required=True,
                ),
            ),
            output_description=(
                "Evidence-backed process bottleneck identification."
            ),
        ),

        "EXECUTIVE_RISK_SUMMARY": ExpertContract(
            decision="EXECUTIVE_RISK_SUMMARY",
            execution_mode="MULTI_DOMAIN_ANALYSIS",
            required_sources=(
                "suppliers",
                "customers",
                "inventory_items",
                "work_orders",
                "assurance_findings",
                "process_bottlenecks",
            ),
            optional_sources=(
                "external_signal_mappings",
            ),
            fields=(
                ExpertField(
                    name="suppliers",
                    source="suppliers",
                    collection=True,
                    required=True,
                ),
                ExpertField(
                    name="customers",
                    source="customers",
                    collection=True,
                    required=True,
                ),
                ExpertField(
                    name="inventory_items",
                    source="inventory_items",
                    collection=True,
                    required=True,
                ),
                ExpertField(
                    name="work_orders",
                    source="work_orders",
                    collection=True,
                    required=True,
                ),
                ExpertField(
                    name="assurance_findings",
                    source="assurance_findings",
                    collection=True,
                    required=True,
                ),
                ExpertField(
                    name="process_bottlenecks",
                    source="process_bottlenecks",
                    collection=True,
                    required=True,
                ),
                ExpertField(
                    name="external_signal_mappings",
                    source="external_signal_mappings",
                    collection=True,
                    required=False,
                ),
            ),
            output_description=(
                "Cross-domain enterprise risk findings."
            ),
        ),

        "SCENARIO_RESULT": ExpertContract(
            decision="SCENARIO_RESULT",
            execution_mode="SCENARIO_OBJECT",
            required_sources=(
                "scenario_definition",
                "scenario_baseline",
            ),
            optional_sources=(),
            fields=(
                ExpertField(
                    name="scenario",
                    source="scenario_definition",
                    required=True,
                ),
                ExpertField(
                    name="baseline_revenue",
                    source="scenario_baseline",
                    aliases=(
                        "baseline_revenue",
                    ),
                    required=True,
                ),
                ExpertField(
                    name="baseline_margin",
                    source="scenario_baseline",
                    aliases=(
                        "baseline_margin",
                    ),
                    required=True,
                ),
                ExpertField(
                    name="baseline_working_capital",
                    source="scenario_baseline",
                    aliases=(
                        "baseline_working_capital",
                    ),
                    required=True,
                ),
                ExpertField(
                    name="baseline_risk_exposure",
                    source="scenario_baseline",
                    aliases=(
                        "baseline_risk_exposure",
                    ),
                    required=True,
                ),
            ),
            output_description=(
                "Deterministic scenario consequences and trade-offs."
            ),
        ),

        "MONTE_CARLO_RESULT": ExpertContract(
            decision="MONTE_CARLO_RESULT",
            execution_mode="NUMERICAL_SIMULATION",
            required_sources=(
                "simulation_input",
            ),
            optional_sources=(),
            fields=(
                ExpertField(
                    name="mean_value",
                    source="simulation_input",
                    aliases=(
                        "mean_value",
                        "mean_usd",
                    ),
                    required=True,
                ),
                ExpertField(
                    name="variance_pct",
                    source="simulation_input",
                    aliases=(
                        "variance_pct",
                    ),
                    required=True,
                ),
                ExpertField(
                    name="iterations_count",
                    source="simulation_input",
                    aliases=(
                        "iterations_count",
                    ),
                    required=True,
                ),
            ),
            output_description=(
                "Deterministic approximation of simulation outcome percentiles."
            ),
        ),

        "EXECUTIVE_BRIEF": ExpertContract(
            decision="EXECUTIVE_BRIEF",
            execution_mode="EXECUTIVE_SYNTHESIS",
            required_sources=(
                "executive_context",
            ),
            optional_sources=(),
            fields=(
                ExpertField(
                    name="supplier_disruption_days",
                    source="executive_context",
                    aliases=(
                        "supplier_disruption_days",
                    ),
                    required=True,
                ),
                ExpertField(
                    name="expected_value_usd",
                    source="executive_context",
                    aliases=(
                        "expected_value_usd",
                    ),
                    required=True,
                ),
                ExpertField(
                    name="realized_savings_usd",
                    source="executive_context",
                    aliases=(
                        "realized_savings_usd",
                    ),
                    required=True,
                ),
            ),
            output_description=(
                "Executive eight-question synthesis."
            ),
            execution_allowed=False,
        ),

        "FORECAST_ELIGIBILITY": ExpertContract(
            decision="FORECAST_ELIGIBILITY",
            execution_mode="DERIVED_ANALYTICAL",
            required_sources=(
                "orders",
                "order_lines",
            ),
            optional_sources=(
                "forecast",
                "inventory_transactions",
            ),
            fields=(
                ExpertField(
                    name="candidates",
                    source="forecast",
                    aliases=(
                        "candidates",
                        "candidate_models",
                    ),
                    required=False,
                ),
                ExpertField(
                    name="series",
                    source="derived_demand_series",
                    required=True,
                ),
                ExpertField(
                    name="freq",
                    source="derived_forecast_metadata",
                    required=True,
                ),
                ExpertField(
                    name="missing_pct",
                    source="derived_forecast_metadata",
                    required=True,
                ),
                ExpertField(
                    name="demand_class",
                    source="derived_forecast_metadata",
                    required=True,
                ),
                ExpertField(
                    name="seasonal_detected",
                    source="derived_forecast_metadata",
                    required=True,
                ),
            ),
            output_description=(
                "Determines which forecasting models are "
                "eligible for the available demand history."
            ),
        ),

        "FORECAST_ACCURACY": ExpertContract(
            decision="FORECAST_ACCURACY",
            execution_mode="DERIVED_ANALYTICAL",
            required_sources=(
                "orders",
                "order_lines",
                "forecast",
            ),
            optional_sources=(
                "inventory_transactions",
            ),
            fields=(
                ExpertField(
                    name="actuals",
                    source="derived_actual_series",
                    required=True,
                ),
                ExpertField(
                    name="predictions",
                    source="derived_prediction_series",
                    required=True,
                ),
            ),
            output_description=(
                "Evaluates forecast accuracy using actual and "
                "predicted demand series."
            ),
        ),

        "OPERATING_CASH": ExpertContract(
            decision="OPERATING_CASH",
            execution_mode="CALCULATION",
            required_sources=(
                "financial_baseline",
            ),
            optional_sources=(
                "accounts_receivable",
                "accounts_payable",
            ),
            fields=(
                ExpertField(
                    name="current_cash_balance",
                    source="financial_baseline",
                    aliases=(
                        "current_cash_balance",
                        "cash_balance",
                        "cash",
                    ),
                    required=True,
                ),
                ExpertField(
                    name="expected_ar_inflows",
                    source="financial_baseline",
                    aliases=(
                        "expected_ar_inflows",
                        "ar_inflows",
                        "expected_accounts_receivable",
                    ),
                    required=True,
                ),
                ExpertField(
                    name="expected_ap_outflows",
                    source="financial_baseline",
                    aliases=(
                        "expected_ap_outflows",
                        "ap_outflows",
                        "expected_accounts_payable",
                    ),
                    required=True,
                ),
                ExpertField(
                    name="currency",
                    source="financial_baseline",
                    aliases=(
                        "currency",
                    ),
                    required=False,
                ),
            ),
            output_description=(
                "Projected short-term operating cash position."
            ),
        ),

        "MARGIN_ANALYSIS": ExpertContract(
            decision="MARGIN_ANALYSIS",
            execution_mode="CALCULATION",
            required_sources=(
                "financial_baseline",
            ),
            optional_sources=(
                "product",
                "orders",
            ),
            fields=(
                ExpertField(
                    name="net_revenue",
                    source="financial_baseline",
                    aliases=(
                        "net_revenue",
                        "revenue",
                        "annual_revenue",
                    ),
                    required=True,
                ),
                ExpertField(
                    name="cogs",
                    source="financial_baseline",
                    aliases=(
                        "cogs",
                        "cost_of_goods_sold",
                        "annual_cogs",
                    ),
                    required=True,
                ),
                ExpertField(
                    name="variable_costs",
                    source="financial_baseline",
                    aliases=(
                        "variable_costs",
                        "variable_cost",
                    ),
                    required=False,
                ),
            ),
            output_description=(
                "Gross margin and profitability assessment."
            ),
        ),

        "SHIPMENT_ETA": ExpertContract(
            decision="SHIPMENT_ETA",
            execution_mode="ANALYTICAL",
            required_sources=("shipments",),
            optional_sources=("shipment_evaluation",),
            fields=(
                ExpertField(
                    name="shipment",
                    source="shipments",
                    collection=False,
                ),
                ExpertField(
                    name="carrier_performance",
                    source="shipment_evaluation",
                    required=False,
                ),
                ExpertField(
                    name="lane_performance",
                    source="shipment_evaluation",
                    required=False,
                ),
            ),
        ),

        "CAPACITY_STATUS": ExpertContract(
            decision="CAPACITY_STATUS",
            execution_mode="ANALYTICAL",
            required_sources=(
                "work_centers",
                "work_orders",
            ),
            optional_sources=(
                "inventory_position",
                "orders",
                "capacity_checks",
            ),
            fields=(
                ExpertField(
                    name="work_centers",
                    source="work_centers",
                    collection=True,
                ),
                ExpertField(
                    name="work_orders",
                    source="work_orders",
                    collection=True,
                ),
            ),
        ),

        "OEE_STATUS": ExpertContract(
            decision="OEE_STATUS",
            execution_mode="CALCULATION",
            required_sources=("oee_metrics",),
            optional_sources=(
                "production_events",
                "work_centers",
            ),
            fields=(
                ExpertField(
                    name="work_center_id",
                    source="oee_metrics",
                ),
                ExpertField(
                    name="period_key",
                    source="oee_metrics",
                ),
                ExpertField(
                    name="planned_production_minutes",
                    source="oee_metrics",
                ),
                ExpertField(
                    name="actual_run_time_minutes",
                    source="oee_metrics",
                ),
                ExpertField(
                    name="theoretical_output_units",
                    source="oee_metrics",
                ),
                ExpertField(
                    name="actual_output_units",
                    source="oee_metrics",
                ),
                ExpertField(
                    name="good_units",
                    source="oee_metrics",
                ),
                ExpertField(
                    name="scrap_units",
                    source="oee_metrics",
                    required=False,
                ),
            ),
        ),

        "QUALITY_STATUS": ExpertContract(
            decision="QUALITY_STATUS",
            execution_mode="ANALYTICAL",
            required_sources=("production_events",),
            optional_sources=("quality_events",),
            fields=(
                ExpertField(
                    name="production_events",
                    source="production_events",
                    collection=True,
                ),
            ),
        ),

        "MRP_PLAN": ExpertContract(
            decision="MRP_PLAN",
            execution_mode="ANALYTICAL",
            required_sources=(
                "demand_schedule",
                "bom_relationships",
                "inventory_position",
            ),
            optional_sources=(
                "purchase_orders",
                "work_orders",
                "product",
            ),
            fields=(
                ExpertField(
                    name="demand_schedule",
                    source="demand_schedule",
                    collection=True,
                ),
                ExpertField(
                    name="bom_relationships",
                    source="bom_relationships",
                    collection=True,
                ),
                ExpertField(
                    name="inventory_positions",
                    source="inventory_position",
                    collection=True,
                ),
                ExpertField(
                    name="open_purchase_orders",
                    source="purchase_orders",
                    collection=True,
                    required=False,
                ),
                ExpertField(
                    name="open_work_orders",
                    source="work_orders",
                    collection=True,
                    required=False,
                ),
                ExpertField(
                    name="products_lookup",
                    source="product",
                    required=False,
                ),
            ),
        ),
    }

    @classmethod
    def get(
        cls,
        decision: str,
    ) -> ExpertContract:
        key = decision.strip().upper()

        if key not in cls.CONTRACTS:
            raise KeyError(
                f"Unknown expert contract: {decision}"
            )

        return cls.CONTRACTS[key]

    @classmethod
    def all(cls) -> List[ExpertContract]:
        return list(cls.CONTRACTS.values())


# ============================================================
# CONTROL-PLANE HELPERS
# ============================================================




__all__ = [
    "ExpertField",
    "ExpertContract",
    "ExpertContractRegistry",
]
