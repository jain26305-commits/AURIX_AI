"""
AURIX semantic business lexicon.

Maps natural-language variants, abbreviations, operational terminology,
and business expressions into normalized enterprise concepts.

This is deliberately deterministic:
same input -> same semantic interpretation.
"""

from __future__ import annotations

import re
from typing import Dict, List


SEMANTIC_GROUPS: Dict[str, List[str]] = {
    # -----------------------------
    # INVENTORY
    # -----------------------------
    "INVENTORY": [
        "inventory",
        "stock",
        "stock level",
        "stock position",
        "inventory position",
        "available inventory",
        "available stock",
        "stock balance",
        "inventory balance",
        "quantity on hand",
        "on hand",
        "oh",
        "physical stock",
        "physical inventory",
        "warehouse stock",
        "warehouse inventory",
        "goods on hand",
    ],

    "SAFETY_STOCK": [
        "buffer",
        "how much buffer",
        "how much safety stock",
        "buffer remaining",
        "remaining buffer",
        "safety stock",
        "buffer stock",
        "buffer inventory",
        "protective stock",
        "minimum buffer",
        "safety inventory",
        "inventory buffer",
        "stock buffer",
    ],

    "REORDER_POINT": [
        "reorder point",
        "rop",
        "reorder level",
        "replenishment trigger",
        "order trigger",
        "stock trigger",
        "inventory trigger",
        "when should we reorder",
        "when to reorder",
    ],

    "STOCKOUT": [
        "running low",
        "running short",
        "low on stock",
        "low stock",
        "low inventory",
        "inventory is low",
        "inventory is tight",
        "stock is tight",
        "short on stock",
        "short on inventory",
        "not enough stock",
        "not enough inventory",
        "insufficient stock",
        "insufficient inventory",
        "inventory constraint",
        "supply constraint",
        "stockout",
        "stock out",
        "stock-out",
        "out of stock",
        "run out",
        "running out",
        "will run out",
        "inventory depletion",
        "depletion",
        "shortage",
        "shortfall",
        "inventory shortage",
        "stock shortage",
    ],

    "EXCESS_INVENTORY": [
        "excess inventory",
        "overstock",
        "overstocked",
        "too much inventory",
        "surplus stock",
        "inventory surplus",
        "dead stock",
        "slow moving",
        "slow-moving",
        "obsolete stock",
        "inventory accumulation",
    ],

    "INBOUND": [
        "on order",
        "open orders",
        "incoming stock",
        "inbound stock",
        "inbound inventory",
        "pipeline inventory",
        "purchase orders",
        "open po",
        "open pos",
        "po pipeline",
        "incoming supply",
    ],

    "COVERAGE": [
        "cover demand",
        "cover demand with",
        "demand coverage",
        "how long will inventory last",
        "how long will stock last",
        "how much demand can we cover",
        "will inventory cover",
        "days of cover",
        "days cover",
        "inventory coverage",
        "stock coverage",
        "forward cover",
        "coverage",
        "runway",
        "inventory runway",
        "supply runway",
    ],

    # -----------------------------
    # DEMAND / FORECAST
    # -----------------------------
    "DEMAND": [
        "demand",
        "sales demand",
        "customer demand",
        "consumption",
        "usage",
        "run rate",
        "sales velocity",
        "demand rate",
        "daily demand",
        "weekly demand",
        "monthly demand",
        "offtake",
    ],

    "FORECAST": [
        "forecast",
        "forecasting",
        "predicted demand",
        "projected demand",
        "expected demand",
        "future demand",
        "demand outlook",
        "sales outlook",
        "projection",
        "demand projection",
        "forecasted sales",
    ],

    "DEMAND_VARIABILITY": [
        "demand variability",
        "demand volatility",
        "demand uncertainty",
        "demand fluctuation",
        "volatile demand",
        "unstable demand",
        "sales volatility",
        "forecast uncertainty",
    ],

    # -----------------------------
    # SUPPLIER
    # -----------------------------
    "SUPPLIER": [
        "supplier",
        "vendor",
        "source",
        "supplier base",
        "vendor base",
        "sourcing partner",
        "supply partner",
        "manufacturer",
        "contract manufacturer",
    ],

    "SUPPLIER_PERFORMANCE": [
        "supplier performance",
        "vendor performance",
        "supplier scorecard",
        "vendor scorecard",
        "supplier reliability",
        "vendor reliability",
        "supplier service",
        "vendor service",
        "supplier risk",
        "vendor risk",
    ],

    "OTIF": [
        "otif",
        "on time in full",
        "on-time in-full",
        "on time and in full",
        "delivery performance",
        "service performance",
    ],

    "LEAD_TIME": [
        "lead time",
        "lead-time",
        "supplier lead time",
        "procurement lead time",
        "replenishment lead time",
        "cycle time",
        "turnaround time",
        "delivery time",
    ],

    # -----------------------------
    # LOGISTICS
    # -----------------------------
    "SHIPMENT": [
        "shipment",
        "consignment",
        "delivery",
        "dispatch",
        "freight movement",
        "transport movement",
        "load",
        "truck",
        "container",
    ],

    "ETA": [
        "arrive",
        "arrival",
        "arriving",
        "when does it arrive",
        "when will the shipment arrive",
        "eta",
        "estimated arrival",
        "estimated delivery",
        "arrival time",
        "delivery date",
        "expected arrival",
        "expected delivery",
        "when will it arrive",
    ],

    "DELAY": [
        "delay",
        "delayed",
        "late",
        "behind schedule",
        "delivery slippage",
        "transit delay",
        "late delivery",
        "missed delivery",
    ],

    # -----------------------------
    # PROCUREMENT
    # -----------------------------
    "PURCHASE_ORDER": [
        "purchase order",
        "purchase orders",
        "po",
        "pos",
        "procurement order",
        "buy order",
        "supplier order",
    ],

    "PROCUREMENT": [
        "procurement",
        "purchasing",
        "buying",
        "sourcing",
        "purchase planning",
    ],

    # -----------------------------
    # MANUFACTURING
    # -----------------------------
    "MANUFACTURING": [
        "manufacturing",
        "production",
        "factory",
        "plant",
        "assembly",
        "production planning",
        "manufacturing planning",
    ],

    "CAPACITY": [
        "capacity",
        "available capacity",
        "production capacity",
        "machine capacity",
        "work center capacity",
        "resource capacity",
        "utilization",
        "load",
        "capacity constraint",
        "capacity shortage",
        "bottleneck",
    ],

    "MRP": [
        "mrp",
        "material requirements planning",
        "material requirement",
        "material requirements",
        "net requirement",
        "planned order",
        "material plan",
    ],

    # -----------------------------
    # NETWORK
    # -----------------------------
    "NETWORK": [
        "network",
        "distribution network",
        "supply network",
        "supply chain network",
        "distribution footprint",
        "node",
        "nodes",
        "facility network",
    ],

    "WAREHOUSE": [
        "warehouse",
        "dc",
        "distribution center",
        "distribution centre",
        "fulfillment center",
        "fulfilment center",
        "hub",
        "storage location",
    ],

    "BULLWHIP": [
        "bullwhip",
        "bullwhip effect",
        "demand amplification",
        "order amplification",
        "demand distortion",
    ],

    # -----------------------------
    # FINANCE
    # -----------------------------
    "COST": [
        "cost",
        "cost impact",
        "expense",
        "spend",
        "cost exposure",
        "cost burden",
        "cost implication",
    ],

    "WORKING_CAPITAL": [
        "working capital",
        "cash tied up",
        "cash tied in inventory",
        "inventory investment",
        "capital tied up",
        "cash conversion",
    ],

    "MARGIN": [
        "margin",
        "profit margin",
        "gross margin",
        "contribution margin",
        "profitability",
        "profit impact",
    ],

    # -----------------------------
    # RISK / PERFORMANCE
    # -----------------------------
    "RISK": [
        "inventory pressure",
        "supply pressure",
        "inventory risk",
        "risk",
        "at risk",
        "risk exposure",
        "exposure",
        "vulnerability",
        "threat",
        "concern",
        "problem",
        "issue",
        "flagged",
        "warning",
        "red flag",
    ],

    "TREND": [
        "trend",
        "direction",
        "trajectory",
        "improving",
        "worsening",
        "deteriorating",
        "getting better",
        "getting worse",
        "movement over time",
    ],

    "ANOMALY": [
        "anomaly",
        "outlier",
        "abnormal",
        "unusual",
        "unexpected",
        "deviation",
        "variance",
    ],

    # -----------------------------
    # BUSINESS QUESTIONS
    # -----------------------------
    "WHY": [
        "why",
        "why is",
        "why are",
        "reason",
        "reason for",
        "cause",
        "root cause",
        "driver",
        "drivers",
        "what is causing",
        "what caused",
    ],

    "RECOMMENDATION": [
        "what do you recommend",
        "what would you recommend",
        "what is the best action",
        "what is our best option",
        "how should we handle this",
        "what should happen next",
        "recommend",
        "recommendation",
        "what should we do",
        "what should i do",
        "next step",
        "next action",
        "how should we respond",
        "how do we fix",
        "how to fix",
        "what action",
        "what do you suggest",
        "suggest",
        "best action",
    ],

    "COMPARISON": [
        "more reliable",
        "less reliable",
        "most reliable",
        "least reliable",
        "stronger supplier",
        "weaker supplier",
        "best supplier",
        "worst supplier",
        "top supplier",
        "bottom supplier",
        "compare",
        "comparison",
        "versus",
        "vs",
        "difference",
        "which is better",
        "better than",
        "rank",
        "ranking",
        "highest",
        "lowest",
        "best",
        "worst",
    ],

    "SUMMARY": [
        "executive risk summary",
        "executive summary",
        "portfolio risk summary",
        "risk overview",
        "portfolio overview",
        "management summary",
        "leadership summary",
        "business overview",
        "summary",
        "summarize",
        "overview",
        "brief",
        "snapshot",
        "high level",
        "executive view",
        "portfolio view",
        "big picture",
    ],

    "TREND_REQUEST": [
        "trend",
        "over time",
        "history",
        "historical",
        "how has it changed",
        "what changed",
        "change over time",
        "month over month",
        "mom",
        "year over year",
        "yoy",
    ],

    "SIMULATION": [
        "what if",
        "suppose",
        "scenario",
        "simulate",
        "simulation",
        "if demand increases",
        "if demand falls",
        "if lead time increases",
        "if freight increases",
        "impact if",
    ],
}


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[-_/]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def detect_semantics(text: str) -> Dict[str, List[str]]:
    """
    Returns normalized semantic concepts detected in user language.

    Output:
        {
            "concepts": ["INVENTORY", "RISK"],
            "matched_phrases": {
                "INVENTORY": [...],
                "RISK": [...]
            }
        }
    """
    clean = _normalize(text)
    matched: Dict[str, List[str]] = {}

    for concept, phrases in SEMANTIC_GROUPS.items():
        hits: List[str] = []

        for phrase in phrases:
            normalized_phrase = _normalize(phrase)

            if " " in normalized_phrase:
                if normalized_phrase in clean:
                    hits.append(phrase)
            else:
                if re.search(rf"\b{re.escape(normalized_phrase)}\b", clean):
                    hits.append(phrase)

        if hits:
            matched[concept] = hits

    return {
        "concepts": sorted(matched.keys()),
        "matched_phrases": matched,
    }


def canonical_concepts(text: str) -> List[str]:
    return detect_semantics(text)["concepts"]


def has_concept(text: str, concept: str) -> bool:
    return concept.upper() in canonical_concepts(text)
