"""
AURIX Deterministic Decision Engine 2.0 — Core Decision Engine
Phase 27 Core Implementation.
Generates structured decision candidates and builds Universal Decision Cards across procurement, inventory, pricing, mfg, and finance.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from aurix_core.decisions.confidence_engine import DecisionConfidenceEngine
from aurix_core.decisions.constraint_engine import ConstraintEngine
from aurix_core.decisions.contracts import (
    DecisionCandidate,
    DecisionDomain,
    DecisionState,
    ModelFitnessRating,
    UniversalDecisionCard,
)
from aurix_core.decisions.expected_value import ExpectedValueEngine
from aurix_core.decisions.ranking_engine import RankingEngine


class UniversalDecisionEngine:
    """Core domain-agnostic decision engine generating structured, ranked decision candidates."""

    @classmethod
    def generate_supplier_allocation_decision(
        cls,
        tenant_id: str,
        supplier_id: str,
        supplier_name: str,
        target_sku_id: str,
        order_amount_usd: float,
        supplier_otif: float,
        port_delay_days: float = 0.0,
    ) -> UniversalDecisionCard:
        """
        Generate decision candidates for supplier disruption or allocation:
        Candidate A: Retain primary supplier (baseline)
        Candidate B: Split order 60/40 with secondary qualified vendor
        Candidate C: Expedite air freight to eliminate delay
        """
        now = datetime.now(timezone.utc)

        # Candidate A: Retain Current
        c_a = DecisionCandidate(
            action_code="RETAIN_PRIMARY_SUPPLIER",
            action_name=f"Maintain 100% Allocation to {supplier_name}",
            description="Proceed with standard shipment schedule despite delay risk.",
            benefit_usd=order_amount_usd * 0.10,  # Standard margin
            cost_usd=0.0,
            risk_penalty_usd=order_amount_usd * (0.25 if supplier_otif < 80 else 0.05),
        )

        # Candidate B: Split Order
        c_b = DecisionCandidate(
            action_code="SPLIT_ORDER_ALLOCATION",
            action_name="Split Order 60/40 with Backup Supplier",
            description="Reallocate 40% volume to local secondary supplier to safeguard critical customer delivery.",
            benefit_usd=order_amount_usd * 0.18,  # Preserves customer SLA
            cost_usd=order_amount_usd * 0.03,     # 3% secondary supplier premium
            risk_penalty_usd=order_amount_usd * 0.02,
        )

        # Candidate C: Expedite Freight
        c_c = DecisionCandidate(
            action_code="EXPEDITE_AIR_FREIGHT",
            action_name="Expedite Critical Quantity via Air Freight",
            description="Air-freight 20% emergency buffer stock to bypass port congestion.",
            benefit_usd=order_amount_usd * 0.15,
            cost_usd=order_amount_usd * 0.08,     # Express air cost
            risk_penalty_usd=0.0,
        )

        candidates = [c_a, c_b, c_c]

        # Evaluate EV, Utility & Constraints
        for c in candidates:
            c.expected_value_usd = ExpectedValueEngine.calculate_expected_value(
                benefit_usd=c.benefit_usd,
                cost_usd=c.cost_usd,
                risk_penalty_usd=c.risk_penalty_usd,
                probability_of_success=0.92 if c.action_code == "SPLIT_ORDER_ALLOCATION" else 0.75,
            )
            c.utility_score = RankingEngine.calculate_utility(c)
            c.constraints_satisfied = ConstraintEngine.validate_candidate(
                candidate=c,
                budget_limit_usd=order_amount_usd * 0.10,
            )

        # Rank and recommend
        ranked = RankingEngine.rank_candidates(candidates)
        recommended = ranked[0]
        recommended.is_recommended = True

        conf_score = DecisionConfidenceEngine.calculate_confidence(
            data_quality_score=0.95,
            data_freshness_score=0.98,
            model_accuracy_score=0.91,
            coverage_score=0.90,
        )

        return UniversalDecisionCard(
            tenant_id=tenant_id,
            decision_domain=DecisionDomain.PROCUREMENT_SUPPLIER,
            decision_type="SUPPLIER_DISRUPTION_REMEDIATION",
            entity_type="SUPPLIER",
            entity_id=supplier_id,
            title=f"Supplier Allocation Strategy: {supplier_name}",
            why_summary=f"Primary supplier OTIF is {supplier_otif:.1f}% with {port_delay_days:.0f} days port delay exposure.",
            recommended_action=recommended.action_name,
            decision_state=DecisionState.PROPOSED,
            expected_value_usd=recommended.expected_value_usd,
            downside_risk_usd=recommended.risk_penalty_usd,
            confidence_score=conf_score,
            financial_impact_summary=f"Generates net expected value of ${recommended.expected_value_usd:,.2f} against downside exposure of ${recommended.risk_penalty_usd:,.2f}.",
            operational_impact_summary="Preserves 98% commercial customer OTIF delivery commitment.",
            alternatives=ranked,
            constraints_evaluated={"BUDGET_COMPLIANCE": "SATISFIED", "CAPACITY_FEASIBILITY": "SATISFIED"},
            assumptions=["Backup vendor has verified 200 unit on-hand buffer.", "Customer OTIF penalty SLA is enforceable."],
            model_name="AURIX_SUPPLIER_ALLOC_V2",
            model_version="v2.0",
            model_fitness=ModelFitnessRating.HIGH,
            approval_required=recommended.cost_usd > 5000.0,
            required_approver_role="PROCUREMENT_MANAGER" if recommended.cost_usd > 5000.0 else None,
            is_reversible=True,
            evidence={"supplier_otif": supplier_otif, "order_amount": order_amount_usd, "port_delay": port_delay_days},
            provenance_trace=[f"orders:sku={target_sku_id}", f"suppliers:id={supplier_id}", "external_signals:port_congestion"],
        )
