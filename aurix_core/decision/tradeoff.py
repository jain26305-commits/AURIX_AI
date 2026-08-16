"""Multi-objective trade-off evaluator comparing operational, financial, and risk impacts across scenarios."""

from typing import List
from aurix_core.schema.phase9_contract import (
    DecisionRecommendation,
    TradeoffOption,
)


class TradeoffEvaluator:
    """Evaluates and structures trade-off options across competing operational and financial objectives."""

    @classmethod
    def compare_recommendations(
        cls,
        primary: DecisionRecommendation,
        alternatives: List[DecisionRecommendation],
    ) -> List[TradeoffOption]:
        """
        Compares alternative decision recommendations against the primary recommendation
        and generates explicit trade-off explanations without hiding multi-dimensional impacts inside a single score.
        """
        options: List[TradeoffOption] = []

        for idx, alt in enumerate(alternatives, start=1):
            reasons: List[str] = []

            # Compare Operational Impact (Coverage Days)
            p_cov_obj = primary.operational_impact.inventory_coverage_change_days
            a_cov_obj = alt.operational_impact.inventory_coverage_change_days

            p_cov = float(p_cov_obj.value) if (p_cov_obj and p_cov_obj.value is not None) else 0.0
            a_cov = float(a_cov_obj.value) if (a_cov_obj and a_cov_obj.value is not None) else 0.0

            if a_cov == float("inf") or p_cov == float("inf"):
                if a_cov > p_cov:
                    reasons.append("Provides permanent coverage (zero demand risk) compared to primary option.")
                elif a_cov < p_cov:
                    reasons.append("Primary option provides permanent coverage, whereas this alternative does not.")
            else:
                if a_cov > p_cov:
                    reasons.append(
                        f"Provides {a_cov - p_cov:.1f} more days of coverage improvement than primary option."
                    )
                elif a_cov < p_cov:
                    reasons.append(
                        f"Provides {p_cov - a_cov:.1f} fewer days of coverage improvement than primary option."
                    )
            # Compare Financial Impact (Total Cost Change)
            p_cost_obj = primary.financial_impact.total_cost_change
            a_cost_obj = alt.financial_impact.total_cost_change

            p_cost = float(p_cost_obj.value) if (p_cost_obj and p_cost_obj.value is not None) else None
            a_cost = float(a_cost_obj.value) if (a_cost_obj and a_cost_obj.value is not None) else None

            if p_cost is not None and a_cost is not None:
                if a_cost < p_cost:
                    reasons.append(
                        f"Lower transportation/transfer cost by {p_cost - a_cost:.2f} {alt.financial_impact.currency}."
                    )
                elif a_cost > p_cost:
                    reasons.append(
                        f"Higher transportation/transfer cost by {a_cost - p_cost:.2f} {alt.financial_impact.currency}."
                    )

            if not reasons:
                reasons.append("Similar operational and financial performance profile.")

            tradeoff_reason_str = " | ".join(reasons)

            options.append(
                TradeoffOption(
                    option_id=f"ALT-OPTION-{idx}",
                    description=f"Alternative transfer from {alt.source_node} to {alt.destination_node} (Qty: {alt.quantity})",
                    decision_type=alt.decision_type,
                    operational_impact=alt.operational_impact,
                    financial_impact=alt.financial_impact,
                    feasibility=alt.feasibility,
                    tradeoff_reason=tradeoff_reason_str,
                )
            )

        return options
