"""Page-level context builder, fact-pack compiler, and anti-hallucination grounding validator for Phase 9."""

import math
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from aurix_core.intelligence.automation import IntelligenceSnapshot
from aurix_core.intelligence.router import PageContext, RoutingDecision


class FactItem(BaseModel):
    """Atomic verifiable fact derived from authoritative AURIX engine outputs."""
    domain: str
    metric_name: str
    entity_id: Optional[str] = None
    value: Any
    unit: Optional[str] = None
    currency: Optional[str] = None
    value_state: str = "OBSERVED"           # OBSERVED, DERIVED, INFERRED, UNAVAILABLE
    freshness: str = "UNKNOWN"              # LIVE, RECENT, STALE, VERY_STALE, UNKNOWN
    provenance_id: Optional[str] = None


class FactPack(BaseModel):
    """Bounded, minimal context package delivered to the AI layer."""
    pack_id: str
    tenant_id: str
    facts: List[FactItem] = Field(default_factory=list)
    page_context: Optional[PageContext] = None
    active_entity_id: Optional[str] = None
    allowable_entities: Set[str] = Field(default_factory=set)
    provenance_refs: List[str] = Field(default_factory=list)
    generated_at: str

    def to_context_string(self, max_chars: int = 4000, max_estimated_tokens: int = 1000) -> str:
        """Serializes fact pack into a bounded, structured context string for LLM prompts."""
        lines = [
            f"--- AURIX VERIFIED CONTEXT (Tenant: {self.tenant_id}) ---",
            f"Active Entity: {self.active_entity_id or 'PORTFOLIO'}",
            f"Context Generated At: {self.generated_at}",
            "VERIFIED FACTS:",
        ]

        if not self.facts:
            lines.append("  (No specific domain metrics found. Data is UNAVAILABLE.)")
        else:
            char_count = sum(len(ln) for ln in lines)
            for f in self.facts:
                val_repr = "UNAVAILABLE" if f.value_state == "UNAVAILABLE" or f.value is None else str(f.value)
                unit_str = f" {f.unit}" if f.unit else ""
                curr_str = f" {f.currency}" if f.currency else ""
                entry = (
                    f"- [{f.domain}] {f.metric_name} ({f.entity_id or 'GENERAL'}): "
                    f"{val_repr}{unit_str}{curr_str} [State: {f.value_state}, Freshness: {f.freshness}]"
                )

                if (char_count + len(entry) + 30 > max_chars) or (
                    (char_count + len(entry)) / 4 > max_estimated_tokens
                ):
                    lines.append("- [SYSTEM] ... additional facts truncated to respect context budget.")
                    break

                lines.append(entry)
                char_count += len(entry) + 1

        lines.append("--- END CONTEXT ---")
        return "\n".join(lines)


class GroundingValidationResult(BaseModel):
    """Result of validating an AI response against authoritative fact pack assertions."""
    is_grounded: bool
    confidence_score: float = 1.0
    detected_numbers: List[float] = Field(default_factory=list)
    approved_direct_numbers: List[float] = Field(default_factory=list)
    approved_derived_numbers: List[float] = Field(default_factory=list)
    unsupported_numbers: List[float] = Field(default_factory=list)
    detected_entities: List[str] = Field(default_factory=list)
    unsupported_entities: List[str] = Field(default_factory=list)
    violations: List[str] = Field(default_factory=list)
    fallback_required: bool = False


