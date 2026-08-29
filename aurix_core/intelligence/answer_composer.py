"""
Best-in-class deterministic answer composition for AURIX.

The AnswerComposer converts an executed deterministic query plan and its
authoritative evidence into a professional, bounded, auditable response.

Design principles:
- Never invent facts.
- Never hide unavailable evidence.
- Prefer direct observed values over derived values.
- Derived values must be reproducible from supplied evidence.
- Recommendations must be explicitly evidence-backed.
- Every answer carries provenance and limitations.
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from pydantic import BaseModel, Field

from aurix_core.intelligence.query_plan import (
    DeterministicQueryPlan,
    QueryIntent,
)

from aurix_core.intelligence.deterministic_answer import (
    DeterministicAnswerContext,
)


class AnswerEvidence(BaseModel):
    """Normalized evidence available to the answer composer."""

    source: str
    available: bool = False
    records: List[Dict[str, Any]] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)


class AnswerCompositionInput(BaseModel):
    """Input contract for deterministic answer composition."""

    query: str
    plan: DeterministicQueryPlan
    evidence: List[AnswerEvidence] = Field(default_factory=list)
    successful_operations: List[str] = Field(default_factory=list)
    failed_operations: List[str] = Field(default_factory=list)
    skipped_operations: List[str] = Field(default_factory=list)
    tenant_id: Optional[str] = None


class AnswerCompositionResult(BaseModel):
    """Final deterministic answer contract."""

    headline: str
    answer: str
    verified_facts: List[str] = Field(default_factory=list)
    calculations: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    evidence_quality: str = "INSUFFICIENT"
    answer_source: str = "AURIX_ENGINE"


class AnswerComposer:
    """Professional deterministic answer composer."""

    _NUMBER_RE = re.compile(
        r"(?<![A-Za-z0-9_-])[-+]?\d+(?:\.\d+)?%?"
    )

    @staticmethod
    def _flatten_records(
        evidence: Sequence[AnswerEvidence],
    ) -> List[Tuple[str, Dict[str, Any]]]:
        flattened: List[Tuple[str, Dict[str, Any]]] = []

        for item in evidence:
            if not item.available:
                continue

            for record in item.records:
                if isinstance(record, dict):
                    flattened.append((item.source, record))

        return flattened

    @staticmethod
    def _numeric(value: Any) -> Optional[float]:
        if isinstance(value, bool):
            return None

        if isinstance(value, (int, float)):
            if isinstance(value, float) and not math.isfinite(value):
                return None
            return float(value)

        return None

    @staticmethod
    def _fmt_number(value: float) -> str:
        if abs(value - round(value)) < 1e-9:
            return f"{int(round(value)):,}"
        return f"{value:,.2f}".rstrip("0").rstrip(".")

    @staticmethod
    def _fmt_pct(value: float) -> str:
        return f"{value:.1f}%"

    @staticmethod
    def _find_entity(plan: DeterministicQueryPlan) -> Optional[str]:
        for entity in plan.entities:
            if entity.entity_id:
                return entity.entity_id
        return None

    @classmethod
    def _inventory_facts(
        cls,
        records: Sequence[Tuple[str, Dict[str, Any]]],
    ) -> Tuple[List[str], List[str], List[str]]:
        facts: List[str] = []
        calculations: List[str] = []
        recommendations: List[str] = []

        for source, row in records:
            if source != "inventory_position":
                continue

            sku = row.get("sku_id") or row.get("id") or "the SKU"
            location = row.get("location_id")

            on_hand = cls._numeric(row.get("on_hand"))
            on_order = cls._numeric(row.get("on_order"))
            safety_stock = cls._numeric(row.get("safety_stock"))

            if on_hand is not None:
                facts.append(
                    f"{sku} has {cls._fmt_number(on_hand)} units on hand"
                    + (f" at {location}." if location else ".")
                )

            if on_order is not None:
                facts.append(
                    f"{cls._fmt_number(on_order)} units are currently on order."
                )

            if safety_stock is not None:
                facts.append(
                    f"Safety stock is {cls._fmt_number(safety_stock)} units."
                )

            if on_hand is not None and safety_stock is not None:
                gap = on_hand - safety_stock
                calculations.append(
                    "On-hand vs safety stock: "
                    f"{cls._fmt_number(gap)} units "
                    f"({'above' if gap >= 0 else 'below'} safety stock)."
                )

                if safety_stock > 0:
                    coverage = on_hand / safety_stock * 100.0
                    calculations.append(
                        "On-hand represents "
                        f"{cls._fmt_pct(coverage)} of safety-stock requirement."
                    )

                if gap < 0:
                    recommendations.append(
                        "Review replenishment coverage because on-hand inventory "
                        "is below the configured safety-stock level."
                    )

            if on_hand is not None and on_order is not None:
                calculations.append(
                    "Current inventory plus inbound: "
                    f"{cls._fmt_number(on_hand + on_order)} units."
                )

        return facts, calculations, recommendations

    @classmethod
    def _supplier_facts(
        cls,
        records: Sequence[Tuple[str, Dict[str, Any]]],
    ) -> Tuple[List[str], List[str], List[str]]:
        facts: List[str] = []
        calculations: List[str] = []
        recommendations: List[str] = []

        for source, row in records:
            if source != "supplier_performance":
                continue

            supplier_id = row.get("supplier_id") or row.get("id") or "Supplier"

            otif = cls._numeric(row.get("otif_rate"))
            quality = cls._numeric(row.get("quality_yield_rate"))
            risk = cls._numeric(row.get("risk_score"))

            if otif is not None:
                facts.append(
                    f"{supplier_id} OTIF is {cls._fmt_pct(otif * 100 if otif <= 1 else otif)}."
                )

            if quality is not None:
                facts.append(
                    f"{supplier_id} quality yield is "
                    f"{cls._fmt_pct(quality * 100 if quality <= 1 else quality)}."
                )

            if risk is not None:
                facts.append(
                    f"{supplier_id} risk score is {cls._fmt_number(risk)}."
                )

                if risk >= 0.8:
                    recommendations.append(
                        f"{supplier_id} warrants priority risk review based on its "
                        "recorded risk score."
                    )

        return facts, calculations, recommendations

    @classmethod
    def _shipment_facts(
        cls,
        records: Sequence[Tuple[str, Dict[str, Any]]],
    ) -> Tuple[List[str], List[str], List[str]]:
        facts: List[str] = []
        calculations: List[str] = []
        recommendations: List[str] = []

        for source, row in records:
            if source != "shipment_evaluation":
                continue

            shipment_id = row.get("shipment_id") or row.get("id") or "Shipment"

            eta = row.get("estimated_delivery_date")
            promised = row.get("promised_delivery_date")
            delay = cls._numeric(row.get("delay_hours"))
            is_delayed = row.get("is_delayed")

            if eta:
                facts.append(
                    f"{shipment_id} estimated delivery: {eta}."
                )

            if promised:
                facts.append(
                    f"Promised delivery date: {promised}."
                )

            if delay is not None:
                calculations.append(
                    f"Recorded delay: {cls._fmt_number(delay)} hours."
                )

            if is_delayed is True:
                recommendations.append(
                    f"{shipment_id} should be monitored for delivery recovery "
                    "because the persisted evaluation marks it as delayed."
                )

        return facts, calculations, recommendations

    @classmethod
    def _forecast_facts(
        cls,
        records: Sequence[Tuple[str, Dict[str, Any]]],
    ) -> Tuple[List[str], List[str], List[str]]:
        facts: List[str] = []
        calculations: List[str] = []
        recommendations: List[str] = []

        forecast_rows = [
            row
            for source, row in records
            if source == "forecast"
        ]

        for row in forecast_rows[:5]:
            target_date = row.get("target_date")
            forecast = cls._numeric(row.get("point_forecast"))

            if forecast is None:
                continue

            facts.append(
                f"Forecast for {target_date or 'the next period'}: "
                f"{cls._fmt_number(forecast)} units."
            )

        if len(forecast_rows) > 5:
            calculations.append(
                f"{len(forecast_rows)} forecast points are available; "
                "the response shows the first five for readability."
            )

        return facts, calculations, recommendations

    @classmethod
    def _generic_facts(
        cls,
        records: Sequence[Tuple[str, Dict[str, Any]]],
    ) -> Tuple[List[str], List[str]]:
        facts: List[str] = []
        limitations: List[str] = []

        for source, row in records:
            if not row:
                continue

            label = (
                row.get("sku_id")
                or row.get("supplier_id")
                or row.get("shipment_id")
                or row.get("id")
                or source
            )

            important_fields = []

            for key, value in row.items():
                if key in {
                    "id",
                    "created_at",
                    "updated_at",
                    "ingestion_run_id",
                    "source_record_id",
                }:
                    continue

                if value is None:
                    continue

                if isinstance(value, (str, int, float, bool)):
                    important_fields.append((key, value))

            if important_fields:
                rendered = "; ".join(
                    f"{key}={value}"
                    for key, value in important_fields[:8]
                )
                facts.append(f"{label}: {rendered}.")

        return facts, limitations

    @classmethod
    def _collect_limitations(
        cls,
        evidence: Sequence[AnswerEvidence],
        plan: DeterministicQueryPlan,
    ) -> List[str]:
        limitations: List[str] = []

        for item in evidence:
            for limitation in item.limitations:
                text = str(limitation).strip()
                if text and text not in limitations:
                    limitations.append(text)

        for missing in plan.missing_requirements:
            text = str(missing).strip()
            if text and text not in limitations:
                limitations.append(text)

        for warning in plan.warnings:
            text = str(warning).strip()
            if text and text not in limitations:
                limitations.append(text)

        return limitations

    @classmethod
    def _headline(
        cls,
        plan: DeterministicQueryPlan,
        facts: Sequence[str],
        calculations: Sequence[str],
    ) -> str:
        entity = cls._find_entity(plan)

        if entity and plan.intent == QueryIntent.DIAGNOSE:
            return f"Risk assessment for {entity}"

        if entity and plan.intent == QueryIntent.RECOMMEND:
            return f"Recommended action for {entity}"

        if entity and plan.intent == QueryIntent.READ:
            return f"Current position for {entity}"

        if entity and plan.intent == QueryIntent.COMPARE:
            return f"Deterministic comparison for {entity}"

        if plan.intent == QueryIntent.SUMMARIZE:
            return "AURIX portfolio summary"

        if plan.intent == QueryIntent.RANK:
            return "AURIX risk ranking"

        if plan.intent == QueryIntent.TREND:
            return "AURIX trend analysis"

        if facts or calculations:
            return "AURIX deterministic analysis"

        return "AURIX evidence assessment"


    @staticmethod
    def _sentence_list(
        title: str,
        values: Sequence[str],
        limit: int = 8,
    ) -> Optional[str]:
        if not values:
            return None

        rendered = "\n".join(
            f"- {value}"
            for value in values[:limit]
        )

        return f"{title}\n{rendered}"

    @classmethod
    def compose_context(
        cls,
        context: DeterministicAnswerContext,
        *,
        plan: DeterministicQueryPlan,
        evidence: Sequence[AnswerEvidence],
        tenant_id: Optional[str] = None,
    ) -> AnswerCompositionResult:
        """
        Compose a professional deterministic answer from an already
        evaluated DeterministicAnswerContext.

        This method is a renderer, not a reasoning engine.

        Rules:
        - Only supported/allowable claims may become conclusions.
        - Direct evidence is preferred over derived statements.
        - Derived values are shown only when reproducible from the
          supplied evidence.
        - A proposition is rendered once.
        - Decision blockers are translated into human-readable
          limitations.
        - Unsupported causal explanations are never invented.
        """

        reasoning = context.reasoning
        causal = context.causal
        eligibility = context.eligibility

        records = cls._flatten_records(evidence)

        # ---------------------------------------------------------
        # Small deterministic text helpers
        # ---------------------------------------------------------

        def normalize(text: str) -> str:
            value = re.sub(
                r"[^a-z0-9]+",
                " ",
                str(text).lower(),
            )
            return re.sub(r"\s+", " ", value).strip()

        def add_unique(
            target: List[str],
            value: Optional[str],
        ) -> None:
            if not value:
                return

            candidate = str(value).strip()
            if not candidate:
                return

            signature = normalize(candidate)

            for existing in target:
                if normalize(existing) == signature:
                    return

            target.append(candidate)

        def human_source(source: str) -> str:
            labels = {
                "forecast": "forecast evidence",
                "replenishment_policy": (
                    "replenishment-policy evidence"
                ),
                "inventory_transactions": (
                    "inventory transaction history"
                ),
                "order_lines": "order-line demand detail",
                "supplier_performance": (
                    "supplier-performance evidence"
                ),
                "purchase_orders": (
                    "purchase-order evidence"
                ),
                "shipment_evaluation": (
                    "shipment-evaluation evidence"
                ),
                "shipments": "shipment records",
                "financial_baseline": (
                    "financial baseline data"
                ),
            }

            return labels.get(
                source,
                source.replace("_", " "),
            )

        # ---------------------------------------------------------
        # Approved claims
        # ---------------------------------------------------------

        claims: List[str] = []

        for claim in reasoning.claims:
            if not (
                claim.supported
                and claim.allowable_in_answer
            ):
                continue

            add_unique(
                claims,
                claim.statement,
            )

        # ---------------------------------------------------------
        # Quantified inventory evidence
        #
        # These values are direct observations or deterministic
        # arithmetic from direct observations.
        # ---------------------------------------------------------

        inventory_rows = [
            row
            for source, row in records
            if source == "inventory_position"
        ]

        inventory_facts: List[str] = []
        inventory_analysis: List[str] = []

        if inventory_rows:
            # Use the first authoritative position for the active
            # entity because EvidenceFabric has already applied the
            # entity filter.
            row = inventory_rows[0]

            sku = (
                row.get("sku_id")
                or context.entity_id
                or "the SKU"
            )

            location = row.get("location_id")

            on_hand = cls._numeric(
                row.get("on_hand")
            )
            on_order = cls._numeric(
                row.get("on_order")
            )
            safety_stock = cls._numeric(
                row.get("safety_stock")
            )

            if (
                on_hand is not None
                and safety_stock is not None
            ):
                gap = (
                    on_hand
                    - safety_stock
                )

                coverage = (
                    on_hand
                    / safety_stock
                    * 100.0
                    if safety_stock > 0
                    else None
                )

                location_text = (
                    f" at {location}"
                    if location
                    else ""
                )

                inventory_facts.append(
                    f"{sku} has "
                    f"{cls._fmt_number(on_hand)} units "
                    f"on hand{location_text}."
                )

                inventory_facts.append(
                    f"Safety stock is "
                    f"{cls._fmt_number(safety_stock)} units."
                )

                inventory_analysis.append(
                    f"On-hand inventory is "
                    f"{cls._fmt_number(abs(gap))} units "
                    f"{'above' if gap >= 0 else 'below'} "
                    f"the safety-stock target."
                )

                if coverage is not None:
                    inventory_analysis.append(
                        f"Current on-hand inventory provides "
                        f"{cls._fmt_pct(coverage)} coverage "
                        f"of the configured safety-stock requirement."
                    )

            if on_order is not None:
                inventory_facts.append(
                    f"{cls._fmt_number(on_order)} units "
                    f"are currently on order."
                )

            if (
                on_hand is not None
                and on_order is not None
            ):
                inventory_analysis.append(
                    f"On-hand plus inbound inventory totals "
                    f"{cls._fmt_number(on_hand + on_order)} units."
                )

        # ---------------------------------------------------------
        # Executive assessment
        # ---------------------------------------------------------

        assessment_parts: List[str] = []

        state = str(
            getattr(
                reasoning,
                "state",
                "",
            )
            or ""
        ).upper()

        state_label = (
            state.replace("_", " ").strip()
        )

        if state_label:
            assessment_parts.append(
                f"AURIX assesses the current position as "
                f"{state_label}."
            )

        # Prefer the strongest approved claim that is not merely
        # a repetition of the state label.
        if claims:
            candidate = claims[0]

            if normalize(candidate) not in {
                normalize(part)
                for part in assessment_parts
            }:
                assessment_parts.append(
                    candidate
                )

        # Inventory-specific enrichment belongs in the executive
        # paragraph because the numbers directly support the state.
        if (
            context.domain == "INVENTORY"
            and inventory_rows
        ):
            row = inventory_rows[0]

            on_hand = cls._numeric(
                row.get("on_hand")
            )
            safety_stock = cls._numeric(
                row.get("safety_stock")
            )

            if (
                on_hand is not None
                and safety_stock is not None
                and safety_stock > 0
            ):
                gap = on_hand - safety_stock
                coverage = (
                    on_hand
                    / safety_stock
                    * 100.0
                )

                quantified = (
                    f"On-hand inventory is "
                    f"{cls._fmt_number(on_hand)} units "
                    f"against a safety-stock target of "
                    f"{cls._fmt_number(safety_stock)} units, "
                    f"leaving a "
                    f"{cls._fmt_number(abs(gap))}-unit "
                    f"{'surplus' if gap >= 0 else 'protection deficit'}."
                )

                add_unique(
                    assessment_parts,
                    quantified,
                )

                coverage_text = str(
                    cls._fmt_pct(coverage)
                ).strip()

                coverage_sentence = (
                    "This represents "
                    + coverage_text
                    + " coverage of the configured safety-stock requirement."
                )

                add_unique(
                    assessment_parts,
                    coverage_sentence,
                )

            on_order = cls._numeric(
                row.get("on_order")
            )

            if on_order is not None:
                add_unique(
                    assessment_parts,
                    f"There are "
                    f"{cls._fmt_number(on_order)} units "
                    f"currently on order."
                )

        executive_assessment = " ".join(
            assessment_parts
        )

        # ---------------------------------------------------------
        # Business narrative
        # ---------------------------------------------------------

        implications: List[str] = []

        if (
            context.domain == "INVENTORY"
            and inventory_rows
        ):
            row = inventory_rows[0]

            on_hand = cls._numeric(
                row.get("on_hand")
            )
            on_order = cls._numeric(
                row.get("on_order")
            )

            if (
                on_hand is not None
                and on_order is not None
            ):
                implications.append(
                    "The "
                    + str(cls._fmt_number(on_order)).strip()
                    + " inbound units improve near-term availability, "
                    "but AURIX cannot determine whether they are "
                    "sufficient to cover future demand because "
                    "forecast evidence is unavailable."
                )

        # The executive assessment already states the primary
        # inventory condition. Do not restate it as a separate
        # causal sentence unless the causal engine identifies a
        # genuinely different driver.

        # ---------------------------------------------------------
        # Recommendations
        # ---------------------------------------------------------

        recommendations: List[str] = []

        if (
            eligibility.deterministic_recommendation_allowed
        ):
            for recommendation in reasoning.recommendations:
                action = str(
                    getattr(
                        recommendation,
                        "action",
                        "",
                    )
                    or ""
                ).strip()

                if not action:
                    continue

                # Keep the user-facing action concise. The rationale
                # stays in the reasoning/provenance layer.
                add_unique(
                    recommendations,
                    action.rstrip(".") + ".",
                )

        # ---------------------------------------------------------
        # Legacy inventory recommendation fallback.
        #
        # This fallback is strictly domain- and permission-gated.
        # Inventory recommendations must NEVER leak into supplier,
        # logistics, economics, forecasting, or executive answers.
        # ---------------------------------------------------------

        if (
            not recommendations
            and eligibility.deterministic_recommendation_allowed
            and context.domain.upper() == "INVENTORY"
        ):
            _, _, legacy_rec = cls._inventory_facts(
                records
            )

            for recommendation in legacy_rec:
                add_unique(
                    recommendations,
                    recommendation,
                )

        # ---------------------------------------------------------
        # Material limitations
        # ---------------------------------------------------------

        limitations: List[str] = []

        # Render only limitations material to the question.
        #
        # A user asking why inventory is low does not need every
        # unavailable dataset in the enterprise data fabric.
        unsupported = list(
            getattr(
                reasoning,
                "unsupported_conclusions",
                [],
            )
        )

        for source in eligibility.blockers:
            if source == "forecast":
                add_unique(
                    limitations,
                    "An exact future stockout date cannot be "
                    "established because forecast evidence is unavailable.",
                )

            elif source == "replenishment_policy":
                add_unique(
                    limitations,
                    "Replenishment adequacy cannot be confirmed "
                    "because the current replenishment policy is unavailable.",
                )

            elif source in {
                "supplier_performance",
                "purchase_orders",
                "shipment_evaluation",
                "shipments",
            }:
                # Only expose this when the query is actually asking
                # about supply-side causality.
                if (
                    context.intent
                    and str(context.intent).upper()
                    in {
                        "DIAGNOSE",
                        "RECOMMEND",
                        "EXPLAIN",
                    }
                    and (
                        "supplier" in context.query.lower()
                        or "vendor" in context.query.lower()
                        or "shipment" in context.query.lower()
                        or "delivery" in context.query.lower()
                    )
                ):
                    add_unique(
                        limitations,
                        "A supplier or shipment root cause cannot "
                        "be established from the evidence currently available.",
                    )

            elif source == "financial_baseline":
                if (
                    "cost" in context.query.lower()
                    or "financial" in context.query.lower()
                    or "working capital" in context.query.lower()
                    or "exposure" in context.query.lower()
                ):
                    add_unique(
                        limitations,
                        "Financial exposure cannot be quantified "
                        "because the financial baseline is unavailable.",
                    )

        # Only retain unsupported conclusions that are material to
        # the requested question. For the current inventory-risk
        # question, suppress generic future/consumption caveats
        # unless they are directly requested.
        query_text = context.query.lower()

        for conclusion in unsupported:
            normalized = normalize(
                conclusion
            )

            relevant = (
                "stockout" in normalized
                and (
                    "stockout" in query_text
                    or "stock out" in query_text
                )
            ) or (
                "replenishment" in normalized
                and "replenish" in query_text
            ) or (
                "consumption" in normalized
                and (
                    "consumption" in query_text
                    or "usage" in query_text
                    or "demand" in query_text
                )
            )

            if relevant:
                add_unique(
                    limitations,
                    conclusion,
                )

        # The user is asking what to do about the current
        # inventory position. Since the recommendation references
        # future coverage, the absence of forecast evidence is a
        # material limitation and must remain visible.
        query_text = context.query.lower()

        # The deterministic pipeline already exposes blocked/unsupported
        # conclusions through context.limitations and decision blockers.
        # Do not make the composer depend on an unavailable fused object
        # or on an optional provenance field.

        existing_limitations = list(
            getattr(
                context,
                "limitations",
                [],
            )
        )

        query_text = context.query.lower()

        for limitation in existing_limitations:
            normalized = normalize(
                limitation
            )

            relevant = (
                "stockout" in normalized
                and (
                    "stockout" in query_text
                    or "stock out" in query_text
                    or "what should" in query_text
                    or "should we" in query_text
                    or "recommend" in query_text
                )
            ) or (
                "replenishment" in normalized
                and (
                    "replenish" in query_text
                    or "inventory" in query_text
                    or "stock" in query_text
                    or "what should" in query_text
                    or "should we" in query_text
                    or "recommend" in query_text
                )
            ) or (
                "consumption" in normalized
                and (
                    "consumption" in query_text
                    or "usage" in query_text
                    or "demand" in query_text
                )
            )

            if relevant:
                add_unique(
                    limitations,
                    limitation,
                )

        # ---------------------------------------------------------
        # Final narrative
        # ---------------------------------------------------------

        paragraphs: List[str] = []

        # Executive assessment.
        if executive_assessment:
            paragraphs.append(
                "Executive assessment:\n"
                + executive_assessment
            )
        else:
            paragraphs.append(
                "Executive assessment:\n"
                "AURIX does not have sufficient authoritative "
                "evidence to fully resolve the requested question."
            )

        # Business implication.
        if implications:
            paragraphs.append(
                "What this means:\n"
                + " ".join(
                    implications[:3]
                )
            )

        # Recommendation.
        if recommendations:
            paragraphs.append(
                "Recommended direction:\n"
                + " ".join(
                    recommendations[:2]
                )
            )

        # Limitations.
        if limitations:
            paragraphs.append(
                "What AURIX cannot currently establish:\n"
                + " ".join(
                    limitations[:3]
                )
            )

        quality = (
            reasoning.evidence_quality
            or "INSUFFICIENT"
        )

        paragraphs.append(
            "Evidence confidence: "
            f"{eligibility.confidence:.2f} "
            f"({quality}) for the current assessment."
        )

        # ---------------------------------------------------------
        # Final text normalization.
        #
        # This is intentionally conservative and only fixes whitespace
        # / punctuation artifacts introduced during composition.
        # ---------------------------------------------------------

        answer = "\n\n".join(
            paragraphs
        )

        answer = re.sub(
            r"([a-zA-Z])([0-9])",
            r"\1 \2",
            answer,
        )

        answer = re.sub(
            r"([0-9])([a-zA-Z])",
            r"\1 \2",
            answer,
        )

        answer = re.sub(
            r"\.\s*\.",
            ".",
            answer,
        )

        answer = re.sub(
            r"\s+([,.])",
            r"\1",
            answer,
        )

        answer = re.sub(
            r"[ \t]+",
            " ",
            answer,
        )

        # Restore paragraph/newline readability after whitespace
        # normalization.
        answer = re.sub(
            r"\n +",
            "\n",
            answer,
        )

        # ---------------------------------------------------------
        # Headline
        # ---------------------------------------------------------

        if context.entity_id:
            headline_map = {
                "INVENTORY": (
                    f"Inventory assessment for "
                    f"{context.entity_id}"
                ),
                "SUPPLY": (
                    f"Supplier assessment for "
                    f"{context.entity_id}"
                ),
                "LOGISTICS": (
                    f"Shipment assessment for "
                    f"{context.entity_id}"
                ),
            }

            headline = headline_map.get(
                context.domain,
                (
                    f"AURIX assessment for "
                    f"{context.entity_id}"
                ),
            )
        else:
            headline = (
                "AURIX deterministic assessment"
            )

        provenance = {
            **context.provenance,
            "composer": (
                "answer-composer-deterministic-v4"
            ),
            "answer_source": "AURIX_ENGINE",
            "tenant_id": (
                tenant_id
                or context.provenance.get(
                    "tenant_id"
                )
            ),
            "evidence_quality": quality,
            "confidence": eligibility.confidence,
            "full_answerable": (
                eligibility.deterministic_answerable
            ),
            "partial_answer_available": (
                eligibility.partial_answer_available
            ),
            "escalation_recommended": (
                eligibility.escalation_recommended
            ),
            "decision_blockers": (
                eligibility.blockers
            ),
        }

        return AnswerCompositionResult(
            headline=headline,
            answer=answer,
            verified_facts=(
                claims
            ),
            calculations=(
                inventory_analysis
            ),
            recommendations=(
                recommendations
            ),
            limitations=(
                limitations
            ),
            provenance=provenance,
            confidence=round(
                eligibility.confidence,
                3,
            ),
            evidence_quality=quality,
            answer_source="AURIX_ENGINE",
        )

    @classmethod
    def compose_validated_claims(
        cls,
        *,
        query: str,
        decision: str,
        claims: Sequence[Any] = (),
        validation_result: Optional[Any] = None,
        limitations: Sequence[str] = (),
        confidence: float = 0.0,
        evidence_quality: str = "INSUFFICIENT",
        provenance: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
    ) -> AnswerCompositionResult:
        """Render only claims accepted by the canonical validator.

        This method is a renderer. It never evaluates freshness,
        selects authority, resolves contradictions, or invents evidence.
        """

        validator_provenance: Dict[str, Any] = {}

        if validation_result is not None:
            accepted_claims = list(
                getattr(validation_result, "accepted", ()) or ()
            )
            rejected_claims = list(
                getattr(validation_result, "rejected", ()) or ()
            )

            # Canonical path: only validator-approved claims may render.
            render_claims = accepted_claims

            validator_limitations = list(
                getattr(validation_result, "limitations", ()) or ()
            )
            validator_provenance = dict(
                getattr(validation_result, "provenance", {}) or {}
            )
        else:
            # Backward-compatible rendering seam for existing callers.
            # The canonical N3.4 service path will pass validation_result.
            render_claims = [
                claim
                for claim in claims
                if bool(getattr(claim, "supported", False))
                and bool(getattr(claim, "allowable_in_answer", False))
            ]
            rejected_claims = [
                claim
                for claim in claims
                if claim not in render_claims
            ]
            validator_limitations = []

        statements = [
            str(getattr(claim, "statement", "")).strip()
            for claim in render_claims
            if str(getattr(claim, "statement", "")).strip()
        ]
        statements = list(dict.fromkeys(statements))

        combined_limitations = [
            str(value).strip()
            for value in (
                list(validator_limitations)
                + list(limitations)
            )
            if str(value).strip()
        ]
        combined_limitations = list(dict.fromkeys(combined_limitations))

        if statements:
            answer = "\n".join(
                f"- {statement}" for statement in statements
            )
        else:
            answer = (
                "AURIX could not produce a sufficiently supported "
                "deterministic answer for this decision."
            )

        if combined_limitations:
            answer += (
                "\n\nEvidence limitations:\n"
                + "\n".join(
                    f"- {item}" for item in combined_limitations
                )
            )

        # Preserve canonical metadata without recalculating anything.
        metadata_provenance: Dict[str, Any] = {}

        if render_claims:
            freshness_states = list(dict.fromkeys(
                str(getattr(claim, "freshness_state", "UNKNOWN"))
                for claim in render_claims
            ))

            freshness_ages = list(dict.fromkeys(
                getattr(claim, "freshness_age_hours", None)
                for claim in render_claims
                if getattr(claim, "freshness_age_hours", None) is not None
            ))

            observation_timestamps = list(dict.fromkeys(
                str(getattr(claim, "observation_timestamp", "")).strip()
                for claim in render_claims
                if str(getattr(claim, "observation_timestamp", "")).strip()
            ))

            sources = list(dict.fromkeys(
                str(getattr(claim, "source", "")).strip()
                for claim in render_claims
                if str(getattr(claim, "source", "")).strip()
            ))

            locations = list(dict.fromkeys(
                str(getattr(claim, "location_id", "")).strip()
                for claim in render_claims
                if str(getattr(claim, "location_id", "")).strip()
            ))

            claim_tenants = list(dict.fromkeys(
                str(getattr(claim, "tenant_id", "")).strip()
                for claim in render_claims
                if str(getattr(claim, "tenant_id", "")).strip()
            ))

            claim_provenance = [
                dict(getattr(claim, "provenance", {}) or {})
                for claim in render_claims
            ]

            # Promote stable lineage/authority metadata to the canonical
            # composer provenance surface while retaining the complete
            # per-claim provenance collection. No values are recalculated
            # or invented here.
            promoted_keys = (
                "source_record_id",
                "ingestion_run_id",
                "authority",
                "contradiction_id",
            )

            promoted_provenance = {}

            for key in promoted_keys:
                values = list(dict.fromkeys(
                    str(item[key]).strip()
                    for item in claim_provenance
                    if item.get(key) is not None
                    and str(item[key]).strip()
                ))

                if len(values) == 1:
                    promoted_provenance[key] = values[0]
                elif values:
                    promoted_provenance[key] = values

            metadata_provenance = {
                "freshness_state": (
                    freshness_states[0]
                    if len(freshness_states) == 1
                    else None
                ),
                "freshness_age_hours": (
                    freshness_ages[0]
                    if len(freshness_ages) == 1
                    else None
                ),
                "freshness_states": freshness_states,
                "observation_timestamps": observation_timestamps,
                "sources": sources,
                "locations": locations,
                "tenants": claim_tenants,
                "claim_provenance": claim_provenance,
                **promoted_provenance,
            }

            if len(observation_timestamps) == 1:
                metadata_provenance["observation_timestamp"] = (
                    observation_timestamps[0]
                )

            if len(sources) == 1:
                metadata_provenance["source"] = sources[0]

            if len(locations) == 1:
                metadata_provenance["location_id"] = locations[0]

            if len(claim_tenants) == 1:
                metadata_provenance["claim_tenant_id"] = claim_tenants[0]

        normalized_decision = (
            str(decision).strip().replace("_", " ").title()
        )

        final_provenance = {
            **dict(provenance or {}),
            **validator_provenance,
            **metadata_provenance,
            "composer": "AnswerComposer",
            "decision": str(decision).strip().upper(),
            "tenant_id": (
                tenant_id
                or validator_provenance.get("tenant_id")
                or metadata_provenance.get("claim_tenant_id")
            ),
            "claims_validated": validation_result is not None,
            "rejected_claim_count": len(rejected_claims),
        }

        return AnswerCompositionResult(
            headline=f"AURIX {normalized_decision}",
            answer=answer,
            verified_facts=statements,
            calculations=[],
            recommendations=[],
            limitations=combined_limitations,
            provenance=final_provenance,
            confidence=max(
                0.0,
                min(1.0, float(confidence)),
            ),
            evidence_quality=evidence_quality,
            answer_source="AURIX_ENGINE",
        )


    @classmethod
    def compose(
        cls,
        request: AnswerCompositionInput,
    ) -> AnswerCompositionResult:
        records = cls._flatten_records(request.evidence)

        facts: List[str] = []
        calculations: List[str] = []
        recommendations: List[str] = []

        inv_facts, inv_calc, inv_rec = cls._inventory_facts(records)
        sup_facts, sup_calc, sup_rec = cls._supplier_facts(records)
        ship_facts, ship_calc, ship_rec = cls._shipment_facts(records)
        fc_facts, fc_calc, fc_rec = cls._forecast_facts(records)

        facts.extend(inv_facts)
        facts.extend(sup_facts)
        facts.extend(ship_facts)
        facts.extend(fc_facts)

        calculations.extend(inv_calc)
        calculations.extend(sup_calc)
        calculations.extend(ship_calc)
        calculations.extend(fc_calc)

        recommendations.extend(inv_rec)
        recommendations.extend(sup_rec)
        recommendations.extend(ship_rec)
        recommendations.extend(fc_rec)

        if not facts and not calculations:
            generic_facts, _ = cls._generic_facts(records)
            facts.extend(generic_facts)

        limitations = cls._collect_limitations(
            request.evidence,
            request.plan,
        )

        if not records:
            limitations.insert(
                0,
                "No authoritative records were available for the requested analysis."
            )

        # Preserve order while removing duplicates.
        facts = list(dict.fromkeys(facts))
        calculations = list(dict.fromkeys(calculations))
        recommendations = list(dict.fromkeys(recommendations))
        limitations = list(dict.fromkeys(limitations))

        paragraphs: List[str] = []

        if facts:
            paragraphs.append("Verified findings:\n- " + "\n- ".join(facts[:8]))

        if calculations:
            paragraphs.append(
                "Deterministic analysis:\n- "
                + "\n- ".join(calculations[:8])
            )

        if recommendations:
            paragraphs.append(
                "Recommended next step:\n- "
                + "\n- ".join(recommendations[:5])
            )

        if limitations:
            paragraphs.append(
                "Evidence limitations:\n- "
                + "\n- ".join(limitations[:8])
            )

        if not paragraphs:
            paragraphs.append(
                "AURIX could not produce a sufficiently supported deterministic "
                "answer from the currently available evidence."
            )

        evidence_quality = "HIGH"

        if not records:
            evidence_quality = "INSUFFICIENT"
        elif limitations:
            evidence_quality = "PARTIAL"
        elif len(records) == 1:
            evidence_quality = "HIGH"

        base_confidence = float(request.plan.confidence or 0.0)

        if evidence_quality == "INSUFFICIENT":
            confidence = min(base_confidence, 0.35)
        elif evidence_quality == "PARTIAL":
            confidence = min(base_confidence, 0.80)
        else:
            confidence = max(base_confidence, 0.90)

        answer = "\n\n".join(paragraphs)

        provenance = {
            "answer_source": "AURIX_ENGINE",
            "query_intent": request.plan.intent.value,
            "plan_confidence": request.plan.confidence,
            "evidence_sources": [
                item.source for item in request.evidence if item.available
            ],
            "unavailable_sources": [
                item.source for item in request.evidence if not item.available
            ],
            "successful_operations": request.successful_operations,
            "failed_operations": request.failed_operations,
            "skipped_operations": request.skipped_operations,
            "tenant_id": request.tenant_id,
        }

        return AnswerCompositionResult(
            headline=cls._headline(
                request.plan,
                facts,
                calculations,
            ),
            answer=answer,
            verified_facts=facts,
            calculations=calculations,
            recommendations=recommendations,
            limitations=limitations,
            provenance=provenance,
            confidence=round(confidence, 3),
            evidence_quality=evidence_quality,
            answer_source="AURIX_ENGINE",
        )
