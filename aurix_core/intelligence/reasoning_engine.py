"""
AURIX Deterministic Reasoning Engine.

Transforms fused authoritative evidence into structured business reasoning.

Design principles:
- deterministic
- evidence-bound
- explainable
- conservative under missing evidence
- reusable by UI, Answer Composer, alerts, decisions and agents
- no external LLM dependency
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from aurix_core.intelligence.claim import DeterministicClaim
from aurix_core.intelligence.evidence_fusion import (
    DerivedFact,
    EvidenceFact,
    FusedEvidence,
)


@dataclass
class ReasoningFinding:
    category: str
    title: str
    explanation: str
    severity: str = "INFO"
    evidence_refs: List[str] = field(default_factory=list)


@dataclass
class ReasoningRecommendation:
    priority: str
    action: str
    rationale: str
    evidence_refs: List[str] = field(default_factory=list)
    blocked_by: List[str] = field(default_factory=list)


@dataclass
class DeterministicReasoningResult:
    query: str
    entity_id: Optional[str]

    business_domain: str
    state: str

    claims: List[DeterministicClaim] = field(
        default_factory=list
    )

    findings: List[ReasoningFinding] = field(default_factory=list)
    recommendations: List[ReasoningRecommendation] = field(
        default_factory=list
    )

    confirmed_conclusions: List[str] = field(default_factory=list)
    unsupported_conclusions: List[str] = field(
        default_factory=list
    )

    missing_evidence: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)

    confidence: float = 0.0
    evidence_quality: str = "NONE"

    escalation_recommended: bool = False
    escalation_reason: Optional[str] = None

    provenance: Dict[str, Any] = field(default_factory=dict)


class DeterministicReasoningEngine:
    """
    Converts FusedEvidence into business-level deterministic conclusions.
    """

    @classmethod
    def reason(
        cls,
        fused: FusedEvidence,
        *,
        domain: Optional[str] = None,
        intent: Optional[str] = None,
    ) -> DeterministicReasoningResult:
        result = DeterministicReasoningResult(
            query=fused.query,
            entity_id=fused.entity_id,
            business_domain=(
                domain.upper()
                if domain
                else cls._infer_domain(fused)
            ),
            state="INSUFFICIENT_EVIDENCE",
            confidence=fused.confidence,
            evidence_quality=fused.evidence_quality,
        )

        result.conflicts = [
            conflict.description
            for conflict in fused.conflicts
        ]

        result.missing_evidence = list(
            fused.unavailable_sources
        )

        # --------------------------------------------------------
        # Domain-specific insufficiency claims.
        #
        # A decision gate may correctly block a request while the
        # reasoning result still has zero claims. That is technically
        # safe but produces an empty user-facing answer.
        #
        # Create a precise, human-readable limitation claim here so
        # the Answer Pipeline and Composer can explain the blockage.
        # --------------------------------------------------------

        business_domain = result.business_domain.upper()
        missing = set(result.missing_evidence)

        if (
            business_domain == "ECONOMICS"
            and "financial_baseline" in missing
        ):
            cls._add_insufficiency_claim(
                result,
                statement=(
                    "AURIX cannot quantify working-capital "
                    "exposure because financial baseline evidence "
                    "is unavailable."
                ),
                category="WORKING_CAPITAL_EVIDENCE_GAP",
                missing_evidence=[
                    "financial_baseline"
                ],
            )

        elif (
            business_domain == "NETWORK"
            and "intelligence_snapshot" in missing
        ):
            cls._add_insufficiency_claim(
                result,
                statement=(
                    "AURIX cannot produce an authoritative "
                    "executive risk summary because the "
                    "intelligence snapshot is unavailable."
                ),
                category="EXECUTIVE_RISK_EVIDENCE_GAP",
                missing_evidence=[
                    "intelligence_snapshot"
                ],
            )

        elif business_domain == "SUPPLY":
            missing_supplier = [
                source
                for source in (
                    "supplier_performance",
                    "suppliers",
                    "purchase_orders",
                    "shipment_evaluation",
                )
                if source in missing
            ]

            if missing_supplier:
                cls._add_insufficiency_claim(
                    result,
                    statement=(
                        "AURIX cannot establish the requested "
                        "supplier assessment because the required "
                        "supplier-performance evidence is unavailable."
                    ),
                    category="SUPPLIER_EVIDENCE_GAP",
                    missing_evidence=missing_supplier,
                )

        elif business_domain == "LOGISTICS":
            missing_logistics = [
                source
                for source in (
                    "shipments",
                    "shipment_evaluation",
                )
                if source in missing
            ]

            if missing_logistics:
                cls._add_insufficiency_claim(
                    result,
                    statement=(
                        "AURIX cannot provide an authoritative "
                        "shipment assessment because the required "
                        "shipment evidence is unavailable."
                    ),
                    category="SHIPMENT_EVIDENCE_GAP",
                    missing_evidence=missing_logistics,
                )

        # --------------------------------------------------------
        # Domain-isolated reasoning.
        #
        # Evidence availability must never cause unrelated domain
        # reasoning to leak into the requested answer.
        #
        # Only invoke deterministic reasoners that actually exist.
        # Unsupported domains must remain explicitly unsupported
        # rather than falling through to generic OBSERVED reasoning.
        # --------------------------------------------------------

        business_domain = result.business_domain.upper()

        if business_domain == "INVENTORY":
            if cls._has_prefix(
                fused,
                "inventory_position",
            ):
                cls._reason_inventory(
                    fused,
                    result,
                )

        elif business_domain == "SUPPLY":
            if cls._has_prefix(
                fused,
                "supplier_performance",
            ):
                cls._reason_supplier(
                    fused,
                    result,
                )

        elif business_domain == "LOGISTICS":
            if cls._has_prefix(
                fused,
                "shipment_evaluation",
            ):
                cls._reason_logistics(
                    fused,
                    result,
                )

        elif business_domain == "ECONOMICS":
            if cls._has_prefix(
                fused,
                "financial_baseline",
            ):
                cls._reason_finance(
                    fused,
                    result,
                )

        elif business_domain == "GENERAL":
            # Generic reasoning is only appropriate when the planner
            # has not identified a specialized business domain.
            cls._reason_generic(
                fused,
                result,
            )

        else:
            # FORECASTING / NETWORK / other domains do not currently
            # have dedicated deterministic reasoners. Keep the result
            # explicitly unsupported rather than manufacturing an
            # OBSERVED/STABLE business conclusion.
            result.state = "INSUFFICIENT_EVIDENCE"
            result.unsupported_conclusions.append(
                "A dedicated deterministic reasoner is not currently "
                "available for the requested business domain."
            )

        cls._apply_intent_constraints(
            fused=fused,
            result=result,
            intent=intent,
        )

        cls._calculate_escalation(
            fused=fused,
            result=result,
        )

        result.provenance = {
            "reasoning_engine": "deterministic-reasoning-v1",
            "answer_source": "AURIX_ENGINE",
            "tenant_id": fused.tenant_id,
            "entity_id": fused.entity_id,
            "business_domain": result.business_domain,
            "intent": intent,
            "evidence_quality": fused.evidence_quality,
            "available_sources": list(
                fused.available_sources
            ),
            "unavailable_sources": list(
                fused.unavailable_sources
            ),
            "findings": len(result.findings),
            "claims": len(result.claims),
            "recommendations": len(
                result.recommendations
            ),
            "confirmed_conclusions": len(
                result.confirmed_conclusions
            ),
            "unsupported_conclusions": len(
                result.unsupported_conclusions
            ),
        }

        return result

    @staticmethod
    def _has_prefix(
        fused: FusedEvidence,
        source: str,
    ) -> bool:
        return any(
            fact.source == source
            for fact in fused.facts
        )

    @staticmethod
    def _get(
        fused: FusedEvidence,
        key: str,
    ) -> Optional[Any]:
        for fact in reversed(fused.facts):
            if fact.key == key:
                return fact.value

        for derived in reversed(
            fused.derived_facts
        ):
            if derived.key == key:
                return derived.value

        return None

    @staticmethod
    def _derived(
        fused: FusedEvidence,
        key: str,
    ) -> Optional[DerivedFact]:
        for derived in reversed(
            fused.derived_facts
        ):
            if derived.key == key:
                return derived

        return None

    @staticmethod
    def _fact_ref(
        fused: FusedEvidence,
        source: str,
        field_name: str,
    ) -> str:
        return f"{source}.{field_name}"

    @classmethod
    def _infer_domain(
        cls,
        fused: FusedEvidence,
    ) -> str:
        sources = set(fused.available_sources)

        if "inventory_position" in sources:
            return "INVENTORY"

        if "supplier_performance" in sources:
            return "SUPPLY"

        if "shipment_evaluation" in sources:
            return "LOGISTICS"

        if "financial_baseline" in sources:
            return "ECONOMICS"

        if "forecast" in sources:
            return "FORECASTING"

        return "GENERAL"

    @classmethod
    def _add_insufficiency_claim(
        cls,
        result: DeterministicReasoningResult,
        *,
        statement: str,
        category: str,
        missing_evidence: List[str],
    ) -> None:
        """
        Adds a deterministic explanation of why the requested
        business conclusion cannot currently be established.

        This is intentionally a blocked claim:
        - supported=False because the business conclusion itself
          is not established;
        - allowable_in_answer=True because explaining the limitation
          is itself safe and useful;
        - confidence=0 because there is no positive evidence for
          the requested conclusion.
        """
        cls._add_claim(
            result=result,
            statement=statement,
            category=category,
            confidence=0.0,
            evidence_refs=[],
            missing_evidence=missing_evidence,
            supported=False,
            allowable_in_answer=True,
            severity="INFO",
        )

    @classmethod
    def _add_claim(
        cls,
        result: DeterministicReasoningResult,
        *,
        statement: str,
        category: str,
        confidence: float,
        evidence_refs: Optional[List[str]] = None,
        missing_evidence: Optional[List[str]] = None,
        supported: bool = True,
        allowable_in_answer: bool = True,
        impact: Optional[str] = None,
        severity: str = "INFO",
    ) -> None:
        result.claims.append(
            DeterministicClaim(
                statement=statement,
                category=category,
                confidence=max(
                    0.0,
                    min(1.0, float(confidence)),
                ),
                evidence_refs=list(
                    evidence_refs or []
                ),
                missing_evidence=list(
                    missing_evidence or []
                ),
                supported=supported,
                allowable_in_answer=allowable_in_answer,
                impact=impact,
                severity=severity,
            )
        )

    @staticmethod
    def _claim_confidence(
        *,
        direct: float = 0.0,
        derived: float = 0.0,
        missing_count: int = 0,
        conflict_count: int = 0,
    ) -> float:
        score = max(direct, derived)

        score -= min(
            0.20,
            missing_count * 0.025,
        )

        score -= min(
            0.25,
            conflict_count * 0.10,
        )

        return round(
            max(0.0, min(0.99, score)),
            3,
        )

    @classmethod
    def _reason_inventory(
        cls,
        fused: FusedEvidence,
        result: DeterministicReasoningResult,
    ) -> None:
        on_hand = cls._get(
            fused,
            "inventory_position.on_hand",
        )
        safety_stock = cls._get(
            fused,
            "inventory_position.safety_stock",
        )
        on_order = cls._get(
            fused,
            "inventory_position.on_order",
        )

        safety_delta = cls._get(
            fused,
            "inventory.safety_stock_delta",
        )

        coverage_pct = cls._get(
            fused,
            "inventory.safety_stock_coverage_pct",
        )

        runway_days = cls._get(
            fused,
            "inventory.on_hand_runway_days",
        )

        if (
            isinstance(on_hand, (int, float))
            and isinstance(safety_stock, (int, float))
        ):
            refs = [
                cls._fact_ref(
                    fused,
                    "inventory_position",
                    "on_hand",
                ),
                cls._fact_ref(
                    fused,
                    "inventory_position",
                    "safety_stock",
                ),
            ]

            if float(on_hand) < float(safety_stock):
                severity = "HIGH"

                result.findings.append(
                    ReasoningFinding(
                        category="INVENTORY_RISK",
                        title="Inventory is below safety stock",
                        explanation=(
                            f"On-hand inventory is {on_hand:g} units "
                            f"versus {safety_stock:g} units of safety stock, "
                            f"a deficit of "
                            f"{abs(float(safety_delta or 0)):g} units."
                        ),
                        severity=severity,
                        evidence_refs=refs,
                    )
                )

                result.confirmed_conclusions.append(
                    "Current on-hand inventory is below the configured safety-stock level."
                )

                cls._add_claim(
                    result,
                    statement=(
                        "Current on-hand inventory is below the configured safety-stock level."
                    ),
                    category="INVENTORY_STATE",
                    confidence=cls._claim_confidence(
                        direct=0.99,
                        missing_count=0,
                        conflict_count=len(
                            fused.conflicts
                        ),
                    ),
                    evidence_refs=[
                        "inventory_position.on_hand",
                        "inventory_position.safety_stock",
                    ],
                    severity="HIGH",
                    impact="Immediate inventory protection risk.",
                )

                if (
                    isinstance(coverage_pct, (int, float))
                    and float(coverage_pct) < 100.0
                ):
                    cls._add_claim(
                        result,
                        statement=(
                            f"On-hand inventory covers "
                            f"{float(coverage_pct):.1f}% of the configured "
                            "safety-stock requirement."
                        ),
                        category="INVENTORY_PROTECTION",
                        confidence=cls._claim_confidence(
                            direct=0.98,
                            missing_count=0,
                            conflict_count=len(
                                fused.conflicts
                            ),
                        ),
                        evidence_refs=[
                            "inventory_position.on_hand",
                            "inventory_position.safety_stock",
                            "inventory.safety_stock_coverage_pct",
                        ],
                        severity="HIGH",
                        impact="Inventory protection is below target.",
                    )

                    result.findings.append(
                        ReasoningFinding(
                            category="INVENTORY_PROTECTION",
                            title="Inventory protection is below target",
                            explanation=(
                                f"On-hand inventory covers "
                                f"{float(coverage_pct):.1f}% "
                                "of the configured safety-stock requirement."
                            ),
                            severity="HIGH",
                            evidence_refs=[
                                "inventory.safety_stock_coverage_pct"
                            ],
                        )
                    )

            else:
                result.findings.append(
                    ReasoningFinding(
                        category="INVENTORY_STATUS",
                        title="Inventory is at or above safety stock",
                        explanation=(
                            f"On-hand inventory is {on_hand:g} units "
                            f"against {safety_stock:g} units of safety stock."
                        ),
                        severity="INFO",
                        evidence_refs=refs,
                    )
                )

                result.confirmed_conclusions.append(
                    "Current on-hand inventory meets or exceeds the configured safety-stock level."
                )

        if (
            isinstance(on_hand, (int, float))
            and isinstance(on_order, (int, float))
        ):
            gross_available = cls._get(
                fused,
                "inventory.total_available_plus_inbound",
            )

            result.findings.append(
                ReasoningFinding(
                    category="INBOUND_COVERAGE",
                    title="Inbound inventory is material to total availability",
                    explanation=(
                        f"There are {on_order:g} units on order. "
                        f"Current on-hand plus inbound quantity is "
                        f"{float(gross_available):g} units."
                        if isinstance(gross_available, (int, float))
                        else (
                            f"There are {on_order:g} units on order."
                        )
                    ),
                    severity="INFO",
                    evidence_refs=[
                        "inventory_position.on_order",
                        "inventory.total_available_plus_inbound",
                    ],
                )
            )

        if isinstance(runway_days, (int, float)):
            result.findings.append(
                ReasoningFinding(
                    category="INVENTORY_RUNWAY",
                    title="Deterministic on-hand runway is available",
                    explanation=(
                        f"Current on-hand inventory represents "
                        f"approximately {float(runway_days):.1f} days "
                        "of coverage at the configured expected daily demand."
                    ),
                    severity=(
                        "HIGH"
                        if float(runway_days) < 7
                        else "MEDIUM"
                        if float(runway_days) < 14
                        else "INFO"
                    ),
                    evidence_refs=[
                        "inventory.on_hand_runway_days"
                    ],
                )
            )

            result.confirmed_conclusions.append(
                "A deterministic on-hand runway can be calculated from the available replenishment demand assumption."
            )

        missing = set(fused.unavailable_sources)

        if "forecast" in missing:
            statement = (
                "An exact future stockout date cannot be established "
                "from the currently available evidence."
            )

            result.unsupported_conclusions.append(
                "Exact future stockout date cannot be established without forecast or demand evidence."
            )

            cls._add_claim(
                result,
                statement=statement,
                category="FUTURE_RISK_LIMITATION",
                confidence=0.0,
                evidence_refs=[],
                missing_evidence=["forecast"],
                supported=False,
                allowable_in_answer=False,
                severity="INFO",
            )

        if "replenishment_policy" in missing:
            result.unsupported_conclusions.append(
                "Replenishment adequacy cannot be fully assessed without the replenishment policy."
            )

        if "inventory_transactions" in missing:
            result.unsupported_conclusions.append(
                "Recent consumption acceleration cannot be confirmed without inventory transaction history."
            )

        if "order_lines" in missing and "orders" not in missing:
            result.unsupported_conclusions.append(
                "Order-level demand detail is incomplete because order-line evidence is unavailable."
            )

        if (
            "replenishment_policy" in missing
            or "forecast" in missing
        ):
            result.recommendations.append(
                ReasoningRecommendation(
                    priority="HIGH",
                    action=(
                        "Review replenishment coverage and demand outlook "
                        "before committing an expedite, allocation, or "
                        "purchase-order change."
                    ),
                    rationale=(
                        "The inventory position is below protection level, "
                        "but the evidence set does not establish the exact "
                        "future stockout timeline."
                    ),
                    evidence_refs=[
                        "inventory_position.on_hand",
                        "inventory_position.safety_stock",
                    ],
                    blocked_by=[
                        source
                        for source in (
                            "replenishment_policy",
                            "forecast",
                        )
                        if source in missing
                    ],
                )
            )

            cls._add_claim(
                result,
                statement=(
                    "An expedite, allocation, or purchase-order change "
                    "should not be committed until replenishment coverage "
                    "and demand outlook are validated."
                ),
                category="RECOMMENDATION_GUARDRAIL",
                confidence=0.90,
                evidence_refs=[
                    "inventory_position.on_hand",
                    "inventory_position.safety_stock",
                    "inventory_position.on_order",
                ],
                missing_evidence=[
                    source
                    for source in (
                        "replenishment_policy",
                        "forecast",
                    )
                    if source in missing
                ],
                severity="HIGH",
                impact="Avoids premature operational intervention.",
            )

        result.state = (
            "AT_RISK"
            if any(
                finding.severity == "HIGH"
                for finding in result.findings
            )
            else "STABLE"
        )

    @classmethod
    def _reason_supplier(
        cls,
        fused: FusedEvidence,
        result: DeterministicReasoningResult,
    ) -> None:
        otif = cls._get(
            fused,
            "supplier.service_coverage_pct",
        )
        risk_score = cls._get(
            fused,
            "supplier_performance.risk_score",
        )
        risk_band = cls._get(
            fused,
            "supplier.risk_band",
        )
        lead_time = cls._get(
            fused,
            "supplier_performance.mean_lead_time_days",
        )

        if isinstance(otif, (int, float)):
            result.findings.append(
                ReasoningFinding(
                    category="SUPPLIER_SERVICE",
                    title="Supplier service performance",
                    explanation=(
                        f"Observed OTIF performance is "
                        f"{float(otif):.1f}%."
                    ),
                    severity=(
                        "HIGH"
                        if float(otif) < 85
                        else "MEDIUM"
                        if float(otif) < 95
                        else "INFO"
                    ),
                    evidence_refs=[
                        "supplier_performance.otif_rate"
                    ],
                )
            )

            result.confirmed_conclusions.append(
                "Supplier service performance is supported by authoritative supplier-performance evidence."
            )

        if isinstance(risk_score, (int, float)):
            result.findings.append(
                ReasoningFinding(
                    category="SUPPLIER_RISK",
                    title="Supplier risk score",
                    explanation=(
                        f"The supplier risk score is "
                        f"{float(risk_score):.1f}, "
                        f"which maps to the {risk_band or 'UNKNOWN'} risk band."
                    ),
                    severity=(
                        str(risk_band)
                        if risk_band in {
                            "HIGH",
                            "MEDIUM",
                            "LOW",
                        }
                        else "INFO"
                    ),
                    evidence_refs=[
                        "supplier_performance.risk_score"
                    ],
                )
            )

        if isinstance(lead_time, (int, float)):
            result.findings.append(
                ReasoningFinding(
                    category="SUPPLIER_LEAD_TIME",
                    title="Supplier lead time",
                    explanation=(
                        f"Mean supplier lead time is "
                        f"{float(lead_time):.1f} days."
                    ),
                    severity="INFO",
                    evidence_refs=[
                        "supplier_performance.mean_lead_time_days"
                    ],
                )
            )

        if risk_band in {"HIGH", "MEDIUM"}:
            result.state = "AT_RISK"

            result.recommendations.append(
                ReasoningRecommendation(
                    priority="HIGH" if risk_band == "HIGH" else "MEDIUM",
                    action=(
                        "Review supplier allocation, service recovery "
                        "options, and alternate qualified supply coverage."
                    ),
                    rationale=(
                        f"Deterministic supplier evidence indicates "
                        f"{risk_band.lower()} risk."
                    ),
                    evidence_refs=[
                        "supplier_performance.risk_score",
                        "supplier_performance.otif_rate",
                    ],
                )
            )
        else:
            result.state = "STABLE"

        if "supplier_performance" in fused.unavailable_sources:
            result.unsupported_conclusions.append(
                "Supplier reliability cannot be established without supplier-performance evidence."
            )

    @classmethod
    def _reason_logistics(
        cls,
        fused: FusedEvidence,
        result: DeterministicReasoningResult,
    ) -> None:
        delay_hours = cls._get(
            fused,
            "shipment_evaluation.delay_hours",
        )
        status = cls._get(
            fused,
            "logistics.delivery_status",
        )
        eta = cls._get(
            fused,
            "shipment_evaluation.estimated_delivery_date",
        )

        if isinstance(delay_hours, (int, float)):
            delayed = float(delay_hours) > 0

            result.findings.append(
                ReasoningFinding(
                    category="LOGISTICS_DELAY",
                    title=(
                        "Shipment is delayed"
                        if delayed
                        else "No recorded shipment delay"
                    ),
                    explanation=(
                        f"Recorded delay is "
                        f"{float(delay_hours) / 24.0:.2f} days."
                        if delayed
                        else "Recorded delay is zero hours."
                    ),
                    severity=(
                        "HIGH"
                        if float(delay_hours) > 48
                        else "MEDIUM"
                        if delayed
                        else "INFO"
                    ),
                    evidence_refs=[
                        "shipment_evaluation.delay_hours"
                    ],
                )
            )

            if delayed:
                result.state = "AT_RISK"
                result.confirmed_conclusions.append(
                    "A shipment delay is supported by the available logistics evaluation."
                )

        if status:
            result.confirmed_conclusions.append(
                f"Shipment delivery status is {status}."
            )

        if eta:
            result.findings.append(
                ReasoningFinding(
                    category="LOGISTICS_ETA",
                    title="Estimated delivery date available",
                    explanation=(
                        f"Recorded estimated delivery date: {eta}."
                    ),
                    severity="INFO",
                    evidence_refs=[
                        "shipment_evaluation.estimated_delivery_date"
                    ],
                )
            )
        elif "shipment_evaluation" in fused.unavailable_sources:
            result.unsupported_conclusions.append(
                "A deterministic ETA cannot be established because shipment evaluation evidence is unavailable."
            )

    @classmethod
    def _reason_finance(
        cls,
        fused: FusedEvidence,
        result: DeterministicReasoningResult,
    ) -> None:
        holding = cls._get(
            fused,
            "economics.holding_cost_exposure",
        )

        if isinstance(holding, (int, float)):
            result.findings.append(
                ReasoningFinding(
                    category="FINANCIAL_EXPOSURE",
                    title="Holding-cost exposure identified",
                    explanation=(
                        f"Observed holding-cost exposure is "
                        f"{float(holding):,.2f}."
                    ),
                    severity=(
                        "HIGH"
                        if float(holding) > 100000
                        else "MEDIUM"
                        if float(holding) > 25000
                        else "INFO"
                    ),
                    evidence_refs=[
                        "replenishment_policy.holding_cost_exposure"
                    ],
                )
            )

            result.confirmed_conclusions.append(
                "Financial exposure is supported by persisted cost evidence."
            )

    @classmethod
    def _reason_generic(
        cls,
        fused: FusedEvidence,
        result: DeterministicReasoningResult,
    ) -> None:
        if fused.facts:
            result.state = "OBSERVED"

            result.findings.append(
                ReasoningFinding(
                    category="OBSERVATION",
                    title="Authoritative evidence is available",
                    explanation=(
                        f"AURIX has {len(fused.facts)} "
                        "authoritative facts available for deterministic analysis."
                    ),
                    severity="INFO",
                )
            )

            result.confirmed_conclusions.append(
                "AURIX can answer from the available authoritative evidence."
            )
        else:
            result.state = "INSUFFICIENT_EVIDENCE"
            result.unsupported_conclusions.append(
                "No authoritative evidence is available to support a deterministic conclusion."
            )

    @classmethod
    def _apply_intent_constraints(
        cls,
        *,
        fused: FusedEvidence,
        result: DeterministicReasoningResult,
        intent: Optional[str],
    ) -> None:
        intent_upper = (
            str(intent).upper()
            if intent
            else ""
        )

        if intent_upper == "RECOMMEND":
            if not result.recommendations:
                result.recommendations.append(
                    ReasoningRecommendation(
                        priority="MEDIUM",
                        action=(
                            "Review the highest-severity confirmed finding "
                            "and address missing evidence before taking a "
                            "material operational action."
                        ),
                        rationale=(
                            "A deterministic recommendation must remain "
                            "evidence-bound."
                        ),
                        evidence_refs=[
                            finding.evidence_refs[0]
                            for finding in result.findings
                            if finding.evidence_refs
                        ],
                        blocked_by=list(
                            fused.unavailable_sources
                        ),
                    )
                )

        if intent_upper == "COMPARE":
            if len(result.findings) < 2:
                result.unsupported_conclusions.append(
                    "A robust deterministic comparison requires evidence for at least two comparable entities."
                )

    @classmethod
    def _calculate_escalation(
        cls,
        *,
        fused: FusedEvidence,
        result: DeterministicReasoningResult,
    ) -> None:
        severe_conflicts = len(fused.conflicts) >= 2
        almost_no_evidence = len(fused.facts) == 0

        high_value_question_with_gaps = (
            result.business_domain in {
                "INVENTORY",
                "SUPPLY",
                "LOGISTICS",
                "ECONOMICS",
            }
            and len(result.unsupported_conclusions) >= 2
            and len(fused.facts) < 5
        )

        if severe_conflicts:
            result.escalation_recommended = True
            result.escalation_reason = (
                "Multiple authoritative evidence conflicts prevent a reliable deterministic conclusion."
            )
            result.confidence = 0.45
            return

        if almost_no_evidence:
            result.escalation_recommended = True
            result.escalation_reason = (
                "No authoritative evidence is available for deterministic reasoning."
            )
            result.confidence = 0.0
            return

        if high_value_question_with_gaps:
            result.escalation_recommended = True
            result.escalation_reason = (
                "The question is business-relevant but deterministic evidence coverage is insufficient."
            )
            result.confidence = round(
                min(0.69, max(0.40, fused.confidence)),
                3,
            )
            return

        result.escalation_recommended = False
        result.escalation_reason = None

        # Claim-aware confidence:
        # unsupported/non-allowable claims must not mathematically destroy
        # confidence in independently supported present-state conclusions.
        supported_claims = [
            claim
            for claim in result.claims
            if claim.supported and claim.allowable_in_answer
        ]

        if supported_claims:
            weighted_sum = 0.0
            weight_total = 0.0

            for claim in supported_claims:
                category = claim.category.upper()

                if category in {
                    "INVENTORY_STATE",
                    "SUPPLIER_SERVICE",
                    "LOGISTICS_DELAY",
                    "LOGISTICS_ETA",
                    "FINANCIAL_EXPOSURE",
                }:
                    weight = 1.40
                elif category in {
                    "INVENTORY_PROTECTION",
                    "INBOUND_COVERAGE",
                    "SUPPLIER_RISK",
                    "SUPPLIER_LEAD_TIME",
                    "INVENTORY_RUNWAY",
                }:
                    weight = 1.20
                elif category == "RECOMMENDATION_GUARDRAIL":
                    weight = 0.90
                else:
                    weight = 1.00

                weighted_sum += (
                    float(claim.confidence) * weight
                )
                weight_total += weight

            base_confidence = (
                weighted_sum / weight_total
                if weight_total > 0
                else fused.confidence
            )

            # Missing evidence reduces certainty moderately, rather than
            # treating every unavailable source as a failed answer.
            missing_count = len(fused.unavailable_sources)

            completeness_penalty = min(
                0.10,
                missing_count * 0.0125,
            )

            conflict_penalty = min(
                0.12,
                len(fused.conflicts) * 0.04,
            )

            result.confidence = round(
                max(
                    0.55,
                    min(
                        0.99,
                        base_confidence
                        - completeness_penalty
                        - conflict_penalty,
                    ),
                ),
                3,
            )

            return

        # Fallback for legacy reasoning results with no claims yet.
        result.confidence = round(
            max(
                0.0,
                min(
                    0.99,
                    float(fused.confidence),
                ),
            ),
            3,
        )


__all__ = [
    "ReasoningFinding",
    "ReasoningRecommendation",
    "DeterministicReasoningResult",
    "DeterministicReasoningEngine",
]