class ContextBuilder:
    """Extracts strictly necessary facts from snapshot and analytical data for AI ingestion."""

    @classmethod
    def build_fact_pack(
        cls,
        tenant_id: str,
        routing_decision: RoutingDecision,
        snapshot: Optional[IntelligenceSnapshot] = None,
        analytical_data: Optional[Dict[str, Any]] = None,
        page_context: Optional[PageContext] = None,
        max_facts: int = 25,
    ) -> FactPack:
        """Compiles a bounded, relevant FactPack preserving exact upstream metadata."""
        pack_id = f"FACT-{uuid.uuid4().hex[:10].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()
        target_entity = routing_decision.resolved_entity_id
        target_domain: Optional[str] = (
            routing_decision.domain.value
            if routing_decision.domain is not None
            else None
        )

        facts: List[FactItem] = []
        provenance_refs: List[str] = []
        allowable_entities: Set[str] = set()

        if target_entity:
            allowable_entities.add(target_entity.upper())

        # 1. Inherit Freshness Map from Snapshot if Available
        freshness_map: Dict[str, str] = getattr(snapshot, "freshness_summary", {}) if snapshot else {}

        # 2. Extract Portfolio KPIs from Snapshot
        if snapshot and not target_entity:
            port_freshness = freshness_map.get("PORTFOLIO", "UNKNOWN")
            facts.append(
                FactItem(
                    domain="PORTFOLIO",
                    metric_name="high_risk_skus_count",
                    value=snapshot.high_risk_skus_count,
                    value_state="DERIVED",
                    freshness=port_freshness,
                )
            )
            facts.append(
                FactItem(
                    domain="PORTFOLIO",
                    metric_name="delayed_shipments_count",
                    value=snapshot.delayed_shipments_count,
                    value_state="DERIVED",
                    freshness=freshness_map.get("SHIPMENT_TRACKING_ETA", port_freshness),
                )
            )
            facts.append(
                FactItem(
                    domain="PORTFOLIO",
                    metric_name="supplier_risks_count",
                    value=snapshot.supplier_risks_count,
                    value_state="DERIVED",
                    freshness=freshness_map.get("SUPPLIER_PERFORMANCE_RISK", port_freshness),
                )
            )

        # 3. Extract Domain Metrics from Analytical Outputs
        data = analytical_data or {}
        for domain_key, domain_payload in data.items():
            if target_domain and domain_key.upper() != target_domain and target_domain != "ECONOMICS":
                continue

            dom_freshness = freshness_map.get(domain_key.upper(), "UNKNOWN")

            if isinstance(domain_payload, dict):
                for metric_k, metric_v in domain_payload.items():
                    if isinstance(metric_v, dict):
                        val = metric_v.get("value")
                        state = metric_v.get("state", "DERIVED" if val is not None else "UNAVAILABLE")
                        f_fresh = metric_v.get("freshness", dom_freshness)
                        unit = metric_v.get("unit")
                        curr = metric_v.get("currency")
                        ent = metric_v.get("entity_id", target_entity)

                        if ent:
                            allowable_entities.add(str(ent).upper())

                        facts.append(
                            FactItem(
                                domain=domain_key.upper(),
                                metric_name=metric_k,
                                entity_id=ent,
                                value=val,
                                unit=unit,
                                currency=curr,
                                value_state=state,
                                freshness=f_fresh,
                                provenance_id=metric_v.get("source"),
                            )
                        )
                    elif isinstance(metric_v, (int, float, str, bool)):
                        facts.append(
                            FactItem(
                                domain=domain_key.upper(),
                                metric_name=metric_k,
                                entity_id=target_entity,
                                value=metric_v,
                                value_state="DERIVED",
                                freshness=dom_freshness,
                            )
                        )

        bounded_facts = facts[:max_facts]

        return FactPack(
            pack_id=pack_id,
            tenant_id=tenant_id,
            facts=bounded_facts,
            page_context=page_context,
            active_entity_id=target_entity,
            allowable_entities=allowable_entities,
            provenance_refs=provenance_refs,
            generated_at=now_iso,
        )


