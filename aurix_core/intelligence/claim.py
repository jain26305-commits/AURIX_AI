"""
AURIX Deterministic Claim Contracts.

A claim is the smallest business conclusion that AURIX is allowed
to present to a user. Every claim is explicitly tied to evidence,
confidence and missing-data constraints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DeterministicClaim:
    statement: str
    category: str
    confidence: float

    evidence_refs: List[str] = field(default_factory=list)
    missing_evidence: List[str] = field(default_factory=list)

    supported: bool = True
    allowable_in_answer: bool = True

    impact: Optional[str] = None
    severity: str = "INFO"

    # Canonical evidence/freshness metadata.
    # These fields carry upstream metadata only.
    # Freshness is evaluated exclusively by DataReadinessEngine.
    freshness_state: str = "UNKNOWN"
    freshness_age_hours: Optional[float] = None
    observation_timestamp: Optional[str] = None

    source: Optional[str] = None
    tenant_id: Optional[str] = None
    location_id: Optional[str] = None
    provenance: dict = field(default_factory=dict)
