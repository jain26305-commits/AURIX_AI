
"""
AURIX Expert Engine Registry.

This registry does not implement business calculations.
It maps canonical business decisions to existing authoritative
expert engines already present in the AURIX codebase.

The intelligence layer owns:
    - semantic interpretation
    - decision resolution
    - evidence gating
    - expert-engine selection
    - claim normalization
    - safety validation

Existing expert engines remain the source of business calculations.
"""

from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ExpertBinding:
    decision: str
    domain: str
    module_path: str
    class_name: str
    method_name: str

    description: str = ""

    @property
    def import_path(self) -> str:
        return (
            f"{self.module_path}:"
            f"{self.class_name}."
            f"{self.method_name}"
        )


class ExpertRegistry:
    """
    Single mapping between canonical business decisions and
    existing authoritative expert engines.
    """

    BINDINGS: Dict[str, ExpertBinding] = {

        # =========================================================
        # FINANCE / ECONOMICS
        # =========================================================

        "WORKING_CAPITAL": ExpertBinding(
            decision="WORKING_CAPITAL",
            domain="ECONOMICS",
            module_path=(
                "aurix_core.finance.working_capital_engine"
            ),
            class_name="WorkingCapitalEngine",
            method_name="calculate_working_capital",
            description=(
                "Calculates operating working capital from "
                "inventory, receivables and payables."
            ),
        ),

        "OPERATING_CASH": ExpertBinding(
            decision="OPERATING_CASH",
            domain="ECONOMICS",
            module_path=(
                "aurix_core.finance.cash_intelligence"
            ),
            class_name="CashIntelligenceEngine",
            method_name="project_operating_cash",
            description=(
                "Projects short-term operating cash position."
            ),
        ),

        "MARGIN_ANALYSIS": ExpertBinding(
            decision="MARGIN_ANALYSIS",
            domain="ECONOMICS",
            module_path=(
                "aurix_core.finance.margin_engine"
            ),
            class_name="MarginEngine",
            method_name="calculate_margin",
            description=(
                "Calculates gross margin from revenue, COGS "
                "and variable costs."
            ),
        ),

        # =========================================================
        # FORECASTING
        # =========================================================

        "FORECAST_ELIGIBILITY": ExpertBinding(
            decision="FORECAST_ELIGIBILITY",
            domain="FORECASTING",
            module_path=(
                "aurix_core.forecasting.gate"
            ),
            class_name="ModelEligibilityGate",
            method_name="evaluate_eligibility",
            description=(
                "Determines which forecasting approaches are "
                "eligible for a given demand series."
            ),
        ),

        "FORECAST_ACCURACY": ExpertBinding(
            decision="FORECAST_ACCURACY",
            domain="FORECASTING",
            module_path=(
                "aurix_core.forecasting.metrics"
            ),
            class_name="MetricsEngine",
            method_name="evaluate",
            description=(
                "Evaluates forecast accuracy metrics."
            ),
        ),

        # =========================================================
        # MANUFACTURING
        # =========================================================

        "CAPACITY_STATUS": ExpertBinding(
            decision="CAPACITY_STATUS",
            domain="MANUFACTURING",
            module_path=(
                "aurix_core.manufacturing.capacity_engine"
            ),
            class_name="CapacityEngine",
            method_name="evaluate_capacity",
            description=(
                "Evaluates work-center load against capacity."
            ),
        ),

        "OEE_STATUS": ExpertBinding(
            decision="OEE_STATUS",
            domain="MANUFACTURING",
            module_path=(
                "aurix_core.manufacturing.oee_engine"
            ),
            class_name="OEEEngine",
            method_name="calculate_oee",
            description=(
                "Calculates availability, performance, quality "
                "and OEE."
            ),
        ),

        "QUALITY_STATUS": ExpertBinding(
            decision="QUALITY_STATUS",
            domain="MANUFACTURING",
            module_path=(
                "aurix_core.manufacturing.quality_engine"
            ),
            class_name="QualityEngine",
            method_name="evaluate_quality",
            description=(
                "Evaluates production yield and quality."
            ),
        ),

        "MRP_PLAN": ExpertBinding(
            decision="MRP_PLAN",
            domain="MANUFACTURING",
            module_path=(
                "aurix_core.manufacturing.mrp_engine"
            ),
            class_name="MRPEngine",
            method_name="calculate_mrp",
            description=(
                "Executes gross-to-net MRP planning."
            ),
        ),

        # =========================================================
        # LOGISTICS
        # =========================================================

        "SHIPMENT_ETA": ExpertBinding(
            decision="SHIPMENT_ETA",
            domain="LOGISTICS",
            module_path=(
                "aurix_core.logistics.eta_engine"
            ),
            class_name="DeterministicETAEngine",
            method_name="calculate_eta",
            description=(
                "Calculates shipment ETA with provenance."
            ),
        ),

        # =========================================================
        # PROCESS
        # =========================================================

        "PROCESS_BOTTLENECK": ExpertBinding(
            decision="PROCESS_BOTTLENECK",
            domain="PROCESS",
            module_path=(
                "aurix_core.process.bottleneck_engine"
            ),
            class_name="BottleneckEngine",
            method_name="detect_bottlenecks",
            description=(
                "Detects process bottlenecks, queue depth, "
                "waiting duration and SLA breaches."
            ),
        ),

        # =========================================================
        # RISK
        # =========================================================

        "EXECUTIVE_RISK_SUMMARY": ExpertBinding(
            decision="EXECUTIVE_RISK_SUMMARY",
            domain="RISK",
            module_path=(
                "aurix_core.risk.risk_engine"
            ),
            class_name="RiskEngine",
            method_name="evaluate_risks",
            description=(
                "Generates evidence-backed enterprise risk findings."
            ),
        ),

        # =========================================================
        # DECISIONS
        # =========================================================

        "DECISION_READINESS": ExpertBinding(
            decision="DECISION_READINESS",
            domain="DECISION",
            module_path=(
                "aurix_core.decisions.readiness_engine"
            ),
            class_name="DecisionReadinessEngine",
            method_name="evaluate_readiness",
            description=(
                "Evaluates whether enterprise decisions are "
                "ready for controlled execution."
            ),
        ),

        "DECISION_CONSTRAINTS": ExpertBinding(
            decision="DECISION_CONSTRAINTS",
            domain="DECISION",
            module_path=(
                "aurix_core.decisions.constraint_engine"
            ),
            class_name="ConstraintEngine",
            method_name="validate_candidate",
            description=(
                "Validates candidate actions against constraints."
            ),
        ),

        "EXPECTED_VALUE": ExpertBinding(
            decision="EXPECTED_VALUE",
            domain="DECISION",
            module_path=(
                "aurix_core.decisions.expected_value"
            ),
            class_name="ExpectedValueEngine",
            method_name="calculate_expected_value",
            description=(
                "Calculates deterministic expected value."
            ),
        ),

        "DECISION_RANKING": ExpertBinding(
            decision="DECISION_RANKING",
            domain="DECISION",
            module_path=(
                "aurix_core.decisions.ranking_engine"
            ),
            class_name="RankingEngine",
            method_name="rank_candidates",
            description=(
                "Ranks decision candidates by deterministic utility."
            ),
        ),

        # =========================================================
        # SCENARIOS
        # =========================================================

        "SCENARIO_RESULT": ExpertBinding(
            decision="SCENARIO_RESULT",
            domain="SCENARIO",
            module_path=(
                "aurix_core.scenarios.scenario_engine"
            ),
            class_name="DeterministicScenarioEngine",
            method_name="execute_scenario",
            description=(
                "Executes deterministic scenario perturbations."
            ),
        ),

        "MONTE_CARLO_RESULT": ExpertBinding(
            decision="MONTE_CARLO_RESULT",
            domain="SCENARIO",
            module_path=(
                "aurix_core.scenarios.monte_carlo"
            ),
            class_name="MonteCarloEngine",
            method_name="simulate_distributions",
            description=(
                "Generates deterministic simulation percentiles."
            ),
        ),

        "EXECUTIVE_BRIEF": ExpertBinding(
            decision="EXECUTIVE_BRIEF",
            domain="OVERVIEW",
            module_path=(
                "aurix_core.scenarios.executive_engine"
            ),
            class_name="ExecutiveIntelligenceEngine",
            method_name="generate_executive_brief",
            description=(
                "Generates the grounded executive eight-question brief."
            ),
        ),
    
    }

    @classmethod
    def get(
        cls,
        decision: str,
    ) -> ExpertBinding:
        key = decision.strip().upper()

        if key not in cls.BINDINGS:
            raise KeyError(
                f"No expert binding registered for decision: {key}"
            )

        return cls.BINDINGS[key]

    @classmethod
    def all(cls) -> list[ExpertBinding]:
        return list(cls.BINDINGS.values())

    @classmethod
    def load_class(
        cls,
        binding: ExpertBinding,
    ) -> type:
        module = importlib.import_module(
            binding.module_path
        )
        return getattr(
            module,
            binding.class_name,
        )

    @classmethod
    def load_method(
        cls,
        binding: ExpertBinding,
    ) -> Any:
        engine_class = cls.load_class(
            binding
        )

        method = getattr(
            engine_class,
            binding.method_name,
        )

        if not callable(method):
            raise TypeError(
                f"Registered expert method is not callable: "
                f"{binding.import_path}"
            )

        return method

    @classmethod
    def signature(
        cls,
        decision: str,
    ) -> inspect.Signature:
        binding = cls.get(decision)
        return inspect.signature(
            cls.load_method(binding)
        )

    @classmethod
    def validate_all(
        cls,
    ) -> list[str]:
        errors: list[str] = []

        for binding in cls.all():
            try:
                method = cls.load_method(binding)

                if not callable(method):
                    errors.append(
                        f"{binding.import_path}: not callable"
                    )

            except Exception as exc:
                errors.append(
                    f"{binding.import_path}: "
                    f"{type(exc).__name__}: {exc}"
                )

        return errors


__all__ = [
    "ExpertBinding",
    "ExpertRegistry",
]
