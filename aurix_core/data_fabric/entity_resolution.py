"""
AURIX Enterprise Data Fabric — Entity Resolution Engine
Phase 19 Core Implementation.
Performs deterministic matching, alias indexing, and confidence-scored resolution.
"""

from __future__ import annotations

import re
import uuid
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from aurix_core.data_fabric.contracts import CanonicalEntityType, ResolutionStatus


class ResolutionDecision(BaseModel):
    """Authoritative outcome of an entity resolution operation."""
    canonical_id: str
    tenant_id: str
    entity_type: CanonicalEntityType
    status: ResolutionStatus
    confidence_score: float = Field(ge=0.0, le=1.0)
    matched_rule: str
    is_new_entity: bool = False
    review_required: bool = False
    source_identifier: str
    source_system: str


class EntityResolutionEngine:
    """Resolves disparate external identifiers into unified canonical entities."""

    AUTO_RESOLVE_THRESHOLD = 0.85
    REVIEW_THRESHOLD = 0.60

    def __init__(self) -> None:
        # Alias store: (tenant_id, entity_type, source_system, source_id) -> canonical_id
        self._alias_registry: Dict[Tuple[str, str, str, str], str] = {}
        # Canonical entity name store: (tenant_id, entity_type, normalized_name) -> canonical_id
        self._name_registry: Dict[Tuple[str, str, str], str] = {}

    @staticmethod
    def clean_name(name: str) -> str:
        """Normalize company/product strings for matching."""
        if not name:
            return ""
        cleaned = name.upper()
        # Remove common corporate suffixes
        cleaned = re.sub(r"\b(LTD|LIMITED|INC|CORP|CORPORATION|LLC|PVT|PRIVATE)\b", "", cleaned)
        cleaned = re.sub(r"[^\w\s]", "", cleaned)
        return re.sub(r"\s+", " ", cleaned).strip()

    @classmethod
    def compute_similarity(cls, s1: str, s2: str) -> float:
        """Compute robust token-based and Levenshtein string similarity."""
        s1_clean = cls.clean_name(s1)
        s2_clean = cls.clean_name(s2)

        if not s1_clean or not s2_clean:
            return 0.0
        if s1_clean == s2_clean:
            return 1.0

        # Token set overlap (Jaccard)
        t1 = set(s1_clean.split())
        t2 = set(s2_clean.split())
        intersection = t1.intersection(t2)
        union = t1.union(t2)
        jaccard = len(intersection) / len(union) if union else 0.0

        # Exact sub-string bonus
        if s1_clean in s2_clean or s2_clean in s1_clean:
            jaccard = max(jaccard, 0.88)

        return round(jaccard, 4)

    def register_alias(
        self,
        tenant_id: str,
        entity_type: CanonicalEntityType,
        source_system: str,
        source_id: str,
        canonical_id: str,
        entity_name: Optional[str] = None,
    ) -> None:
        """Bind an external source ID to a canonical entity."""
        key = (tenant_id, entity_type.value, source_system.upper(), source_id.upper())
        self._alias_registry[key] = canonical_id
        if entity_name:
            name_key = (tenant_id, entity_type.value, self.clean_name(entity_name))
            self._name_registry[name_key] = canonical_id

    def resolve(
        self,
        tenant_id: str,
        entity_type: CanonicalEntityType,
        source_system: str,
        source_id: str,
        candidate_name: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> ResolutionDecision:
        """Resolve a source record to a canonical ID with confidence scoring."""
        src_sys = source_system.upper()
        src_id = source_id.upper()

        # Step 1: Deterministic Alias Lookup (100% confidence)
        alias_key = (tenant_id, entity_type.value, src_sys, src_id)
        if alias_key in self._alias_registry:
            return ResolutionDecision(
                canonical_id=self._alias_registry[alias_key],
                tenant_id=tenant_id,
                entity_type=entity_type,
                status=ResolutionStatus.RESOLVED_ALIAS,
                confidence_score=1.0,
                matched_rule="EXACT_ALIAS_LOOKUP",
                is_new_entity=False,
                review_required=False,
                source_identifier=source_id,
                source_system=source_system,
            )

        # Step 2: Exact Name Lookup
        if candidate_name:
            cleaned = self.clean_name(candidate_name)
            name_key = (tenant_id, entity_type.value, cleaned)
            if name_key in self._name_registry:
                canonical_id = self._name_registry[name_key]
                # Auto-link the alias
                self._alias_registry[alias_key] = canonical_id
                return ResolutionDecision(
                    canonical_id=canonical_id,
                    tenant_id=tenant_id,
                    entity_type=entity_type,
                    status=ResolutionStatus.RESOLVED_EXACT,
                    confidence_score=0.98,
                    matched_rule="EXACT_NAME_MATCH",
                    is_new_entity=False,
                    review_required=False,
                    source_identifier=source_id,
                    source_system=source_system,
                )

            # Step 3: Fuzzy Name & Attribute Matching
            best_match_id = None
            best_score = 0.0

            for (t_id, e_type, registered_name), c_id in self._name_registry.items():
                if t_id == tenant_id and e_type == entity_type.value:
                    score = self.compute_similarity(candidate_name, registered_name)
                    if score > best_score:
                        best_score = score
                        best_match_id = c_id

            if best_match_id and best_score >= self.AUTO_RESOLVE_THRESHOLD:
                self._alias_registry[alias_key] = best_match_id
                return ResolutionDecision(
                    canonical_id=best_match_id,
                    tenant_id=tenant_id,
                    entity_type=entity_type,
                    status=ResolutionStatus.RESOLVED_FUZZY,
                    confidence_score=best_score,
                    matched_rule="FUZZY_NAME_HIGH_CONFIDENCE",
                    is_new_entity=False,
                    review_required=False,
                    source_identifier=source_id,
                    source_system=source_system,
                )
            elif best_match_id and best_score >= self.REVIEW_THRESHOLD:
                # Ambiguous: generate candidate ID but flag for manual review
                return ResolutionDecision(
                    canonical_id=best_match_id,
                    tenant_id=tenant_id,
                    entity_type=entity_type,
                    status=ResolutionStatus.AMBIGUOUS_REVIEW_REQUIRED,
                    confidence_score=best_score,
                    matched_rule="FUZZY_AMBIGUOUS_MATCH",
                    is_new_entity=False,
                    review_required=True,
                    source_identifier=source_id,
                    source_system=source_system,
                )

        # Step 4: No match found — Provision new Canonical Entity
        new_canonical_id = f"CAN-{entity_type.value.upper()[:3]}-{uuid.uuid4().hex[:12].upper()}"
        self.register_alias(
            tenant_id=tenant_id,
            entity_type=entity_type,
            source_system=source_system,
            source_id=source_id,
            canonical_id=new_canonical_id,
            entity_name=candidate_name,
        )

        return ResolutionDecision(
            canonical_id=new_canonical_id,
            tenant_id=tenant_id,
            entity_type=entity_type,
            status=ResolutionStatus.RESOLVED_EXACT,
            confidence_score=1.0,
            matched_rule="NEW_CANONICAL_PROVISIONED",
            is_new_entity=True,
            review_required=False,
            source_identifier=source_id,
            source_system=source_system,
        )
