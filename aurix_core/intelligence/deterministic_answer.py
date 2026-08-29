"""
AURIX Deterministic Answer Pipeline.

This module is the orchestration boundary between:
semantic understanding,
evidence acquisition,
evidence fusion,
reasoning,
causal analysis,
decision gates,
and final answer eligibility.

It does not call external AI providers.

Its only responsibility is to determine:
1. what AURIX knows,
2. what AURIX can safely answer,
3. what remains unsupported,
4. whether deterministic handling is sufficient,
5. whether escalation is justified.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from aurix_core.intelligence.causal_engine import (
    CausalReasoningResult,
    DeterministicCausalEngine,
)
from aurix_core.intelligence.decision_gate import (
    DeterministicDecisionGate,
)
from aurix_core.intelligence.reasoning_engine import (
    DeterministicReasoningEngine,
    DeterministicReasoningResult,
)


@dataclass
class AnswerEligibility:
    # Whether AURIX can fully answer the user's requested decision.
    deterministic_answerable: bool = False

    # Whether AURIX has enough supported information to provide
    # a useful partial answer without pretending the requested
    # decision itself has been resolved.
    partial_answer_available: bool = False

    deterministic_recommendation_allowed: bool = False
    deterministic_causality_allowed: bool = False

    escalation_recommended: bool = False
    escalation_reason: Optional[str] = None

    blockers: List[str] = field(
        default_factory=list
    )

    eligible_claim_count: int = 0
    blocked_claim_count: int = 0

    confidence: float = 0.0


@dataclass
class DeterministicAnswerContext:
    query: str
    entity_id: Optional[str]

    domain: str
    intent: Optional[str]

    reasoning: DeterministicReasoningResult
    causal: CausalReasoningResult

    eligibility: AnswerEligibility

    answer_claims: List[str] = field(
        default_factory=list
    )

    limitations: List[str] = field(
        default_factory=list
    )

    provenance: Dict[str, Any] = field(
        default_factory=dict
    )


class DeterministicAnswerPipeline:
    """
    Evaluates whether a query is sufficiently supported by the
    deterministic AURIX evidence stack.

    External AI should only receive control after this pipeline
    determines that deterministic evidence is insufficient.
    """

    @classmethod
    def evaluate(
        cls,
        *,
        fused: Any,
        domain: str,
        intent: Optional[str] = None,
        requested_decision: Optional[str] = None,
    ) -> DeterministicAnswerContext:

        reasoning = DeterministicReasoningEngine.reason(
            fused,
            domain=domain,
            intent=intent,
        )

        causal = DeterministicCausalEngine.reason(
            fused,
            business_domain=domain,
        )

        eligibility = cls._evaluate_eligibility(
            fused=fused,
            reasoning=reasoning,
            causal=causal,
            domain=domain,
            requested_decision=requested_decision,
        )

        answer_claims = [
            claim.statement
            for claim in reasoning.claims
            if (
                claim.supported
                and claim.allowable_in_answer
            )
        ]

        limitations = [
            claim.statement
            for claim in reasoning.claims
            if (
                not claim.supported
                or not claim.allowable_in_answer
            )
        ]

        result = DeterministicAnswerContext(
            query=fused.query,
            entity_id=fused.entity_id,
            domain=domain.upper(),
            intent=intent,
            reasoning=reasoning,
            causal=causal,
            eligibility=eligibility,
            answer_claims=answer_claims,
            limitations=limitations,
        )

        result.provenance = {
            "pipeline": (
                "deterministic-answer-pipeline-v1"
            ),
            "answer_source": "AURIX_ENGINE",
            "tenant_id": fused.tenant_id,
            "entity_id": fused.entity_id,
            "domain": domain.upper(),
            "intent": intent,
            "requested_decision": requested_decision,
            "deterministic_answerable": (
                eligibility.deterministic_answerable
            ),
            "partial_answer_available": (
                eligibility.partial_answer_available
            ),
            "deterministic_recommendation_allowed": (
                eligibility
                .deterministic_recommendation_allowed
            ),
            "deterministic_causality_allowed": (
                eligibility
                .deterministic_causality_allowed
            ),
            "escalation_recommended": (
                eligibility.escalation_recommended
            ),
            "confidence": eligibility.confidence,
        }

        return result

    @classmethod
    def _evaluate_eligibility(
        cls,
        *,
        fused: Any,
        reasoning: DeterministicReasoningResult,
        causal: CausalReasoningResult,
        domain: str,
        requested_decision: Optional[str],
    ) -> AnswerEligibility:

        supported_claims = [
            claim
            for claim in reasoning.claims
            if (
                claim.supported
                and claim.allowable_in_answer
            )
        ]

        blocked_claims = [
            claim
            for claim in reasoning.claims
            if (
                not claim.supported
                or not claim.allowable_in_answer
            )
        ]

        # --------------------------------------------------------
        # Determine the actual requested decision gate.
        # --------------------------------------------------------

        decision_gate = None

        if requested_decision:
            decision_gate = (
                DeterministicDecisionGate.evaluate(
                    requested_decision,
                    fused.available_sources,
                )
            )

        # Generic deterministic evidence sufficiency.
        generic_answerable = bool(
            supported_claims
        ) and not bool(
            fused.conflicts
        )

        # Partial answer means AURIX knows something useful, even
        # though the requested business decision cannot be settled.
        partial_answer_available = generic_answerable

        # --------------------------------------------------------
        # Decision-aware answerability.
        # --------------------------------------------------------

        if decision_gate is not None:
            deterministic_answerable = (
                decision_gate.can_answer
                and generic_answerable
            )
        else:
            deterministic_answerable = generic_answerable

        # --------------------------------------------------------
        # Recommendation / causality must also respect the gate.
        # --------------------------------------------------------

        deterministic_recommendation_allowed = (
            generic_answerable
            and any(
                claim.category
                == "RECOMMENDATION_GUARDRAIL"
                and claim.allowable_in_answer
                for claim in reasoning.claims
            )
        )

        deterministic_causality_allowed = (
            generic_answerable
            and any(
                link.causal_supported
                and link.allowable_in_answer
                for link in causal.causal_links
            )
        )

        if decision_gate is not None:
            if not decision_gate.can_recommend:
                deterministic_recommendation_allowed = False

            if not decision_gate.can_establish_causality:
                deterministic_causality_allowed = False

        # --------------------------------------------------------
        # Blockers must be decision-specific.
        # --------------------------------------------------------

        if decision_gate is not None:
            blockers = list(
                decision_gate.missing_required_sources
            )
        else:
            blockers = []

        blockers = list(
            dict.fromkeys(
                blockers
            )
        )

        # --------------------------------------------------------
        # Escalation logic.
        # --------------------------------------------------------

        escalation = False
        escalation_reason = None

        if not deterministic_answerable:
            escalation = True

            if decision_gate is not None and blockers:
                escalation_reason = (
                    "The requested business decision requires "
                    "evidence that is currently unavailable."
                )
            else:
                escalation_reason = (
                    "No sufficiently supported deterministic "
                    "claim is available for the requested query."
                )

        # --------------------------------------------------------
        # Confidence semantics.
        #
        # Confidence answers:
        # "How confident is AURIX in the evidence-backed material
        # it can safely state?"
        #
        # It is NOT allowed to imply confidence that a blocked
        # decision has actually been resolved.
        # --------------------------------------------------------

        confidence = float(
            reasoning.confidence
        )

        if causal.confidence > 0:
            confidence = (
                confidence * 0.70
                + causal.confidence * 0.30
            )

        if fused.conflicts:
            confidence = min(
                confidence,
                0.50,
            )

        # Missing evidence for the requested decision should not
        # inflate or overstate the confidence of that decision.
        if (
            decision_gate is not None
            and not decision_gate.can_answer
        ):
            confidence = min(
                confidence,
                0.60,
            )

        # If there is literally no usable deterministic evidence,
        # confidence should collapse.
        if not supported_claims:
            confidence = 0.0

        return AnswerEligibility(
            deterministic_answerable=(
                deterministic_answerable
            ),
            partial_answer_available=(
                partial_answer_available
            ),
            deterministic_recommendation_allowed=(
                deterministic_recommendation_allowed
            ),
            deterministic_causality_allowed=(
                deterministic_causality_allowed
            ),
            escalation_recommended=(
                escalation
            ),
            escalation_reason=(
                escalation_reason
            ),
            blockers=blockers,
            eligible_claim_count=len(
                supported_claims
            ),
            blocked_claim_count=len(
                blocked_claims
            ),
            confidence=round(
                max(
                    0.0,
                    min(
                        0.99,
                        confidence,
                    ),
                ),
                3,
            ),
        )

