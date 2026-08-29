"""
AURIX Deterministic Causal Reasoning Engine.

Builds evidence-supported cause/effect relationships from the
FusedEvidence produced by the deterministic Evidence Fusion layer.

Strict rule:
Two correlated observations are NOT automatically treated as causal.

A causal relationship requires supporting evidence that connects
the driver to the observed business condition.

The engine intentionally produces structured causal relationships
rather than free-form prose.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from aurix_core.intelligence.decision_gate import (
    DeterministicDecisionGate,
)
from aurix_core.intelligence.evidence_fusion import (
    FusedEvidence,
)


@dataclass
class CausalLink:
    driver: str
    effect: str
    relationship: str
    strength: float

    evidence_refs: List[str] = field(default_factory=list)
    missing_evidence: List[str] = field(default_factory=list)

    causal_supported: bool = False
    allowable_in_answer: bool = False


@dataclass
class CausalFinding:
    category: str
    title: str
    explanation: str
    severity: str = "INFO"

    causal_links: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)


@dataclass
class CausalReasoningResult:
    query: str
    entity_id: Optional[str]

    primary_driver: Optional[str] = None
    secondary_drivers: List[str] = field(
        default_factory=list
    )

    causal_links: List[CausalLink] = field(
        default_factory=list
    )

    findings: List[CausalFinding] = field(
        default_factory=list
    )

    confirmed_causal_conclusions: List[str] = field(
        default_factory=list
    )

    rejected_causal_conclusions: List[str] = field(
        default_factory=list
    )

    decision_blockers: List[str] = field(
        default_factory=list
    )

    decision_gates: Dict[str, Any] = field(
        default_factory=dict
    )

    confidence: float = 0.0
    causal_quality: str = "NONE"

    provenance: Dict[str, Any] = field(
        default_factory=dict
    )


class DeterministicCausalEngine:
    """
    Deterministic causal reasoning over fused evidence.

    The engine distinguishes four levels:

    1. DIRECT
       A fact directly establishes the condition.

    2. DERIVED
       A deterministic calculation establishes a relationship.

    3. CORROBORATED_CAUSAL
       Multiple evidence sources establish a directional relationship.

    4. UNSUPPORTED
       The available evidence is insufficient to state causality.
    """

    @classmethod
    def reason(
        cls,
        fused: FusedEvidence,
        *,
        business_domain: Optional[str] = None,
    ) -> CausalReasoningResult:

        result = CausalReasoningResult(
            query=fused.query,
            entity_id=fused.entity_id,
        )

        domain = (
            business_domain.upper()
            if business_domain
            else cls._infer_domain(fused)
        )

        cls._inventory_causality(
            fused,
            result,
            domain,
        )

        cls._supplier_inventory_causality(
            fused,
            result,
            domain,
        )

        cls._shipment_inventory_causality(
            fused,
            result,
            domain,
        )

        cls._demand_inventory_causality(
            fused,
            result,
            domain,
        )

        cls._financial_causality(
            fused,
            result,
            domain,
        )

        cls._identify_primary_driver(
            result
        )

        cls._evaluate_decision_gates(
            fused,
            result,
            domain,
        )

        cls._identify_decision_blockers(
            fused,
            result,
            domain,
        )

        cls._score_result(
            fused,
            result,
        )

        result.provenance = {
            "causal_engine": (
                "deterministic-causal-engine-v1"
            ),
            "answer_source": "AURIX_ENGINE",
            "tenant_id": fused.tenant_id,
            "entity_id": fused.entity_id,
            "business_domain": domain,
            "causal_links": len(
                result.causal_links
            ),
            "confirmed_causal_conclusions": len(
                result.confirmed_causal_conclusions
            ),
            "rejected_causal_conclusions": len(
                result.rejected_causal_conclusions
            ),
            "decision_blockers": len(
                result.decision_blockers
            ),
            "decision_gates": list(
                result.decision_gates.keys()
            ),
        }

        return result

    # ------------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _infer_domain(
        fused: FusedEvidence,
    ) -> str:
        sources = set(
            fused.available_sources
        )

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

    @staticmethod
    def _get(
        fused: FusedEvidence,
        key: str,
    ) -> Any:
        for fact in reversed(
            fused.facts
        ):
            if fact.key == key:
                return fact.value

        for derived in reversed(
            fused.derived_facts
        ):
            if derived.key == key:
                return derived.value

        return None

    @staticmethod
    def _available(
        fused: FusedEvidence,
        source: str,
    ) -> bool:
        return source in fused.available_sources

    @staticmethod
    def _add_link(
        result: CausalReasoningResult,
        *,
        driver: str,
        effect: str,
        relationship: str,
        strength: float,
        evidence_refs: Optional[List[str]] = None,
        missing_evidence: Optional[List[str]] = None,
        causal_supported: bool = False,
        allowable_in_answer: bool = False,
    ) -> None:
        result.causal_links.append(
            CausalLink(
                driver=driver,
                effect=effect,
                relationship=relationship,
                strength=max(
                    0.0,
                    min(1.0, float(strength)),
                ),
                evidence_refs=list(
                    evidence_refs or []
                ),
                missing_evidence=list(
                    missing_evidence or []
                ),
                causal_supported=(
                    causal_supported
                ),
                allowable_in_answer=(
                    allowable_in_answer
                ),
            )
        )

    # ------------------------------------------------------------------
    # Inventory causality
    # ------------------------------------------------------------------

    @classmethod
    def _inventory_causality(
        cls,
        fused: FusedEvidence,
        result: CausalReasoningResult,
        domain: str,
    ) -> None:
        if not cls._available(
            fused,
            "inventory_position",
        ):
            return

        on_hand = cls._get(
            fused,
            "inventory_position.on_hand",
        )

        safety_stock = cls._get(
            fused,
            "inventory_position.safety_stock",
        )

        coverage = cls._get(
            fused,
            "inventory.safety_stock_coverage_pct",
        )

        if not (
            isinstance(on_hand, (int, float))
            and isinstance(
                safety_stock,
                (int, float),
            )
        ):
            return

        below_safety = (
            float(on_hand)
            < float(safety_stock)
        )

        if below_safety:
            result.findings.append(
                CausalFinding(
                    category="INVENTORY_PROTECTION",
                    title=(
                        "Inventory protection breach "
                        "is directly observed"
                    ),
                    explanation=(
                        f"On-hand inventory of "
                        f"{float(on_hand):g} units is "
                        f"below safety stock of "
                        f"{float(safety_stock):g} units."
                    ),
                    severity="HIGH",
                    evidence_refs=[
                        "inventory_position.on_hand",
                        "inventory_position.safety_stock",
                    ],
                )
            )

            cls._add_link(
                result,
                driver=(
                    "On-hand inventory is below "
                    "configured safety stock."
                ),
                effect=(
                    "Inventory protection is below "
                    "target."
                ),
                relationship="DIRECT_THRESHOLD_BREACH",
                strength=0.99,
                evidence_refs=[
                    "inventory_position.on_hand",
                    "inventory_position.safety_stock",
                    "inventory.safety_stock_coverage_pct",
                ],
                causal_supported=True,
                allowable_in_answer=True,
            )

            result.confirmed_causal_conclusions.append(
                "The current inventory-protection breach is directly supported by authoritative inventory evidence."
            )

        if (
            isinstance(coverage, (int, float))
            and float(coverage) < 100.0
        ):
            cls._add_link(
                result,
                driver=(
                    "On-hand inventory provides less "
                    "than 100% of safety-stock requirement."
                ),
                effect=(
                    "Protection buffer is below "
                    "configured target."
                ),
                relationship="DETERMINISTIC_COVERAGE_RELATIONSHIP",
                strength=0.99,
                evidence_refs=[
                    "inventory.safety_stock_coverage_pct"
                ],
                causal_supported=True,
                allowable_in_answer=True,
            )

    # ------------------------------------------------------------------
    # Supplier -> inventory causality
    # ------------------------------------------------------------------

    @classmethod
    def _supplier_inventory_causality(
        cls,
        fused: FusedEvidence,
        result: CausalReasoningResult,
        domain: str,
    ) -> None:
        has_supplier = cls._available(
            fused,
            "supplier_performance",
        )

        if not has_supplier:
            return

        otif = cls._get(
            fused,
            "supplier.service_coverage_pct",
        )

        risk_score = cls._get(
            fused,
            "supplier_performance.risk_score",
        )

        inventory_risk = (
            cls._get(
                fused,
                "inventory.safety_stock_coverage_pct",
            )
            if cls._available(
                fused,
                "inventory_position",
            )
            else None
        )

        if not (
            isinstance(otif, (int, float))
            or isinstance(
                risk_score,
                (int, float),
            )
        ):
            return

        supplier_weak = (
            (
                isinstance(
                    otif,
                    (int, float),
                )
                and float(otif) < 90.0
            )
            or (
                isinstance(
                    risk_score,
                    (int, float),
                )
                and float(risk_score) >= 50.0
            )
        )

        if not supplier_weak:
            return

        if (
            isinstance(
                inventory_risk,
                (int, float),
            )
            and float(inventory_risk) < 100.0
        ):
            # Important: poor supplier performance plus low inventory
            # is still NOT enough to claim causality.
            missing = [
                source
                for source in (
                    "purchase_orders",
                    "shipments",
                    "shipment_evaluation",
                )
                if source
                in fused.unavailable_sources
            ]

            if not missing:
                cls._add_link(
                    result,
                    driver=(
                        "Supplier service performance "
                        "is below acceptable level."
                    ),
                    effect=(
                        "Inventory protection is "
                        "deteriorating."
                    ),
                    relationship=(
                        "CORROBORATED_SUPPLY_TO_INVENTORY"
                    ),
                    strength=0.88,
                    evidence_refs=[
                        "supplier_performance.otif_rate",
                        "supplier_performance.risk_score",
                        "inventory.safety_stock_coverage_pct",
                    ],
                    causal_supported=True,
                    allowable_in_answer=True,
                )

                result.confirmed_causal_conclusions.append(
                    "Supplier performance is supported as a contributor to the inventory condition."
                )

            else:
                cls._add_link(
                    result,
                    driver=(
                        "Supplier service performance "
                        "is below acceptable level."
                    ),
                    effect=(
                        "Inventory protection may be "
                        "affected."
                    ),
                    relationship="POTENTIAL_SUPPLY_DRIVER",
                    strength=0.55,
                    evidence_refs=[
                        "supplier_performance.otif_rate",
                        "supplier_performance.risk_score",
                        "inventory.safety_stock_coverage_pct",
                    ],
                    missing_evidence=missing,
                    causal_supported=False,
                    allowable_in_answer=False,
                )

                result.rejected_causal_conclusions.append(
                    "Supplier underperformance cannot currently be stated as the cause of the inventory shortage because transaction-level supply linkage is unavailable."
                )

    # ------------------------------------------------------------------
    # Shipment -> inventory causality
    # ------------------------------------------------------------------

    @classmethod
    def _shipment_inventory_causality(
        cls,
        fused: FusedEvidence,
        result: CausalReasoningResult,
        domain: str,
    ) -> None:
        if not cls._available(
            fused,
            "shipment_evaluation",
        ):
            return

        delay_hours = cls._get(
            fused,
            "shipment_evaluation.delay_hours",
        )

        delayed = (
            isinstance(
                delay_hours,
                (int, float),
            )
            and float(delay_hours) > 0
        )

        if not delayed:
            return

        inventory_coverage = cls._get(
            fused,
            "inventory.safety_stock_coverage_pct",
        )

        if not (
            isinstance(
                inventory_coverage,
                (int, float),
            )
            and float(inventory_coverage) < 100.0
        ):
            return

        missing = [
            source
            for source in (
                "shipments",
                "orders",
            )
            if source
            in fused.unavailable_sources
        ]

        if not missing:
            cls._add_link(
                result,
                driver=(
                    "Inbound shipment is delayed."
                ),
                effect=(
                    "Inventory protection is "
                    "under pressure."
                ),
                relationship=(
                    "CORROBORATED_INBOUND_DELAY"
                ),
                strength=0.90,
                evidence_refs=[
                    "shipment_evaluation.delay_hours",
                    "inventory.safety_stock_coverage_pct",
                ],
                causal_supported=True,
                allowable_in_answer=True,
            )

            result.confirmed_causal_conclusions.append(
                "Inbound shipment delay is supported as a contributor to the inventory risk."
            )

        else:
            cls._add_link(
                result,
                driver=(
                    "Inbound shipment is delayed."
                ),
                effect=(
                    "Inventory protection may be "
                    "under pressure."
                ),
                relationship="POTENTIAL_INBOUND_DELAY",
                strength=0.58,
                evidence_refs=[
                    "shipment_evaluation.delay_hours",
                    "inventory.safety_stock_coverage_pct",
                ],
                missing_evidence=missing,
                causal_supported=False,
                allowable_in_answer=False,
            )

            result.rejected_causal_conclusions.append(
                "Shipment delay cannot be stated as a confirmed cause of the inventory shortage without an established inbound-to-inventory linkage."
            )

    # ------------------------------------------------------------------
    # Demand -> inventory causality
    # ------------------------------------------------------------------

    @classmethod
    def _demand_inventory_causality(
        cls,
        fused: FusedEvidence,
        result: CausalReasoningResult,
        domain: str,
    ) -> None:
        demand = cls._get(
            fused,
            "replenishment_policy.expected_daily_demand",
        )

        forecast_points_available = cls._available(
            fused,
            "forecast",
        )

        if (
            isinstance(demand, (int, float))
            and float(demand) > 0
            and cls._available(
                fused,
                "inventory_position",
            )
        ):
            runway = cls._get(
                fused,
                "inventory.on_hand_runway_days",
            )

            if isinstance(
                runway,
                (int, float),
            ):
                cls._add_link(
                    result,
                    driver=(
                        "Configured expected daily demand "
                        "consumes available on-hand inventory."
                    ),
                    effect=(
                        "A finite deterministic on-hand "
                        "runway exists."
                    ),
                    relationship=(
                        "DETERMINISTIC_DEMAND_COVERAGE"
                    ),
                    strength=0.94,
                    evidence_refs=[
                        "replenishment_policy.expected_daily_demand",
                        "inventory_position.on_hand",
                        "inventory.on_hand_runway_days",
                    ],
                    causal_supported=True,
                    allowable_in_answer=True,
                )

                result.confirmed_causal_conclusions.append(
                    "Expected daily demand can be deterministically related to current on-hand coverage."
                )

        if not forecast_points_available:
            result.rejected_causal_conclusions.append(
                "Future demand growth or acceleration cannot be stated as a cause without forecast evidence."
            )

    # ------------------------------------------------------------------
    # Financial causality
    # ------------------------------------------------------------------

    @classmethod
    def _financial_causality(
        cls,
        fused: FusedEvidence,
        result: CausalReasoningResult,
        domain: str,
    ) -> None:
        holding = cls._get(
            fused,
            "economics.holding_cost_exposure",
        )

        on_order = cls._get(
            fused,
            "inventory_position.on_order",
        )

        if not (
            isinstance(
                holding,
                (int, float),
            )
            or isinstance(
                on_order,
                (int, float),
            )
        ):
            return

        if (
            isinstance(
                holding,
                (int, float),
            )
            and isinstance(
                on_order,
                (int, float),
            )
            and float(on_order) > 0
        ):
            cls._add_link(
                result,
                driver=(
                    "Material inbound inventory exists "
                    "while holding-cost exposure is present."
                ),
                effect=(
                    "Additional supply can have working-capital "
                    "implications."
                ),
                relationship=(
                    "INBOUND_TO_WORKING_CAPITAL"
                ),
                strength=0.82,
                evidence_refs=[
                    "inventory_position.on_order",
                    "economics.holding_cost_exposure",
                ],
                causal_supported=True,
                allowable_in_answer=True,
            )

            result.confirmed_causal_conclusions.append(
                "Inbound inventory has a deterministic working-capital implication when holding-cost exposure is available."
            )

    # ------------------------------------------------------------------
    # Primary driver selection
    # ------------------------------------------------------------------

    @classmethod
    def _identify_primary_driver(
        cls,
        result: CausalReasoningResult,
    ) -> None:
        valid_links = [
            link
            for link in result.causal_links
            if link.causal_supported
        ]

        if not valid_links:
            return

        priority = {
            "DIRECT_THRESHOLD_BREACH": 100,
            "CORROBORATED_INBOUND_DELAY": 88,
            "CORROBORATED_SUPPLY_TO_INVENTORY": 85,
            "DETERMINISTIC_DEMAND_COVERAGE": 80,
            "INBOUND_TO_WORKING_CAPITAL": 60,
        }

        # Deterministic coverage relationships describe/support the
        # primary condition; they are not separate causal drivers.
        driver_links = [
            link
            for link in valid_links
            if link.relationship
            not in {
                "DETERMINISTIC_COVERAGE_RELATIONSHIP",
            }
        ]

        if not driver_links:
            driver_links = valid_links

        driver_links.sort(
            key=lambda link: (
                priority.get(
                    link.relationship,
                    50,
                ),
                link.strength,
            ),
            reverse=True,
        )

        result.primary_driver = (
            driver_links[0].driver
        )

        seen = set()

        for link in driver_links[1:]:
            if link.driver in seen:
                continue

            # Do not classify an evidence expression of the primary
            # condition as a secondary driver.
            if (
                "less than 100%" in link.driver.lower()
                or "below configured safety stock" in link.driver.lower()
                and result.primary_driver
                and "below configured safety stock"
                in result.primary_driver.lower()
            ):
                continue

            result.secondary_drivers.append(
                link.driver
            )
            seen.add(link.driver)

    # ------------------------------------------------------------------
    # Decision gate evaluation
    # ------------------------------------------------------------------

    @classmethod
    def _evaluate_decision_gates(
        cls,
        fused: FusedEvidence,
        result: CausalReasoningResult,
        domain: str,
    ) -> None:
        decisions: List[str] = []

        if domain == "INVENTORY":
            decisions.extend(
                [
                    "INVENTORY_STATUS",
                    "INVENTORY_PROTECTION",
                    "STOCKOUT_FORECAST",
                    "REPLENISHMENT_ADEQUACY",
                    "EXPEDITE_DECISION",
                    "SUPPLIER_CAUSALITY",
                    "SHIPMENT_CAUSALITY",
                    "DEMAND_CAUSALITY",
                    "WORKING_CAPITAL",
                ]
            )

        elif domain == "SUPPLY":
            decisions.extend(
                [
                    "SUPPLIER_CAUSALITY",
                ]
            )

        elif domain == "LOGISTICS":
            decisions.extend(
                [
                    "SHIPMENT_CAUSALITY",
                ]
            )

        elif domain == "ECONOMICS":
            decisions.extend(
                [
                    "WORKING_CAPITAL",
                ]
            )

        elif domain == "FORECASTING":
            decisions.extend(
                [
                    "STOCKOUT_FORECAST",
                    "DEMAND_CAUSALITY",
                ]
            )

        for decision in decisions:
            gate = DeterministicDecisionGate.evaluate(
                decision,
                fused.available_sources,
            )

            result.decision_gates[decision] = {
                "required_sources": (
                    gate.required_sources
                ),
                "available_sources": (
                    gate.available_sources
                ),
                "missing_required_sources": (
                    gate.missing_required_sources
                ),
                "can_answer": gate.can_answer,
                "can_recommend": (
                    gate.can_recommend
                ),
                "can_establish_causality": (
                    gate.can_establish_causality
                ),
            }

    # ------------------------------------------------------------------
    # Decision blockers
    # ------------------------------------------------------------------


    @classmethod
    def _identify_decision_blockers(
        cls,
        fused: FusedEvidence,
        result: CausalReasoningResult,
        domain: str,
    ) -> None:
        blockers: List[str] = []

        # Determine blockers for the most relevant business decision.
        primary_decision = {
            "INVENTORY": "INVENTORY_STATUS",
            "SUPPLY": "SUPPLIER_CAUSALITY",
            "LOGISTICS": "SHIPMENT_CAUSALITY",
            "ECONOMICS": "WORKING_CAPITAL",
            "FORECASTING": "STOCKOUT_FORECAST",
        }.get(
            domain,
            "INVENTORY_STATUS",
        )

        gate = result.decision_gates.get(
            primary_decision
        )

        if gate:
            blockers.extend(
                gate.get(
                    "missing_required_sources",
                    [],
                )
            )

        result.decision_blockers = list(
            dict.fromkeys(blockers)
        )

    # ------------------------------------------------------------------
    # Quality / confidence
    # ------------------------------------------------------------------

    @classmethod
    def _score_result(
        cls,
        fused: FusedEvidence,
        result: CausalReasoningResult,
    ) -> None:
        supported = [
            link
            for link in result.causal_links
            if link.causal_supported
            and link.allowable_in_answer
        ]

        rejected = [
            link
            for link in result.causal_links
            if not link.causal_supported
        ]

        if not result.causal_links:
            result.causal_quality = "NONE"
            result.confidence = 0.0
            return

        if (
            len(supported) >= 3
            and len(fused.available_sources) >= 4
            and not fused.conflicts
        ):
            result.causal_quality = "HIGH"
        elif (
            len(supported) >= 2
            and not fused.conflicts
        ):
            result.causal_quality = "GOOD"
        elif supported:
            result.causal_quality = "PARTIAL"
        else:
            result.causal_quality = "INSUFFICIENT"

        if supported:
            avg = sum(
                link.strength
                for link in supported
            ) / len(supported)

            confidence = avg

            # Missing cross-source linkage reduces causal confidence.
            confidence -= min(
                0.12,
                len(rejected) * 0.025,
            )

            confidence -= min(
                0.10,
                len(fused.conflicts) * 0.05,
            )

            result.confidence = round(
                max(
                    0.0,
                    min(
                        0.99,
                        confidence,
                    ),
                ),
                3,
            )
        else:
            result.confidence = 0.0


__all__ = [
    "CausalLink",
    "CausalFinding",
    "CausalReasoningResult",
    "DeterministicCausalEngine",
]
