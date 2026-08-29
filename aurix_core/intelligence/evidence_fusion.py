"""
AURIX Deterministic Evidence Fusion Engine.

Combines heterogeneous EvidenceFabric outputs into a bounded,
auditable business evidence model without invoking an external LLM.

The fusion layer:
- normalizes source records
- identifies corroborating facts
- detects conflicts
- derives operational metrics
- derives business-risk relationships
- preserves source limitations
- produces a deterministic evidence narrative input
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class EvidenceFact:
    key: str
    value: Any
    source: str
    entity_id: Optional[str] = None
    location_id: Optional[str] = None
    record_id: Optional[str] = None
    source_record_id: Optional[str] = None
    ingestion_run_id: Optional[str] = None
    unit: Optional[str] = None
    confidence: float = 1.0
    observed: bool = True


@dataclass
class EvidenceConflict:
    key: str
    values: List[Any]
    sources: List[str]
    description: str
    entity_id: Optional[str] = None
    location_id: Optional[str] = None
    record_ids: List[str] = field(default_factory=list)
    source_record_ids: List[str] = field(default_factory=list)
    ingestion_run_ids: List[str] = field(default_factory=list)


@dataclass
class DerivedFact:
    key: str
    value: Any
    formula: str
    source_facts: List[str] = field(default_factory=list)
    location_id: Optional[str] = None
    confidence: float = 1.0


@dataclass
class FusedEvidence:
    query: str
    tenant_id: str
    entity_id: Optional[str]
    location_id: Optional[str] = None

    facts: List[EvidenceFact] = field(default_factory=list)
    derived_facts: List[DerivedFact] = field(default_factory=list)
    conflicts: List[EvidenceConflict] = field(default_factory=list)

    available_sources: List[str] = field(default_factory=list)
    unavailable_sources: List[str] = field(default_factory=list)

    evidence_quality: str = "NONE"
    confidence: float = 0.0

    provenance: Dict[str, Any] = field(default_factory=dict)


class EvidenceFusionEngine:
    """
    Deterministically fuses EvidenceFabric source packets.

    This class intentionally does not generate free-form language.
    It produces structured evidence for the Answer Composer.
    """

    SOURCE_WEIGHTS: Dict[str, float] = {
        "inventory_position": 1.00,
        "replenishment_policy": 1.00,
        "forecast": 0.95,
        "supplier_performance": 1.00,
        "shipment_evaluation": 1.00,
        "inventory_transactions": 0.90,
        "order_lines": 0.95,
        "orders": 0.95,
        "purchase_orders": 0.95,
        "shipments": 0.95,
        "product": 0.85,
        "suppliers": 0.85,
        "financial_baseline": 0.90,
        "intelligence_snapshot": 1.00,
    }

    @classmethod
    def fuse(
        cls,
        *,
        tenant_id: str,
        query: str,
        evidence_pack: Any,
        entity_id: Optional[str] = None,
        location_id: Optional[str] = None,
    ) -> FusedEvidence:
        available = list(
            getattr(evidence_pack, "available_sources", None) or []
        )
        unavailable = list(
            getattr(evidence_pack, "unavailable_sources", None) or []
        )

        fused = FusedEvidence(
            query=query,
            tenant_id=tenant_id,
            entity_id=entity_id,
            location_id=location_id,
            available_sources=available,
            unavailable_sources=unavailable,
        )

        source_items = getattr(evidence_pack, "items", None) or []

        for item in source_items:
            source = str(getattr(item, "source", "") or "").strip()
            records = getattr(item, "records", None) or []

            if not source or not records:
                continue

            for record in records:
                if not isinstance(record, dict):
                    continue

                cls._extract_facts(
                    fused=fused,
                    source=source,
                    record=record,
                    entity_id=entity_id,
                    location_id=location_id,
                )

        cls._derive_inventory_relationships(fused)
        cls._derive_supplier_relationships(fused)
        cls._derive_logistics_relationships(fused)
        cls._derive_financial_relationships(fused)

        cls._detect_conflicts(fused)
        cls._score_quality(fused)

        existing_limitations = list(
            fused.provenance.get("limitations", [])
        )

        fused.provenance = {
            "answer_source": "AURIX_ENGINE",
            "fusion_engine": "deterministic-evidence-fusion-v1",
            "tenant_id": tenant_id,
            "entity_id": entity_id,
            "location_id": location_id,
            "available_sources": list(available),
            "unavailable_sources": list(unavailable),
            "fact_count": len(fused.facts),
            "derived_fact_count": len(fused.derived_facts),
            "conflict_count": len(fused.conflicts),
            "limitations": existing_limitations,
        }

        return fused

    @classmethod
    def _extract_facts(
        cls,
        *,
        fused: FusedEvidence,
        source: str,
        record: Dict[str, Any],
        entity_id: Optional[str],
        location_id: Optional[str],
    ) -> None:
        effective_entity = (
            str(
                record.get("sku_id")
                or record.get("supplier_id")
                or record.get("shipment_id")
                or record.get("entity_id")
                or entity_id
            )
            if (
                record.get("sku_id")
                or record.get("supplier_id")
                or record.get("shipment_id")
                or record.get("entity_id")
                or entity_id
            )
            else None
        )

        for key, value in record.items():
            if key in {
                "id",
                "created_at",
                "updated_at",
                "evaluated_at",
                "source_record_id",
                "ingestion_run_id",
            }:
                continue

            if value is None:
                continue

            if isinstance(value, (str, int, float, bool)):
                fused.facts.append(
                    EvidenceFact(
                        key=f"{source}.{key}",
                        value=value,
                        source=source,
                        entity_id=effective_entity,
                        location_id=(
                            str(record.get("location_id"))
                            if record.get("location_id") is not None
                            else location_id
                        ),
                        record_id=(
                            str(record.get("id"))
                            if record.get("id") is not None
                            else None
                        ),
                        source_record_id=(
                            str(record.get("source_record_id"))
                            if record.get("source_record_id") is not None
                            else None
                        ),
                        ingestion_run_id=(
                            str(record.get("ingestion_run_id"))
                            if record.get("ingestion_run_id") is not None
                            else None
                        ),
                        confidence=cls.SOURCE_WEIGHTS.get(source, 0.75),
                    )
                )

    @staticmethod
    def _resolve_inventory_location(
        fused: FusedEvidence,
    ) -> tuple[Optional[str], bool]:
        """
        Resolve inventory scope without collapsing locations.

        Returns:
            (location_id, ambiguous)

        Rules:
          1. Explicit fusion location is authoritative.
          2. Exactly one observed inventory location can be inferred.
          3. Multiple locations without explicit scope are ambiguous.
          4. Ambiguous inventory must not produce a single derived result.
        """

        if fused.location_id:
            return fused.location_id, False

        locations = {
            fact.location_id
            for fact in fused.facts
            if (
                fact.source == "inventory_position"
                and fact.location_id is not None
            )
        }

        if len(locations) == 1:
            return next(iter(locations)), False

        if len(locations) > 1:
            return None, True

        return None, False

    @classmethod
    def _get_inventory(
        cls,
        fused: FusedEvidence,
        key: str,
        location_id: Optional[str],
    ) -> Optional[Any]:
        """
        Inventory-specific fact selection.

        The generic _get() is intentionally untouched because it is
        shared by other domains.
        """

        wanted = f"inventory_position.{key}"

        candidates = [
            fact
            for fact in fused.facts
            if (
                fact.key == wanted
                and fact.source == "inventory_position"
            )
        ]

        if not candidates:
            return None

        if location_id is not None:
            candidates = [
                fact
                for fact in candidates
                if fact.location_id == location_id
            ]

            if not candidates:
                return None

        else:
            locations = {
                fact.location_id
                for fact in candidates
            }

            if len(locations) > 1:
                return None

        return candidates[-1].value

    @staticmethod
    def _get(
        fused: FusedEvidence,
        source: str,
        key: str,
    ) -> Optional[Any]:
        wanted = f"{source}.{key}"

        for fact in reversed(fused.facts):
            if fact.key == wanted:
                return fact.value

        return None

    @classmethod
    def _derive_inventory_relationships(
        cls,
        fused: FusedEvidence,
    ) -> None:
        inventory_location, inventory_ambiguous = (
            cls._resolve_inventory_location(fused)
        )

        if inventory_ambiguous:
            fused.provenance.setdefault(
                "limitations",
                [],
            ).append(
                "INVENTORY_LOCATION_SCOPE_AMBIGUOUS"
            )
            return

        on_hand = cls._get_inventory(
            fused,
            "on_hand",
            inventory_location,
        )
        safety_stock = cls._get_inventory(
            fused,
            "safety_stock",
            inventory_location,
        )
        on_order = cls._get_inventory(
            fused,
            "on_order",
            inventory_location,
        )

        if isinstance(on_hand, (int, float)) and isinstance(
            safety_stock, (int, float)
        ):
            delta = float(on_hand) - float(safety_stock)

            fused.derived_facts.append(
                DerivedFact(
                    key="inventory.safety_stock_delta",
                    value=round(delta, 4),
                    formula="on_hand - safety_stock",
                    source_facts=[
                        "inventory_position.on_hand",
                        "inventory_position.safety_stock",
                    ],
                    location_id=inventory_location,
                    confidence=0.99,
                )
            )

            if float(safety_stock) != 0:
                coverage_pct = (
                    float(on_hand) / float(safety_stock)
                ) * 100.0

                fused.derived_facts.append(
                    DerivedFact(
                        key="inventory.safety_stock_coverage_pct",
                        value=round(coverage_pct, 2),
                        formula="on_hand / safety_stock * 100",
                        source_facts=[
                            "inventory_position.on_hand",
                            "inventory_position.safety_stock",
                        ],
                        location_id=inventory_location,
                    confidence=0.99,
                    )
                )

        if (
            isinstance(on_hand, (int, float))
            and isinstance(on_order, (int, float))
        ):
            fused.derived_facts.append(
                DerivedFact(
                    key="inventory.total_available_plus_inbound",
                    value=round(
                        float(on_hand) + float(on_order),
                        4,
                    ),
                    formula="on_hand + on_order",
                    source_facts=[
                        "inventory_position.on_hand",
                        "inventory_position.on_order",
                    ],
                    location_id=inventory_location,
                    confidence=0.99,
                )
            )

        daily_demand = cls._get(
            fused,
            "replenishment_policy",
            "expected_daily_demand",
        )

        if (
            isinstance(on_hand, (int, float))
            and isinstance(daily_demand, (int, float))
            and float(daily_demand) > 0
        ):
            runway = float(on_hand) / float(daily_demand)

            fused.derived_facts.append(
                DerivedFact(
                    key="inventory.on_hand_runway_days",
                    value=round(runway, 2),
                    formula="on_hand / expected_daily_demand",
                    source_facts=[
                        "inventory_position.on_hand",
                        "replenishment_policy.expected_daily_demand",
                    ],
                    location_id=inventory_location,
                    confidence=0.98,
                )
            )

    @classmethod
    def _derive_supplier_relationships(
        cls,
        fused: FusedEvidence,
    ) -> None:
        otif = cls._get(
            fused,
            "supplier_performance",
            "otif_rate",
        )
        risk = cls._get(
            fused,
            "supplier_performance",
            "risk_score",
        )
        lead_time = cls._get(
            fused,
            "supplier_performance",
            "mean_lead_time_days",
        )

        if isinstance(otif, (int, float)):
            fused.derived_facts.append(
                DerivedFact(
                    key="supplier.service_coverage_pct",
                    value=round(float(otif) * 100.0, 2)
                    if 0 <= float(otif) <= 1
                    else round(float(otif), 2),
                    formula=(
                        "otif_rate * 100 when rate is fractional, "
                        "otherwise otif_rate"
                    ),
                    source_facts=[
                        "supplier_performance.otif_rate"
                    ],
                    confidence=0.98,
                )
            )

        if isinstance(risk, (int, float)):
            if float(risk) >= 80:
                severity = "HIGH"
            elif float(risk) >= 50:
                severity = "MEDIUM"
            else:
                severity = "LOW"

            fused.derived_facts.append(
                DerivedFact(
                    key="supplier.risk_band",
                    value=severity,
                    formula="deterministic risk thresholding",
                    source_facts=[
                        "supplier_performance.risk_score"
                    ],
                    confidence=0.97,
                )
            )

        if isinstance(lead_time, (int, float)):
            fused.derived_facts.append(
                DerivedFact(
                    key="supplier.mean_lead_time_days",
                    value=round(float(lead_time), 2),
                    formula="authoritative supplier performance value",
                    source_facts=[
                        "supplier_performance.mean_lead_time_days"
                    ],
                    confidence=0.99,
                )
            )

    @classmethod
    def _derive_logistics_relationships(
        cls,
        fused: FusedEvidence,
    ) -> None:
        delay_hours = cls._get(
            fused,
            "shipment_evaluation",
            "delay_hours",
        )
        is_delayed = cls._get(
            fused,
            "shipment_evaluation",
            "is_delayed",
        )

        if isinstance(delay_hours, (int, float)):
            fused.derived_facts.append(
                DerivedFact(
                    key="logistics.delay_days",
                    value=round(
                        float(delay_hours) / 24.0,
                        2,
                    ),
                    formula="delay_hours / 24",
                    source_facts=[
                        "shipment_evaluation.delay_hours"
                    ],
                    confidence=0.99,
                )
            )

        if isinstance(is_delayed, bool):
            fused.derived_facts.append(
                DerivedFact(
                    key="logistics.delivery_status",
                    value="DELAYED" if is_delayed else "ON_TIME",
                    formula="shipment_evaluation.is_delayed",
                    source_facts=[
                        "shipment_evaluation.is_delayed"
                    ],
                    confidence=0.99,
                )
            )

    @classmethod
    def _derive_financial_relationships(
        cls,
        fused: FusedEvidence,
    ) -> None:
        holding_exposure = cls._get(
            fused,
            "replenishment_policy",
            "holding_cost_exposure",
        )

        if isinstance(holding_exposure, (int, float)):
            fused.derived_facts.append(
                DerivedFact(
                    key="economics.holding_cost_exposure",
                    value=round(float(holding_exposure), 2),
                    formula="authoritative replenishment policy value",
                    source_facts=[
                        "replenishment_policy.holding_cost_exposure"
                    ],
                    confidence=0.99,
                )
            )

    @classmethod
    def _detect_conflicts(
        cls,
        fused: FusedEvidence,
    ) -> None:
        """
        Detect contradictions within the same entity/location/attribute scope.

        Conflict scope is deliberately:
            entity_id + location_id + attribute

        Rules:
          - Different entities never conflict.
          - Different locations never conflict.
          - Same value repeated is compatible.
          - Different values in the same scope are a conflict,
            even when the evidence source label is the same.
          - This method does not select an authoritative winner.
            Source authority remains outside EvidenceFusion.
        """

        grouped: Dict[
            tuple[Optional[str], Optional[str], str],
            List[EvidenceFact],
        ] = {}

        for fact in fused.facts:
            parts = fact.key.split(".", 1)

            if len(parts) != 2:
                continue

            attribute = parts[1]

            scope = (
                fact.entity_id,
                fact.location_id,
                attribute,
            )

            grouped.setdefault(scope, []).append(fact)

        for (
            entity_id,
            location_id,
            attribute,
        ), facts in grouped.items():

            values: List[Any] = []
            sources: List[str] = []
            record_ids: List[str] = []
            source_record_ids: List[str] = []
            ingestion_run_ids: List[str] = []

            for fact in facts:
                if fact.value not in values:
                    values.append(fact.value)

                if fact.source not in sources:
                    sources.append(fact.source)

                if fact.record_id is not None and fact.record_id not in record_ids:
                    record_ids.append(fact.record_id)

                if (
                    fact.source_record_id is not None
                    and fact.source_record_id not in source_record_ids
                ):
                    source_record_ids.append(
                        fact.source_record_id
                    )

                if (
                    fact.ingestion_run_id is not None
                    and fact.ingestion_run_id not in ingestion_run_ids
                ):
                    ingestion_run_ids.append(
                        fact.ingestion_run_id
                    )

            # Identical values are compatible, regardless of duplication.
            if len(values) <= 1:
                continue

            fused.conflicts.append(
                EvidenceConflict(
                    key=attribute,
                    values=values,
                    sources=sources,
                    description=(
                        f"Conflicting values detected for {attribute} "
                        f"within entity={entity_id!r}, "
                        f"location={location_id!r}."
                    ),
                    entity_id=entity_id,
                    location_id=location_id,
                    record_ids=record_ids,
                    source_record_ids=source_record_ids,
                    ingestion_run_ids=ingestion_run_ids,
                )
            )

    @classmethod
    def _score_quality(
        cls,
        fused: FusedEvidence,
    ) -> None:
        source_count = len(fused.available_sources)
        fact_count = len(fused.facts)

        if fact_count == 0:
            fused.evidence_quality = "NONE"
            fused.confidence = 0.0
            return

        if source_count >= 5 and fact_count >= 10:
            quality = "HIGH"
        elif source_count >= 3 and fact_count >= 5:
            quality = "GOOD"
        elif source_count >= 2:
            quality = "PARTIAL"
        else:
            quality = "LIMITED"

        confidence = min(
            0.99,
            max(
                0.55,
                0.55
                + min(source_count, 8) * 0.05
                + min(len(fused.derived_facts), 8) * 0.03
                - min(len(fused.conflicts), 4) * 0.08,
            ),
        )

        fused.evidence_quality = quality
        fused.confidence = round(confidence, 3)


__all__ = [
    "EvidenceFact",
    "EvidenceConflict",
    "DerivedFact",
    "FusedEvidence",
    "EvidenceFusionEngine",
]
