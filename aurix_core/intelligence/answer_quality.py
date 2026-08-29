"""
AURIX deterministic answer quality gate.

Evaluates whether a response is sufficiently supported by deterministic
evidence before the answer is returned as authoritative.
"""

from __future__ import annotations

from typing import Any, Dict, List


class AnswerQualityGate:
    """Scores answerability based on evidence coverage and semantic fit."""

    @classmethod
    def evaluate(
        cls,
        semantic: Any,
        evidence: Any,
        derived_claim_count: int = 0,
    ) -> Dict[str, Any]:

        requested = list(getattr(evidence, "available_sources", [])) + list(
            getattr(evidence, "unavailable_sources", [])
        )

        available = len(getattr(evidence, "available_sources", []))
        unavailable = len(getattr(evidence, "unavailable_sources", []))

        source_coverage = (
            available / len(requested)
            if requested
            else 0.0
        )

        semantic_confidence = float(
            getattr(semantic, "confidence", 0.0)
        )

        # Evidence coverage is useful but not sufficient by itself.
        score = (
            semantic_confidence * 0.45
            + source_coverage * 0.45
            + min(derived_claim_count / 5.0, 1.0) * 0.10
        )

        score = round(min(max(score, 0.0), 1.0), 3)

        if score >= 0.85:
            quality = "HIGH"
        elif score >= 0.65:
            quality = "PARTIAL"
        else:
            quality = "LOW"

        limitations: List[str] = []

        for source in getattr(evidence, "unavailable_sources", []):
            limitations.append(str(source))

        return {
            "answerable": available > 0 and semantic_confidence >= 0.65,
            "confidence": score,
            "evidence_quality": quality,
            "source_coverage": round(source_coverage, 3),
            "available_source_count": available,
            "unavailable_source_count": unavailable,
            "limitations": limitations,
        }
