"""
AURIX evidence orchestration layer.

Coordinates semantic interpretation, evidence requirements, and the existing
EvidenceFabric. It never invents missing data.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from aurix_core.intelligence.evidence import EvidenceFabric
from aurix_core.intelligence.evidence_requirements import EvidenceRequirementPlanner
from aurix_core.intelligence.semantic_resolver import SemanticResolver


class EvidenceOrchestrationResult:
    def __init__(
        self,
        semantic: Any,
        evidence: Any,
        requested_sources: list[str],
        resolved_entity_id: Optional[str] = None,
        resolved_location_id: Optional[str] = None,
    ) -> None:
        self.semantic = semantic
        self.evidence = evidence
        self.requested_sources = requested_sources
        self.resolved_entity_id = resolved_entity_id
        self.resolved_location_id = resolved_location_id

    def model_dump(self) -> Dict[str, Any]:
        return {
            "semantic": self.semantic.model_dump(),
            "requested_sources": self.requested_sources,
            "available_sources": self.evidence.available_sources,
            "unavailable_sources": self.evidence.unavailable_sources,
            "resolved_entity_id": self.resolved_entity_id,
            "resolved_location_id": self.resolved_location_id,
        }


class EvidenceOrchestrator:
    """Collects the broadest relevant deterministic evidence available."""

    @staticmethod
    def _classify_entity_roles(
        entities: list[str],
        explicit_entity_id: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Deterministically classify recognized enterprise identifiers.

        This does not modify semantic parsing. It only maps the existing
        entity list into domain-relevant roles for evidence retrieval.

        Returns:
            (entity_id, location_id)
        """

        values = [
            str(value).strip().upper()
            for value in entities
            if value is not None and str(value).strip()
        ]

        explicit = (
            str(explicit_entity_id).strip().upper()
            if explicit_entity_id
            else None
        )

        sku_candidates = [
            value
            for value in values
            if "-SKU-" in value or value.startswith("SKU-")
        ]

        location_candidates = [
            value
            for value in values
            if (
                "-DC-" in value
                or value.startswith("DC-")
                or "-NODE-" in value
                or value.startswith("NODE-")
            )
        ]

        resolved_entity = explicit

        if resolved_entity is None and sku_candidates:
            resolved_entity = sku_candidates[0]

        resolved_location = (
            location_candidates[0]
            if len(location_candidates) == 1
            else None
        )

        return resolved_entity, resolved_location

    @classmethod
    def collect(
        cls,
        db: Any,
        tenant_id: str,
        query: str,
        entity_id: Optional[str] = None,
    ) -> EvidenceOrchestrationResult:

        semantic = SemanticResolver.resolve(query)

        resolved_entity, resolved_location = (
            cls._classify_entity_roles(
                semantic.entities,
                explicit_entity_id=entity_id,
            )
        )

        requested_sources = EvidenceRequirementPlanner.required_sources(
            concepts=semantic.concepts,
            dimensions=semantic.dimensions,
            question_type=semantic.question_type,
        )

        evidence = EvidenceFabric.collect(
            db=db,
            tenant_id=tenant_id,
            query=query,
            sources=requested_sources,
            entity_id=resolved_entity,
            location_id=resolved_location,
        )

        return EvidenceOrchestrationResult(
            semantic=semantic,
            evidence=evidence,
            requested_sources=requested_sources,
            resolved_entity_id=resolved_entity,
            resolved_location_id=resolved_location,
        )