class GroundingValidator:
    """Validates candidate AI responses against direct facts and approved arithmetic derivations."""

    @classmethod
    def extract_numbers(cls, text: str) -> List[float]:
        """Extracts standalone numeric tokens, percentages, and currencies from text."""
        raw_matches = re.findall(r"(?<![a-zA-Z\-_])\b\d+(?:\.\d+)?\b%?", text)
        extracted: List[float] = []

        for m in raw_matches:
            clean = m.replace("%", "").strip()
            try:
                extracted.append(float(clean))
            except ValueError:
                continue

        return extracted

    @classmethod
    def extract_entities(cls, text: str) -> List[str]:
        """Extracts formal AURIX entity identifiers (e.g. SKU-123, SUP-A, DC-1, PO-999)."""
        matches = re.findall(r"\b((?:SKU|SUP|PO|SHPM|DC|NODE)-[A-Z0-9_-]+)\b", text, re.IGNORECASE)
        return [m.upper() for m in matches]

    @classmethod
    def generate_approved_derivations(cls, facts: List[FactItem]) -> Set[float]:
        """Generates approved derived numerical values (ratios, sums, percentages, differences)."""
        numeric_facts: List[float] = [
            float(f.value)
            for f in facts
            if f.value is not None and isinstance(f.value, (int, float))
        ]

        approved: Set[float] = set(numeric_facts)

        for i in [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 7.0, 10.0, 30.0, 365.0]:
            approved.add(i)

        for v in numeric_facts:
            if 0.0 <= v <= 1.0:
                approved.add(round(v * 100.0, 2))
                approved.add(round(v * 100.0, 1))
            if 1.0 < v <= 100.0:
                approved.add(round(v / 100.0, 4))
                approved.add(round(v / 100.0, 2))

        for a in numeric_facts:
            for b in numeric_facts:
                if abs(b) > 1e-6:
                    ratio = a / b
                    approved.add(round(ratio, 1))
                    approved.add(round(ratio, 2))
                    approved.add(float(math.floor(ratio)))
                    approved.add(float(math.ceil(ratio)))
                approved.add(round(a + b, 2))
                approved.add(round(abs(a - b), 2))

        return approved

    @classmethod
    def validate(
        cls,
        ai_response_text: str,
        fact_pack: FactPack,
    ) -> GroundingValidationResult:
        """Validates that all numbers and entities in the AI response match direct facts or approved derivations."""
        if not ai_response_text or not ai_response_text.strip():
            return GroundingValidationResult(
                is_grounded=False,
                confidence_score=0.0,
                violations=["EMPTY_RESPONSE"],
                fallback_required=True,
            )

        allowable_entities: Set[str] = set(fact_pack.allowable_entities)
        if fact_pack.active_entity_id:
            allowable_entities.add(fact_pack.active_entity_id.upper())

        for f in fact_pack.facts:
            if f.entity_id:
                allowable_entities.add(f.entity_id.upper())

        direct_numbers: Set[float] = {
            float(f.value)
            for f in fact_pack.facts
            if f.value is not None and isinstance(f.value, (int, float))
        }
        approved_derivations = cls.generate_approved_derivations(fact_pack.facts)

        resp_numbers = cls.extract_numbers(ai_response_text)
        resp_entities = cls.extract_entities(ai_response_text)

        approved_direct: List[float] = []
        approved_derived: List[float] = []
        unsupported_nums: List[float] = []
        unsupported_ents: List[str] = []
        violations: List[str] = []

        for ent in resp_entities:
            if ent not in allowable_entities and not any(ent in a_ent for a_ent in allowable_entities):
                unsupported_ents.append(ent)
                violations.append(f"UNSUPPORTED_ENTITY_FABRICATED: {ent}")

        for num in resp_numbers:
            if any(abs(num - d) < 0.01 for d in direct_numbers):
                approved_direct.append(num)
                continue

            if any(abs(num - der) < 0.05 for der in approved_derivations):
                approved_derived.append(num)
                continue

            unsupported_nums.append(num)
            violations.append(f"UNSUPPORTED_NUMERIC_CLAIM: {num}")

        is_grounded = len(violations) == 0

        return GroundingValidationResult(
            is_grounded=is_grounded,
            confidence_score=1.0 if is_grounded else 0.0,
            detected_numbers=resp_numbers,
            approved_direct_numbers=approved_direct,
            approved_derived_numbers=approved_derived,
            unsupported_numbers=unsupported_nums,
            detected_entities=resp_entities,
            unsupported_entities=unsupported_ents,
            violations=violations,
            fallback_required=not is_grounded,
        )


class ContextAssemblyEngine:
    """Dynamic context assembler aggregating facts, permissions, and entity data."""

    @classmethod
    def assemble_context(
        cls,
        tenant_id: str,
        user_id: str,
        user_roles: List[str],
        user_permissions: List[str],
        page_context: Optional[Any] = None,
        active_entity_id: Optional[str] = None,
    ) -> FactPack:
        """Constructs an operational FactPack for runtime copilot query evaluation."""
        return FactPack(
            pack_id=f"PACK-{uuid.uuid4().hex[:8].upper()}",
            tenant_id=tenant_id,
            facts=[],
            active_entity_id=active_entity_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
