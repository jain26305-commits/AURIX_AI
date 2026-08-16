"""Evidence chain builder connecting multi-phase operational associations for Phase 9 Executive Intelligence."""

import uuid
from typing import List, Optional
from aurix_core.intelligence.config import IntelligenceConfiguration
from aurix_core.schema.phase5_contract import TrackedValue, ValueState
from aurix_core.schema.phase8_contract import Phase8InputContract
from aurix_core.schema.phase9_contract import Phase9InputContract
from aurix_core.schema.phase10_contract import Phase10InputContract
from aurix_core.schema.phase11_contract import (
    BusinessSignal,
    EvidenceChain,
    EvidenceChainStep,
)


class EvidenceChainBuilder:
    """Constructs multi-phase evidence chains correlating operational signals and decisions without claiming unproven physical causality."""

    RELATIONSHIP_PRIMARY_TRIGGER: str = "PRIMARY_TRIGGER"
    RELATIONSHIP_ASSOCIATED_DECISION: str = "ASSOCIATED_DECISION"
    RELATIONSHIP_QUANTIFIED_IMPACT: str = "QUANTIFIED_IMPACT"
    RELATIONSHIP_EVIDENTIARY_ASSOCIATION: str = "EVIDENTIARY_ASSOCIATION"

    @classmethod
    def build_evidence_chains(
        cls,
        signals: List[BusinessSignal],
        phase7a_contract: Optional[Phase8InputContract] = None,
        phase7b_contract: Optional[Phase9InputContract] = None,
        phase8_contract: Optional[Phase10InputContract] = None,
        config: Optional[IntelligenceConfiguration] = None,
    ) -> List[EvidenceChain]:
        """Constructs evidence chains for signals using available multi-phase data and evidence-backed relationship classifications."""
        cfg = config or IntelligenceConfiguration()
        if not signals:
            return []

        chains: List[EvidenceChain] = []

        for sig in signals:
            if len(chains) >= cfg.max_evidence_chains:
                break

            chain_id = f"CHN-{uuid.uuid4().hex[:8]}"
            steps: List[EvidenceChainStep] = []

            # Step 1: Primary Signal Origin (Direct Evidence)
            metric_val = next(iter(sig.source_metrics.values()), None) if sig.source_metrics else None
            if not metric_val:
                metric_val = TrackedValue(
                    value=None,
                    state=ValueState.UNAVAILABLE,
                    source="SIGNAL_EVIDENCE",
                )

            steps.append(
                EvidenceChainStep(
                    step_number=1,
                    phase=sig.source_phase,
                    entity_id=sig.affected_entity_id,
                    metric_name=sig.signal_type,
                    metric_value=metric_val,
                    relationship_type=cls.RELATIONSHIP_PRIMARY_TRIGGER,
                    explanation=f"Primary signal {sig.signal_type} observed with severity {sig.severity.value}.",
                )
            )

            # Step 2: Correlated Decision / Rebalancing Step (Associated Decision)
            if phase7b_contract:
                sku_key = sig.provenance.get("sku_id") or sig.affected_entity_id.split("@")[0]
                opt = phase7b_contract.decisions.get(sku_key)
                if opt and opt.recommended_action:
                    rec = opt.recommended_action
                    steps.append(
                        EvidenceChainStep(
                            step_number=len(steps) + 1,
                            phase="Phase 7B",
                            entity_id=f"{rec.source_node}->{rec.destination_node}",
                            metric_name="REBALANCE_QUANTITY",
                            metric_value=TrackedValue(
                                value=rec.quantity,
                                state=ValueState.DERIVED,
                                source="DECISION_ENGINE",
                            ),
                            relationship_type=cls.RELATIONSHIP_ASSOCIATED_DECISION,
                            explanation=(
                                f"Associated decision option: validated rebalancing transfer of {rec.quantity:.1f} "
                                "units available to mitigate exposure."
                            ),
                        )
                    )

            # Step 3: Correlated Financial Impact (Quantified Impact)
            if sig.financial_exposure and sig.financial_exposure.value is not None:
                steps.append(
                    EvidenceChainStep(
                        step_number=len(steps) + 1,
                        phase=sig.source_phase,
                        entity_id=sig.affected_entity_id,
                        metric_name="FINANCIAL_EXPOSURE",
                        metric_value=sig.financial_exposure,
                        relationship_type=cls.RELATIONSHIP_QUANTIFIED_IMPACT,
                        explanation=(
                            f"Associated financial impact quantified at {float(sig.financial_exposure.value):.2f} "
                            "in native currency."
                        ),
                    )
                )

            chains.append(
                EvidenceChain(
                    chain_id=chain_id,
                    title=f"Evidence Chain for {sig.affected_entity_id} ({sig.signal_type})",
                    primary_signal_id=sig.signal_id,
                    steps=steps,
                    summary=(
                        f"Evidentiary association chain connecting {sig.signal_type} in {sig.source_phase} "
                        f"to operational decisions and financial metrics across {len(steps)} verified steps."
                    ),
                )
            )

        return chains