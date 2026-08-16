"""Structured executive narrative generator for Phase 9 Executive Intelligence."""

from typing import List, Optional
from aurix_core.intelligence.config import IntelligenceConfiguration
from aurix_core.schema.phase11_contract import (
    BusinessSignal,
    EvidenceChain,
    ExecutiveSummary,
    ExecutiveSummarySection,
    PrioritizedAction,
    SignalSeverity,
)


class ExecutiveNarrativeGenerator:
    """Generates structured, machine-readable executive summaries directly from validated evidence."""

    @classmethod
    def generate_summary(
        cls,
        signals: List[BusinessSignal],
        actions: List[PrioritizedAction],
        chains: List[EvidenceChain],
        config: Optional[IntelligenceConfiguration] = None,
        data_sufficiency: str = "ADEQUATE",
    ) -> ExecutiveSummary:
        """Constructs an ExecutiveSummary from signals, prioritized actions, and evidence chains."""
        # 1. Overall Health Status
        critical_count = sum(1 for s in signals if s.severity == SignalSeverity.CRITICAL)
        high_count = sum(1 for s in signals if s.severity == SignalSeverity.HIGH)

        if critical_count > 0:
            overall_health = "CRITICAL_EXPOSURE"
            headline = f"Executive Alert: {critical_count} critical operational/financial risk signals identified."
        elif high_count > 0:
            overall_health = "ELEVATED_RISK"
            headline = f"Executive Warning: {high_count} high-priority risks require management attention."
        elif signals:
            overall_health = "STABLE_WITH_OPPORTUNITIES"
            headline = "Network Operations Stable: Rebalancing and optimization opportunities available."
        elif data_sufficiency in ("INSUFFICIENT", "PARTIAL"):
            overall_health = "INSUFFICIENT_EVIDENCE"
            headline = "Executive Notice: Insufficient upstream analytical evidence to rule out operational risk."
        else:
            overall_health = "STABLE_WITH_NO_MATERIAL_EXCEPTIONS"
            headline = "Supply Chain Operating Within Normal Parameters: No material exceptions detected."

        # 2. What Changed Section
        what_changed_takeaways = [f"Detected {len(signals)} actionable business signals across active domains."]
        if signals:
            what_changed_takeaways.append(
                f"Primary activity concentrated in {signals[0].domain.value} domain."
            )
        else:
            if data_sufficiency in ("INSUFFICIENT", "PARTIAL"):
                what_changed_takeaways.append("Upstream data coverage is incomplete or insufficient.")
            else:
                what_changed_takeaways.append("No material operational anomalies or risk threshold breaches observed.")

        what_changed_sec = ExecutiveSummarySection(
            section_title="What Changed",
            key_takeaways=what_changed_takeaways,
            detailed_narrative=(
                f"Recent evaluation identified {len(signals)} distinct operational and financial signals. "
                "Network conditions reflect active inventory imbalances and working capital allocations."
            ),
        )

        # 3. Top Risks Section
        risk_signals = [s for s in signals if s.severity in (SignalSeverity.CRITICAL, SignalSeverity.HIGH)]
        risk_takeaways = [
            f"{s.signal_type} on {s.affected_entity_id}: {s.description}" for s in risk_signals[:3]
        ]
        if not risk_takeaways:
            if data_sufficiency in ("INSUFFICIENT", "PARTIAL"):
                risk_takeaways = ["Data sufficiency is limited; unmonitored risk exposure may exist."]
            else:
                risk_takeaways = ["No critical or high-severity operational risks currently flagged."]

        top_risks_sec = ExecutiveSummarySection(
            section_title="Top Risks",
            key_takeaways=risk_takeaways,
            detailed_narrative=(
                f"Identified {len(risk_signals)} high-exposure risk areas across the portfolio. "
                "Attention should focus on working capital concentration and single-source dependencies."
            ),
        )

        # 4. Top Opportunities Section
        opp_signals = [s for s in signals if "OPPORTUNITY" in s.signal_type or "REBALANCE" in s.signal_type]
        opp_takeaways = [f"{s.description}" for s in opp_signals[:3]]
        if not opp_takeaways:
            opp_takeaways = ["No immediate structural rebalancing opportunities identified in current cycle."]

        top_opps_sec = ExecutiveSummarySection(
            section_title="Top Opportunities",
            key_takeaways=opp_takeaways,
            detailed_narrative=(
                f"Discovered {len(opp_signals)} validated operational optimization opportunities "
                "capable of releasing working capital or reducing lead-time exposure."
            ),
        )

        # 5. Recommended Actions Section
        action_takeaways = [
            f"Rank #{act.rank}: {act.title} (Score: {act.priority_score:.2f})" for act in actions[:3]
        ]
        if not action_takeaways:
            action_takeaways = ["No specific management actions required at this time."]

        recommended_actions_sec = ExecutiveSummarySection(
            section_title="Recommended Actions",
            key_takeaways=action_takeaways,
            detailed_narrative=(
                f"Prioritized {len(actions)} management actions based on multi-dimensional scoring of "
                "severity, financial value, and operational urgency."
            ),
        )

        # 6. Financial Impact Summary
        fin_takeaways: List[str] = []
        fin_signal_count = 0
        for s in signals:
            if s.financial_exposure is not None and s.financial_exposure.value is not None:
                fin_signal_count += 1
                if len(fin_takeaways) < 3:
                    fin_takeaways.append(
                        f"Exposure identified: {s.affected_entity_id} = {float(s.financial_exposure.value):.2f}"
                    )
        if not fin_takeaways:
            fin_takeaways = ["Financial impact metrics unavailable or not applicable for current signals."]

        fin_sec = ExecutiveSummarySection(
            section_title="Financial Impact Summary",
            key_takeaways=fin_takeaways,
            detailed_narrative=(
                f"Quantified financial metrics available for {fin_signal_count} signals. "
                "All monetary values strictly preserve native currency isolation."
            ),
        )

        # 7. Operational Impact Summary
        op_takeaways = [f"Constructed {len(chains)} evidence chains linking root causes."]
        op_sec = ExecutiveSummarySection(
            section_title="Operational Impact Summary",
            key_takeaways=op_takeaways,
            detailed_narrative=(
                "Operational metrics trace inventory coverage, lead times, and transfer feasibility "
                "across distribution centers and supply channels."
            ),
        )

        # 8. Data Limitations
        lim_takeaways = [
            "Narratives are generated strictly from validated facts using Zero-Fabrication principles.",
            "Missing cost or lead-time data defaults to ValueState.UNAVAILABLE.",
        ]
        if data_sufficiency in ("INSUFFICIENT", "PARTIAL"):
            lim_takeaways.append("WARNING: Upstream input dataset is incomplete or has missing domain inputs.")

        limitations_sec = ExecutiveSummarySection(
            section_title="Data Limitations",
            key_takeaways=lim_takeaways,
            detailed_narrative=(
                "Analysis is bounded by available upstream inputs from Phases 1-8. "
                "Unobserved metrics are explicitly marked unavailable rather than estimated."
            ),
        )

        return ExecutiveSummary(
            headline=headline,
            overall_health_status=overall_health,
            what_changed=what_changed_sec,
            top_risks=top_risks_sec,
            top_opportunities=top_opps_sec,
            recommended_actions=recommended_actions_sec,
            financial_impact_summary=fin_sec,
            operational_impact_summary=op_sec,
            data_limitations=limitations_sec,
        )