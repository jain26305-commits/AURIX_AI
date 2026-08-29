
"""
AURIX Unified Intelligence Orchestrator.

This is the controlled execution boundary between:

    semantic decision
        ↓
    canonical business contract
        ↓
    evidence control
        ↓
    deterministic reasoning / expert engine
        ↓
    normalized answer context

The orchestrator contains no domain mathematics.

It fails closed when:
    - the decision is unknown
    - required evidence is unavailable
    - required expert inputs are incomplete
    - the expert contract explicitly disables execution
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from aurix_core.intelligence.domain_registry import (
    DomainRegistry,
)
from aurix_core.intelligence.evidence import (
    EvidencePack,
)
from aurix_core.intelligence.evidence_control import (
    EvidenceControl,
    ExpertContractRegistry,
    ExpertPreparation,
)
from aurix_core.intelligence.expert_executor import ExpertExecutor
from aurix_core.intelligence.claim_validator import (
    ClaimValidator,
    SpecialistClaimNormalizer,
)


@dataclass
class IntelligenceExecutionResult:
    """
    Unified result of deterministic intelligence execution.
    """

    decision: str

    status: str = "BLOCKED"

    execution_path: Optional[str] = None

    expert_executed: bool = False

    blocked: bool = False

    escalation_recommended: bool = False

    confidence: float = 0.0

    claims: List[Any] = field(
        default_factory=list
    )

    expert_result: Any = None

    preparation: Optional[
        ExpertPreparation
    ] = None

    blockers: List[str] = field(
        default_factory=list
    )

    limitations: List[str] = field(
        default_factory=list
    )

    provenance: Dict[str, Any] = field(
        default_factory=dict
    )


class IntelligenceOrchestrator:
    """
    Single deterministic execution boundary.
    """

    @classmethod
    def execute(
        cls,
        *,
        decision: str,
        evidence_pack: EvidencePack,
        fused: Any,
        domain: Optional[str] = None,
        intent: Optional[str] = None,
    ) -> IntelligenceExecutionResult:

        decision_key = decision.strip().upper()

        # ------------------------------------------------------
        # Canonical decision validation.
        # ------------------------------------------------------

        try:
            decision_spec = DomainRegistry.get(
                decision_key
            )
        except KeyError as exc:

            return IntelligenceExecutionResult(
                decision=decision_key,
                status="INVALID_DECISION",
                blocked=True,
                escalation_recommended=True,
                blockers=[
                    str(exc)
                ],
                provenance={
                    "stage": "DECISION_VALIDATION",
                    "decision": decision_key,
                },
            )

        # ------------------------------------------------------
        # Domain consistency.
        # ------------------------------------------------------

        requested_domain = (
            domain.upper()
            if domain
            else decision_spec.domain.upper()
        )

        if (
            requested_domain
            != decision_spec.domain.upper()
        ):

            return IntelligenceExecutionResult(
                decision=decision_key,
                status="DOMAIN_MISMATCH",
                blocked=True,
                escalation_recommended=True,
                blockers=[
                    "DECISION_DOMAIN_MISMATCH"
                ],
                provenance={
                    "stage": "DOMAIN_VALIDATION",
                    "decision": decision_key,
                    "requested_domain": requested_domain,
                    "decision_domain": (
                        decision_spec.domain
                    ),
                },
            )

        # ------------------------------------------------------
        # Evidence preparation.
        #
        # Convert FusedEvidence into the source->records format
        # expected by EvidenceControl.
        # ------------------------------------------------------

        evidence = cls._extract_evidence(
            evidence_pack
        )

        # EvidencePack is the authoritative raw-record input boundary.
        # FusedEvidence alone must never be used to reconstruct
        # specialist-engine records.
        if evidence_pack is None:
            return IntelligenceExecutionResult(
                decision=decision_key,
                status="EVIDENCE_PACK_REQUIRED",
                blocked=True,
                escalation_recommended=True,
                blockers=[
                    "EVIDENCE_PACK_REQUIRED"
                ],
                limitations=[
                    (
                        "Original evidence records are required "
                        "for specialist execution."
                    )
                ],
                provenance={
                    "stage": "EVIDENCE_INPUT_VALIDATION",
                    "decision": decision_key,
                },
            )

        preparation = (
            EvidenceControl.prepare_expert_inputs(
                decision=decision_key,
                evidence=evidence,
                tenant_id=getattr(
                    fused,
                    "tenant_id",
                    None,
                ),
            )
        )

        if not preparation.ready:

            blockers = list(
                preparation.unavailable_sources
            )

            blockers.extend(
                preparation.missing_sources
            )

            blockers.extend(
                preparation.missing_fields
            )

            limitations = []

            if preparation.unavailable_sources:
                limitations.append(
                    "Required evidence is currently unavailable."
                )

            if preparation.missing_sources:
                limitations.append(
                    "Required evidence was not retrieved."
                )

            if preparation.missing_fields:
                limitations.append(
                    "Required expert input fields are incomplete."
                )

            return IntelligenceExecutionResult(
                decision=decision_key,
                status="INSUFFICIENT_EVIDENCE",
                execution_path=(
                    preparation.provenance.get(
                        "path"
                    )
                ),
                blocked=True,
                escalation_recommended=True,
                preparation=preparation,
                blockers=blockers,
                limitations=limitations,
                provenance={
                    "stage": "EVIDENCE_GATE",
                    "decision": decision_key,
                    "domain": decision_spec.domain,
                    "intent": intent,
                    **preparation.provenance,
                },
            )

        # ------------------------------------------------------
        # Specialist-engine path.
        # ------------------------------------------------------

        try:
            contract = ExpertContractRegistry.get(
                decision_key
            )
        except KeyError:

            # No specialist contract means the canonical decision
            # belongs to deterministic reasoning.
            return cls._execute_reasoning(
                decision_spec=decision_spec,
                decision=decision_key,
                fused=fused,
                preparation=preparation,
                intent=intent,
            )

        # ------------------------------------------------------
        # Specialist execution.
        # The executor is the single specialist invocation boundary.
        # ------------------------------------------------------

        tenant_id = getattr(fused, "tenant_id", None)
        expert_execution = ExpertExecutor.execute(
            decision=decision_key,
            prepared_inputs=preparation.inputs,
            available_sources=evidence_pack.available_sources,
            missing_sources=(
                list(evidence_pack.unavailable_sources)
                + list(preparation.missing_sources)
                + list(preparation.unavailable_sources)
            ),
            missing_fields=preparation.missing_fields,
            tenant_id=tenant_id,
            provenance={
                "stage": "EXPERT_EXECUTION",
                "domain": decision_spec.domain,
                "intent": intent,
                "evidence_provenance": getattr(evidence_pack, "items", None),
            },
        )

        if not expert_execution.executed:
            return IntelligenceExecutionResult(
                decision=decision_key,
                status=expert_execution.status,
                execution_path="SPECIALIST_ENGINE",
                expert_executed=False,
                blocked=True,
                escalation_recommended=True,
                preparation=preparation,
                blockers=list(expert_execution.blockers),
                limitations=list(expert_execution.limitations),
                provenance=dict(expert_execution.provenance),
            )

        claims = SpecialistClaimNormalizer.normalize(
            decision=decision_key,
            result=expert_execution.result,
            contract=contract,
            tenant_id=tenant_id,
            available_sources=evidence_pack.available_sources,
        )
        validation = ClaimValidator.validate(
            decision=decision_key,
            claims=claims,
            available_sources=evidence_pack.available_sources,
            domain=decision_spec.domain,
            tenant_id=tenant_id,
        )

        limitations = list(expert_execution.limitations)
        limitations.extend(validation.limitations)

        return IntelligenceExecutionResult(
            decision=decision_key,
            status=(
                "EXECUTED"
                if validation.accepted
                else "EXECUTED_WITHOUT_ANSWERABLE_CLAIMS"
            ),
            execution_path="SPECIALIST_ENGINE",
            expert_executed=True,
            blocked=False,
            escalation_recommended=not bool(validation.accepted),
            confidence=max(
                (c.confidence for c in validation.accepted),
                default=0.0,
            ),
            claims=list(validation.accepted),
            expert_result=expert_execution.result,
            preparation=preparation,
            limitations=list(dict.fromkeys(limitations)),
            provenance={
                **expert_execution.provenance,
                "claim_validation": validation.provenance,
            },
        )

    @classmethod
    def _execute_reasoning(
        cls,
        *,
        decision_spec: Any,
        decision: str,
        fused: Any,
        preparation: ExpertPreparation,
        intent: Optional[str],
    ) -> IntelligenceExecutionResult:

        from aurix_core.intelligence.reasoning_engine import (
            DeterministicReasoningEngine,
        )

        try:
            reasoning = (
                DeterministicReasoningEngine.reason(
                    fused,
                    domain=decision_spec.domain,
                    intent=intent,
                )
            )

        except Exception as exc:

            return IntelligenceExecutionResult(
                decision=decision,
                status="REASONING_EXECUTION_FAILED",
                execution_path="DETERMINISTIC_REASONING",
                blocked=True,
                escalation_recommended=True,
                preparation=preparation,
                blockers=[
                    "REASONING_EXECUTION_FAILED"
                ],
                limitations=[
                    (
                        "Deterministic reasoning could not "
                        "complete successfully."
                    )
                ],
                provenance={
                    "stage": "DETERMINISTIC_REASONING",
                    "decision": decision,
                    "domain": decision_spec.domain,
                    "error_type": (
                        type(exc).__name__
                    ),
                    "error": str(exc),
                },
            )

        validation = ClaimValidator.validate(
            decision=decision,
            claims=list(getattr(reasoning, "claims", [])),
            available_sources=getattr(fused, "available_sources", []),
            domain=decision_spec.domain,
            tenant_id=getattr(fused, "tenant_id", None),
        )

        limitations = list(
            getattr(
                reasoning,
                "unsupported_conclusions",
                [],
            )
        )
        limitations.extend(validation.limitations)

        return IntelligenceExecutionResult(
            decision=decision,
            status="EXECUTED",
            execution_path="DETERMINISTIC_REASONING",
            expert_executed=False,
            blocked=False,
            escalation_recommended=(
                getattr(reasoning, "escalation_recommended", False)
                or not bool(validation.accepted)
            ),
            confidence=getattr(reasoning, "confidence", 0.0),
            claims=list(validation.accepted),
            expert_result=reasoning,
            preparation=preparation,
            limitations=list(dict.fromkeys(limitations)),
            provenance={
                "stage": "DETERMINISTIC_REASONING",
                "decision": decision,
                "domain": decision_spec.domain,
                "intent": intent,
                "claim_validation": validation.provenance,
            },
        )

    @staticmethod
    def _extract_evidence(
        evidence_pack: EvidencePack,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Convert the original EvidencePack into the source -> records
        structure required by ExpertContract preparation.

        EvidencePack is deliberately used here instead of FusedEvidence.

        FusedEvidence is a normalized analytical representation and is
        therefore not guaranteed to preserve the original record shape
        required by specialist expert engines.
        """

        result: Dict[
            str,
            List[Dict[str, Any]]
        ] = {}

        for item in (
            getattr(
                evidence_pack,
                "items",
                None,
            )
            or []
        ):

            source = str(
                getattr(
                    item,
                    "source",
                    "",
                )
                or ""
            ).strip()

            if not source:
                continue

            records = (
                getattr(
                    item,
                    "records",
                    None,
                )
                or []
            )

            valid_records = [
                record
                for record in records
                if isinstance(record, dict)
            ]

            if valid_records:
                result[source] = valid_records

        return result

    @staticmethod
    def _invoke_expert(
        *,
        method: Any,
        inputs: Dict[str, Any],
    ) -> Any:

        return method(
            **inputs
        )


__all__ = [
    "IntelligenceExecutionResult",
    "IntelligenceOrchestrator",
]
