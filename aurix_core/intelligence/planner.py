"""
AURIX deterministic semantic query planner.

Converts enterprise natural-language questions into a structured
DeterministicQueryPlan without invoking an external LLM.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from aurix_core.intelligence.query_plan import (
    DeterministicOperation,
    DeterministicQueryPlan,
    OutputMode,
    QueryEntity,
    QueryFilter,
    QueryIntent,
    QueryMetric,
    QueryTimeWindow,
)
from aurix_core.intelligence.router import BusinessRouter, PageContext
from aurix_core.tools.registry import ToolRegistry


class DeterministicQueryPlanner:
    """Rule-based semantic planner for high-confidence enterprise queries."""

    ENTITY_PATTERNS = {
        "SKU": r"\bSKU-[A-Z0-9_-]+\b",
        "SUPPLIER": r"\b(?:SUP|SUPPLIER|VENDOR)-[A-Z0-9_-]+\b",
        "PURCHASE_ORDER": r"\bPO-[A-Z0-9_-]+\b",
        "SHIPMENT": r"\b(?:SHPM|SHIP|SHIPMENT)-[A-Z0-9_-]+\b",
        "LOCATION": r"\b(?:DC|NODE)-[A-Z0-9_-]+\b",
    }

    INTENT_PATTERNS = {
        QueryIntent.COMPARE: [
            "compare",
            "versus",
            "vs",
            "difference between",
            "better than",
            "worse than",
        ],
        QueryIntent.RANK: [
            "which",
            "top",
            "bottom",
            "highest",
            "lowest",
            "worst",
            "best",
            "biggest",
            "largest",
            "smallest",
            "rank",
            "ranking",
        ],
        QueryIntent.RECOMMEND: [
            "recommend",
            "recommendation",
            "what should i",
            "what should we",
            "suggest",
            "what action",
            "how should we",
            "how can we fix",
            "what do we do",
        ],
        QueryIntent.DIAGNOSE: [
            "why",
            "root cause",
            "root-cause",
            "driver",
            "reason",
            "causing",
            "problem",
            "issue",
        ],
        QueryIntent.TREND: [
            "trend",
            "trending",
            "over time",
            "trajectory",
            "evolution",
            "month over month",
            "mom",
            "week over week",
            "wow",
        ],
        QueryIntent.SUMMARIZE: [
            "summary",
            "summarize",
            "overview",
            "give me an overview",
            "brief me",
            "status report",
        ],
        QueryIntent.SIMULATE: [
            "what if",
            "simulate",
            "scenario",
            "suppose",
            "if demand",
            "if volume",
            "if lead time",
            "if freight",
        ],
        QueryIntent.EXPLAIN: [
            "explain",
            "why is",
            "why are",
            "how does",
            "how is",
        ],
    }

    METRIC_PATTERNS = {
        "OTIF": ["otif", "on time in full"],
        "OTD": ["otd", "on time delivery"],
        "LEAD_TIME": ["lead time", "lead-time", "delivery time"],
        "RISK_SCORE": ["risk score", "risk level", "risk"],
        "INVENTORY": ["inventory", "stock", "on hand", "on-hand"],
        "SAFETY_STOCK": ["safety stock"],
        "REORDER_POINT": ["reorder point", "rop"],
        "FORECAST": ["forecast", "predicted demand", "projected demand"],
        "ETA": ["eta", "estimated delivery", "delivery date"],
        "WORKING_CAPITAL": ["working capital", "cash tied up"],
        "TCO": ["tco", "total cost of ownership"],
        "COST": ["cost", "spend", "expense"],
        "MARGIN": ["margin", "gross margin"],
        "CAPACITY": ["capacity", "utilization", "bottleneck"],
        "SERVICE_LEVEL": ["service level", "fill rate"],
    }

    TIME_PATTERNS = {
        "CURRENT_MONTH": [
            "this month",
            "current month",
            "month",
        ],
        "PREVIOUS_MONTH": [
            "last month",
            "previous month",
        ],
        "CURRENT_WEEK": [
            "this week",
            "current week",
        ],
        "PREVIOUS_WEEK": [
            "last week",
            "previous week",
        ],
        "TODAY": [
            "today",
        ],
        "YESTERDAY": [
            "yesterday",
        ],
        "CURRENT_QUARTER": [
            "this quarter",
            "current quarter",
        ],
        "PREVIOUS_QUARTER": [
            "last quarter",
            "previous quarter",
        ],
        "CURRENT_YEAR": [
            "this year",
            "current year",
            "ytd",
            "year to date",
        ],
        "LAST_30_DAYS": [
            "last 30 days",
            "past 30 days",
            "previous 30 days",
        ],
        "LAST_90_DAYS": [
            "last 90 days",
            "past 90 days",
            "previous 90 days",
        ],
    }

    OUTPUT_BY_INTENT = {
        QueryIntent.RANK: OutputMode.RANKING,
        QueryIntent.COMPARE: OutputMode.COMPARISON,
        QueryIntent.RECOMMEND: OutputMode.RECOMMENDATION,
        QueryIntent.DIAGNOSE: OutputMode.EXPLANATION,
        QueryIntent.EXPLAIN: OutputMode.EXPLANATION,
        QueryIntent.SUMMARIZE: OutputMode.SUMMARY,
    }

    @classmethod
    def normalize(cls, query: str) -> str:
        return re.sub(r"\s+", " ", query.strip().lower())

    @classmethod
    def extract_entities(cls, query: str) -> List[QueryEntity]:
        entities: List[QueryEntity] = []

        for entity_type, pattern in cls.ENTITY_PATTERNS.items():
            for match in re.findall(pattern, query, re.IGNORECASE):
                entity_id = str(match).upper()

                if entity_type == "SUPPLIER":
                    canonical_type = "SUPPLIER"
                elif entity_type == "PURCHASE_ORDER":
                    canonical_type = "PURCHASE_ORDER"
                elif entity_type == "SHIPMENT":
                    canonical_type = "SHIPMENT"
                elif entity_type == "LOCATION":
                    canonical_type = "LOCATION"
                else:
                    canonical_type = entity_type

                entities.append(
                    QueryEntity(
                        entity_type=canonical_type,
                        entity_id=entity_id,
                        confidence=0.99,
                    )
                )

        unique: Dict[str, QueryEntity] = {}

        for entity in entities:
            if entity.entity_id:
                unique[entity.entity_id] = entity

        return list(unique.values())

    @classmethod
    def infer_intent(cls, query: str) -> QueryIntent:
        for intent, patterns in cls.INTENT_PATTERNS.items():
            if any(pattern in query for pattern in patterns):
                return intent

        if query.startswith(
            (
                "what is",
                "what are",
                "show",
                "get",
                "list",
                "status",
                "how many",
                "current",
            )
        ):
            return QueryIntent.READ

        return QueryIntent.ANALYZE

    @classmethod
    def extract_metrics(cls, query: str) -> List[QueryMetric]:
        metrics: List[QueryMetric] = []

        for name, aliases in cls.METRIC_PATTERNS.items():
            matches = [alias for alias in aliases if alias in query]

            if matches:
                metrics.append(
                    QueryMetric(
                        name=name,
                        aliases=matches,
                        confidence=min(
                            0.99,
                            0.80 + (0.05 * len(matches)),
                        ),
                    )
                )

        return metrics

    @classmethod
    def extract_time_window(
        cls,
        query: str,
    ) -> Optional[QueryTimeWindow]:
        for label, patterns in cls.TIME_PATTERNS.items():
            for pattern in patterns:
                if pattern in query:
                    return QueryTimeWindow(label=label)

        return None

    @classmethod
    def infer_domain(
        cls,
        query: str,
        page_context: Optional[PageContext],
    ) -> Optional[str]:
        routing = BusinessRouter.route(
            query=query,
            page_context=page_context,
        )

        if routing.domain is not None:
            return routing.domain.value

        return None

    @classmethod
    def choose_capability(
        cls,
        query: str,
        domain: Optional[str],
        metrics: List[QueryMetric],
    ) -> Optional[str]:
        metric_names = {metric.name for metric in metrics}

        if "SAFETY_STOCK" in metric_names or "REORDER_POINT" in metric_names:
            return "SAFETY_STOCK_ROP"

        if "FORECAST" in metric_names:
            return "DEMAND_FORECASTING"

        if "OTIF" in metric_names or "OTD" in metric_names:
            return "SUPPLIER_PERFORMANCE_RISK"

        if "ETA" in metric_names:
            return "SHIPMENT_TRACKING_ETA"

        if "CAPACITY" in metric_names:
            return "NETWORK_TOPOLOGY_BOTTLENECK"

        if "WORKING_CAPITAL" in metric_names or "TCO" in metric_names:
            return "WORKING_CAPITAL_TCO"

        if domain == "INVENTORY":
            return "INVENTORY_POSITION_RISK"

        if domain == "SUPPLY":
            return "SUPPLIER_PERFORMANCE_RISK"

        if domain == "LOGISTICS":
            return "SHIPMENT_TRACKING_ETA"

        if domain == "FORECASTING":
            return "DEMAND_FORECASTING"

        if domain == "ECONOMICS":
            return "WORKING_CAPITAL_TCO"

        return "PORTFOLIO_SNAPSHOT"

    @classmethod
    def build_operations(
        cls,
        capability: Optional[str],
        entities: List[QueryEntity],
    ) -> List[DeterministicOperation]:

        if not capability:
            return []

        tool = ToolRegistry.resolve_for_capability(capability)

        if tool is None:
            return []

        entity = entities[0] if entities else None

        return [
            DeterministicOperation(
                operation_id="OP-001",
                tool_name=tool.name,
                capability=capability,
                entity=entity,
                required=True,
            )
        ]

    @classmethod
    def plan(
        cls,
        query: str,
        page_context: Optional[PageContext] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> DeterministicQueryPlan:

        normalized = cls.normalize(query)

        entities = cls.extract_entities(normalized)
        metrics = cls.extract_metrics(normalized)
        intent = cls.infer_intent(normalized)
        time_window = cls.extract_time_window(normalized)

        domain = cls.infer_domain(
            normalized,
            page_context,
        )

        capability = cls.choose_capability(
            normalized,
            domain,
            metrics,
        )

        operations = cls.build_operations(
            capability,
            entities,
        )

        missing: List[str] = []
        warnings: List[str] = []

        tool = (
            ToolRegistry.resolve_for_capability(capability)
            if capability
            else None
        )

        if tool and tool.requires_entity and not entities:
            missing.append("ENTITY")

        if intent in (
            QueryIntent.COMPARE,
            QueryIntent.RANK,
            QueryIntent.TREND,
        ) and not time_window:
            warnings.append(
                "No explicit time window supplied; latest available data will be used."
            )

        if intent == QueryIntent.RECOMMEND:
            warnings.append(
                "Recommendation will remain deterministic and evidence-based."
            )

        confidence = 0.55

        if domain:
            confidence += 0.15

        if capability:
            confidence += 0.15

        if metrics:
            confidence += 0.10

        if entities:
            confidence += 0.05

        if missing:
            confidence -= 0.20

        confidence = max(0.0, min(0.99, confidence))

        requires_cross_entity = intent in {
            QueryIntent.COMPARE,
            QueryIntent.RANK,
        } or len(entities) > 1

        requires_calculation = intent in {
            QueryIntent.ANALYZE,
            QueryIntent.COMPARE,
            QueryIntent.RANK,
            QueryIntent.TREND,
            QueryIntent.DIAGNOSE,
            QueryIntent.RECOMMEND,
            QueryIntent.SIMULATE,
        }

        requires_recommendation = intent == QueryIntent.RECOMMEND

        output_mode = cls.OUTPUT_BY_INTENT.get(
            intent,
            OutputMode.ANSWER,
        )

        return DeterministicQueryPlan(
            query=query,
            normalized_query=normalized,
            intent=intent,
            confidence=confidence,
            entities=entities,
            metrics=metrics,
            time_window=time_window,
            operations=operations,
            output_mode=output_mode,
            requires_historical_data=time_window is not None,
            requires_cross_entity_analysis=requires_cross_entity,
            requires_calculation=requires_calculation,
            requires_recommendation=requires_recommendation,
            missing_requirements=missing,
            warnings=warnings,
            provenance={
                "planner": "AURIX_DETERMINISTIC_SEMANTIC_PLANNER_V1",
                "domain": domain,
                "capability": capability,
                "operation_count": len(operations),
                "conversation_context_available": bool(conversation_history),
            },
        )
