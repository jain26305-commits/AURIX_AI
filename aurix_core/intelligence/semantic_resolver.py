"""
AURIX deterministic semantic resolver.

Converts natural-language enterprise questions into normalized concepts,
question dimensions, and reasoning requirements.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from aurix_core.intelligence.semantic_lexicon import detect_semantics


ENTITY_PATTERN = r"(?<![A-Z0-9_-])((?:AURIX-[A-Z0-9_-]+-(?:SKU|SUP|PO|SHPM|DC|NODE|WO|INV|ORD)-[A-Z0-9_-]+)|(?:[A-Z0-9]+-(?:SKU|SUP|PO|SHPM|DC|NODE|WO|INV|ORD)-[A-Z0-9_-]+)|(?:(?:SKU|SUP|PO|SHPM|DC|NODE|WO|INV|ORD)-[A-Z0-9_-]+))(?![A-Z0-9_-])"


class SemanticResolution:
    def __init__(
        self,
        query: str,
        concepts: List[str],
        matched_phrases: Dict[str, List[str]],
        entities: List[str],
        dimensions: List[str],
        question_type: str,
        confidence: float,
    ) -> None:
        self.query = query
        self.concepts = concepts
        self.matched_phrases = matched_phrases
        self.entities = entities
        self.dimensions = dimensions
        self.question_type = question_type
        self.confidence = confidence

    def model_dump(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "concepts": self.concepts,
            "matched_phrases": self.matched_phrases,
            "entities": self.entities,
            "dimensions": self.dimensions,
            "question_type": self.question_type,
            "confidence": self.confidence,
        }


class SemanticResolver:
    """Deterministic semantic interpretation of enterprise language."""

    @classmethod
    def resolve(cls, query: str) -> SemanticResolution:
        semantics = detect_semantics(query)
        concepts = semantics["concepts"]
        matched_phrases = semantics["matched_phrases"]

        entities = [
            match.upper()
            for match in re.findall(ENTITY_PATTERN, query, re.IGNORECASE)
        ]

        dimensions: List[str] = []

        if any(
            c in concepts
            for c in (
                "INVENTORY",
                "SAFETY_STOCK",
                "REORDER_POINT",
                "STOCKOUT",
                "COVERAGE",
            )
        ):
            dimensions.append("INVENTORY_POSITION")

        if any(
            c in concepts
            for c in (
                "DEMAND",
                "FORECAST",
                "DEMAND_VARIABILITY",
                "COVERAGE",
            )
        ):
            dimensions.append("DEMAND")

        if any(c in concepts for c in ("SUPPLIER", "SUPPLIER_PERFORMANCE", "OTIF", "LEAD_TIME")):
            dimensions.append("SUPPLIER_PERFORMANCE")

        if any(c in concepts for c in ("SHIPMENT", "ETA", "DELAY")):
            dimensions.append("LOGISTICS")

        if any(c in concepts for c in ("MANUFACTURING", "CAPACITY", "MRP")):
            dimensions.append("MANUFACTURING")

        if any(c in concepts for c in ("NETWORK", "WAREHOUSE", "BULLWHIP")):
            dimensions.append("NETWORK")

        if any(c in concepts for c in ("COST", "WORKING_CAPITAL", "MARGIN")):
            dimensions.append("ECONOMICS")

        # Explicit business-question semantics take precedence over
        # generic domain/risk words.
        if "SIMULATION" in concepts:
            question_type = "SIMULATE"
        elif "COMPARISON" in concepts:
            question_type = "COMPARE"
        elif "SUMMARY" in concepts:
            question_type = "SUMMARIZE"
        elif "RECOMMENDATION" in concepts:
            question_type = "RECOMMEND"
        elif "WHY" in concepts:
            question_type = "DIAGNOSE"
        elif "TREND_REQUEST" in concepts or "TREND" in concepts:
            question_type = "TREND"
        elif "RISK" in concepts:
            question_type = "DIAGNOSE"
        else:
            question_type = "READ"

        # Confidence is intentionally evidence-neutral.
        # It measures semantic interpretation quality.
        score = 0.55

        if concepts:
            score += 0.15

        if dimensions:
            score += 0.10

        if entities:
            score += 0.10

        if question_type in {
            "DIAGNOSE",
            "RECOMMEND",
            "COMPARE",
            "SUMMARIZE",
            "SIMULATE",
            "TREND",
        }:
            score += 0.05

        if len(concepts) >= 3:
            score += 0.05

        # Highly specific semantic relationships increase confidence.
        if "COVERAGE" in concepts and {"INVENTORY", "DEMAND"} <= set(concepts):
            score += 0.04

        if "STOCKOUT" in concepts and "INVENTORY" in concepts:
            score += 0.04

        if "COMPARISON" in concepts and "SUPPLIER" in concepts:
            score += 0.04

        if "ETA" in concepts and "SHIPMENT" in concepts:
            score += 0.04

        if "SUMMARY" in concepts and "RISK" in concepts:
            score += 0.04

        return SemanticResolution(
            query=query,
            concepts=concepts,
            matched_phrases=matched_phrases,
            entities=entities,
            dimensions=list(dict.fromkeys(dimensions)),
            question_type=question_type,
            confidence=min(round(score, 3), 0.99),
        )
