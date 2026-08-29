"""Deterministic validation and normalization of AURIX business claims."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence

from aurix_core.intelligence.claim import DeterministicClaim
from aurix_core.intelligence.domain_registry import DomainRegistry
from aurix_core.intelligence.expert_contracts import ExpertContractRegistry


class ClaimValidationResult:
    """Structured result of deterministic claim validation."""

    def __init__(
        self,
        *,
        claims: Sequence[DeterministicClaim],
        accepted: Sequence[DeterministicClaim],
        rejected: Sequence[DeterministicClaim],
        limitations: Sequence[str] = (),
        provenance: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.claims = list(claims)
        self.accepted = list(accepted)
        self.rejected = list(rejected)
        self.limitations = list(limitations)
        self.provenance = dict(provenance or {})

    @property
    def all_valid(self) -> bool:
        return not self.rejected


class ClaimValidator:
    """Structural claim validator; never uses an LLM for validation."""

    BLOCKED_CATEGORIES = {
        "UNSUPPORTED",
        "UNSUPPORTED_CAUSALITY",
    }

    @classmethod
    def validate(
        cls,
        *,
        decision: str,
        claims: Iterable[DeterministicClaim],
        available_sources: Optional[Sequence[str]] = None,
        domain: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> ClaimValidationResult:
        decision_key = str(decision).strip().upper()
        available = {str(value) for value in (available_sources or ())}
        decision_spec = DomainRegistry.get(decision_key)
        allowed_domain = (domain or decision_spec.domain).upper()

        accepted: List[DeterministicClaim] = []
        rejected: List[DeterministicClaim] = []
        limitations: List[str] = []

        for claim in claims:
            reasons = cls._rejection_reasons(
                claim=claim,
                decision=decision_key,
                decision_spec=decision_spec,
                available_sources=available,
                domain=allowed_domain,
            )
            if reasons:
                claim.supported = False
                claim.allowable_in_answer = False
                rejected.append(claim)
                limitations.extend(reasons)
            else:
                accepted.append(claim)
                limitations.extend(
                    cls._freshness_limitations(
                        claim=claim,
                    )
                )

        # Preserve first-seen order without duplicating limitations.
        limitations = list(dict.fromkeys(limitations))
        return ClaimValidationResult(
            claims=[*accepted, *rejected],
            accepted=accepted,
            rejected=rejected,
            limitations=limitations,
            provenance={
                "validator": "ClaimValidator",
                "decision": decision_key,
                "domain": allowed_domain,
                "tenant_id": tenant_id,
                "accepted_claims": len(accepted),
                "rejected_claims": len(rejected),
            },
        )

    @staticmethod
    def _freshness_rejection_reasons(
        *,
        claim: DeterministicClaim,
    ) -> List[str]:
        """Consume canonical freshness metadata without recalculation."""

        state = str(
            getattr(claim, "freshness_state", "UNKNOWN")
            or "UNKNOWN"
        ).upper()

        category = str(
            getattr(claim, "category", "")
            or ""
        ).upper()

        reasons: List[str] = []

        if (
            category == "VERIFIED"
            and state in {"STALE", "VERY_STALE", "UNKNOWN"}
        ):
            reasons.append(
                "CLAIM_FRESHNESS_" + state + "_VERIFIED_BLOCKED"
            )

        if (
            category == "RECOMMENDATION"
            and state in {"STALE", "VERY_STALE", "UNKNOWN"}
        ):
            reasons.append(
                "CLAIM_FRESHNESS_" + state + "_RECOMMENDATION_BLOCKED"
            )

        return reasons

    @staticmethod
    def _freshness_limitations(
        *,
        claim: DeterministicClaim,
    ) -> List[str]:
        """Return disclosure limitations from canonical freshness metadata.

        This helper consumes only the freshness state already attached to the
        DeterministicClaim. It does not calculate age, inspect timestamps,
        select authority, or apply freshness thresholds.
        """
        state = str(
            getattr(claim, "freshness_state", "UNKNOWN")
            or "UNKNOWN"
        ).upper()

        category = str(
            getattr(claim, "category", "")
            or ""
        ).upper()

        limitations: List[str] = []

        if state == "RECENT" and category == "RECOMMENDATION":
            limitations.append(
                "CLAIM_FRESHNESS_RECENT_RECOMMENDATION_DISCLOSURE"
            )

        elif state == "STALE" and category == "INFORMATIONAL":
            limitations.append(
                "CLAIM_FRESHNESS_STALE_INFORMATIONAL_QUALIFIED"
            )

        elif state == "VERY_STALE" and category == "INFORMATIONAL":
            limitations.append(
                "CLAIM_FRESHNESS_VERY_STALE_INFORMATIONAL_QUALIFIED"
            )

        elif state == "UNKNOWN" and category == "INFORMATIONAL":
            limitations.append(
                "CLAIM_FRESHNESS_UNKNOWN_INFORMATIONAL_QUALIFIED"
            )

        return limitations


    @classmethod
    def _rejection_reasons(
        cls,
        *,
        claim: DeterministicClaim,
        decision: str,
        decision_spec: Any,
        available_sources: set[str],
        domain: str,
    ) -> List[str]:
        reasons: List[str] = []

        if not isinstance(claim, DeterministicClaim):
            return ["CLAIM_TYPE_INVALID"]
        reasons.extend(
            cls._freshness_rejection_reasons(
                claim=claim,
            )
        )


        if not claim.statement or not str(claim.statement).strip():
            reasons.append("CLAIM_STATEMENT_EMPTY")

        if not 0.0 <= float(claim.confidence) <= 1.0:
            reasons.append("CLAIM_CONFIDENCE_INVALID")

        if claim.category in cls.BLOCKED_CATEGORIES:
            reasons.append("CLAIM_CATEGORY_NOT_ANSWERABLE")

        if claim.missing_evidence:
            reasons.append("CLAIM_HAS_MISSING_EVIDENCE")

        required_sources = set(decision_spec.required_evidence)
        claim_sources = {
            str(ref).split(".", 1)[0]
            for ref in claim.evidence_refs
            if str(ref).strip()
        }

        # A claim without lineage is not answerable, except for explicit
        # limitation claims which explain absence of support.
        if claim.supported and not claim.evidence_refs:
            reasons.append("CLAIM_PROVENANCE_MISSING")

        unknown_sources = claim_sources - available_sources
        if unknown_sources and claim.supported:
            reasons.append("CLAIM_REFERENCES_UNAVAILABLE_EVIDENCE")

        # A supported claim must not cite evidence from a different
        # canonical decision's required domain unless the current decision
        # explicitly allows that source.
        if claim.supported and claim_sources:
            allowed_sources = required_sources | set(decision_spec.optional_evidence)
            disallowed = claim_sources - allowed_sources
            if disallowed:
                reasons.append("CLAIM_CROSSES_DECISION_EVIDENCE_BOUNDARY")

        if claim.category == "RECOMMENDATION" and not decision_spec.supports_recommendation:
            reasons.append("RECOMMENDATION_NOT_ALLOWED_FOR_DECISION")

        if claim.category in {"CAUSAL", "CAUSALITY"} and not decision_spec.supports_causality:
            reasons.append("CAUSALITY_NOT_ALLOWED_FOR_DECISION")

        if claim.category in {"PREDICTION", "FORECAST"} and not decision_spec.supports_prediction:
            reasons.append("PREDICTION_NOT_ALLOWED_FOR_DECISION")

        if claim.category == "COMPARISON" and not decision_spec.supports_comparison:
            reasons.append("COMPARISON_NOT_ALLOWED_FOR_DECISION")

        if domain != str(decision_spec.domain).upper():
            reasons.append("CLAIM_DOMAIN_MISMATCH")

        return list(dict.fromkeys(reasons))


class SpecialistClaimNormalizer:
    """Convert safe scalar specialist outputs into deterministic claims."""

    @classmethod
    def normalize(
        cls,
        *,
        decision: str,
        result: Any,
        contract: Any = None,
        tenant_id: Optional[str] = None,
        available_sources: Optional[Sequence[str]] = None,
    ) -> List[DeterministicClaim]:
        decision_key = str(decision).strip().upper()
        contract = contract or ExpertContractRegistry.get(decision_key)
        sources = list(available_sources or contract.required_sources)
        source_ref = sources[0] if sources else "specialist"
        values = cls._to_mapping(result)
        claims: List[DeterministicClaim] = []

        if not values:
            return claims

        # A specialist may return an explicit unavailable state.
        # Never turn such metadata into an answerable claim.
        value_state = str(values.get("value_state", "")).upper()
        if value_state == "UNAVAILABLE":
            return claims

        for key, value in values.items():
            if key in cls._excluded_keys() or not cls._answerable_scalar(value):
                continue

            statement = cls._statement(decision_key, key, value)
            if not statement:
                continue

            claims.append(
                DeterministicClaim(
                    statement=statement,
                    category="DERIVED_SPECIALIST",
                    confidence=1.0,
                    evidence_refs=[f"{source_ref}.{key}"],
                    missing_evidence=[],
                    supported=True,
                    allowable_in_answer=True,
                    severity="INFO",
                )
            )

        return claims

    @staticmethod
    def _excluded_keys() -> set[str]:
        return {
            "provenance",
            "metadata",
            "limitations",
            "warning",
            "warnings",
            "error",
            "errors",
            "status",
            "message",
            "description",
            "explanation",
            "recommendation",
            "recommendations",
            "eta_source",
            "eta_method",
            "evidence_quality",
            "value_state",
            "supporting_sample_size",
            "tenant_id",
            "currency",
            "tracked_value",
            "driver_attribution",
        }

    @staticmethod
    def _answerable_scalar(value: Any) -> bool:
        if value is None or isinstance(value, bool):
            return value is not None
        return isinstance(value, (str, int, float, date, datetime))

    @staticmethod
    def _to_mapping(result: Any) -> Dict[str, Any]:
        if result is None:
            return {}
        if isinstance(result, dict):
            return dict(result)
        if is_dataclass(result):
            return asdict(result)
        if hasattr(result, "model_dump"):
            dumped = result.model_dump()
            return dict(dumped) if isinstance(dumped, dict) else {}
        if hasattr(result, "dict") and callable(result.dict):
            dumped = result.dict()
            return dict(dumped) if isinstance(dumped, dict) else {}
        if hasattr(result, "__dict__"):
            return {
                key: value
                for key, value in vars(result).items()
                if not key.startswith("_")
            }
        return {}

    @staticmethod
    def _statement(decision: str, key: str, value: Any) -> Optional[str]:
        labels = key.replace("_", " ").strip()
        if isinstance(value, datetime):
            rendered = value.isoformat()
        elif isinstance(value, date):
            rendered = value.isoformat()
        elif isinstance(value, float):
            rendered = f"{value:.4f}".rstrip("0").rstrip(".")
        else:
            rendered = str(value)
        if not rendered:
            return None
        return f"{labels.capitalize()} is {rendered}."


__all__ = [
    "ClaimValidationResult",
    "ClaimValidator",
    "SpecialistClaimNormalizer",
]
