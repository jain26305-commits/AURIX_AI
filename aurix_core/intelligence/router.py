"""AURIX Business Router: Intent classification, confidence scoring, capability gating, and memory-aware routing."""

import re
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from aurix_core.intelligence.discovery import CapabilityStatus, Domain


class QueryType(str, Enum):
    """Classified business intent of the user query."""
    READ = "READ"                                      # Direct data/metric retrieval (Fast-Path eligible)
    ANALYZE = "ANALYZE"                                # Analytical breakdown across variables
    EXPLAIN = "EXPLAIN"                                # Root-cause and justification explanations
    REASON = "EXPLAIN"                                 # Alias for deep reasoning / explain queries
    COMPARE = "COMPARE"                                # Multi-entity or multi-period comparison
    SIMULATE = "SIMULATE"                              # What-if scenario modeling
    RECOMMEND = "RECOMMEND"                            # Action recommendation requests
    WRITE = "WRITE"                                    # Operational modification requests (Blocked/Gated)
    DESTRUCTIVE = "DESTRUCTIVE"                        # Deletion/reset commands (Strictly Rejected)
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"  # Ambiguous or incomplete input
    OUT_OF_SCOPE = "OUT_OF_SCOPE"                      # Unrelated or general knowledge queries


class RouterConfidence(str, Enum):
    """Routing confidence level."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


# Export alias for backward and gateway compatibility
RoutingConfidence = RouterConfidence


class PageContext(BaseModel):
    """Structured context passed from the active client page or dashboard view."""
    current_page: Optional[str] = None
    current_module: Optional[str] = None
    active_entity_type: Optional[str] = None
    active_entity_id: Optional[str] = None
    active_filters: Dict[str, Any] = Field(default_factory=dict)


class RoutingDecision(BaseModel):
    """Deterministic routing decision and execution directives."""
    query: str
    query_type: QueryType
    domain: Optional[Domain] = None
    target_capability: Optional[str] = None
    confidence: RouterConfidence
    requires_ai: bool = False
    fast_path_eligible: bool = False
    capability_available: bool = True
    resolved_entity_id: Optional[str] = None
    resolved_entity_type: Optional[str] = None
    context_source: str = "DIRECT_QUERY"               # DIRECT_QUERY, PAGE_CONTEXT, CONVERSATION_MEMORY
    rejection_reason: Optional[str] = None
    clarification_prompt: Optional[str] = None
    routing_metadata: Dict[str, Any] = Field(default_factory=dict)


class BusinessRouter:
    """Classifies user queries, evaluates capability availability, and enforces fast-path bypass."""

    DESTRUCTIVE_KEYWORDS = ["delete", "drop", "truncate", "purge", "erase", "remove all", "destroy"]
    WRITE_KEYWORDS = ["update", "insert", "create po", "execute transfer", "modify", "alter", "write to erp"]
    SIMULATE_KEYWORDS = ["what if", "simulate", "scenario", "suppose", "if demand increases", "if freight", "increase"]
    COMPARE_KEYWORDS = ["compare", "versus", "vs", "difference between", "better than"]
    EXPLAIN_KEYWORDS = ["why", "explain", "reason for", "cause of", "how come", "driver behind"]
    RECOMMEND_KEYWORDS = ["recommend", "should i", "suggest", "which supplier", "what action", "how to fix"]
    READ_KEYWORDS = ["what is", "get", "show", "current", "list", "lookup", "value of", "how many", "status of"]

    PRONOUN_TRIGGERS = [
        "this", "it", "that", "the item", "the part", "the sku", "the supplier",
        "the vendor", "the shipment", "the lane", "the dc", "the node", "here", "them"
    ]

    DOMAIN_PATTERNS: Dict[Domain, List[str]] = {
        Domain.FORECASTING: ["forecast", "predicted demand", "horizon", "champion model", "future sales"],
        Domain.INVENTORY: [
            "inventory", "stock", "safety stock", "rop", "reorder point", "stockout", "excess", "on hand"
        ],
        Domain.SUPPLY: ["supplier", "vendor", "purchase order", "po", "lead time variance", "otd", "allocation"],
        Domain.LOGISTICS: ["shipment", "carrier", "eta", "transit", "freight", "delivery date", "lane", "tracking"],
        Domain.NETWORK: [
            "network", "bottleneck", "node", "facility", "single source", "dc", "warehouse", "bullwhip"
        ],
        Domain.DECISION: ["rebalance", "transfer", "lateral move", "rebalancing candidate"],
        Domain.ECONOMICS: ["working capital", "tco", "holding cost", "financial exposure", "spend", "cost impact"],
    }

    DEFAULT_CAPABILITY_MAP: Dict[Domain, str] = {
        Domain.FORECASTING: "DEMAND_FORECASTING",
        Domain.INVENTORY: "SAFETY_STOCK_ROP",
        Domain.SUPPLY: "SUPPLIER_PERFORMANCE_RISK",
        Domain.LOGISTICS: "SHIPMENT_TRACKING_ETA",
        Domain.NETWORK: "NETWORK_TOPOLOGY_BOTTLENECK",
        Domain.DECISION: "INVENTORY_REBALANCING",
        Domain.ECONOMICS: "WORKING_CAPITAL_TCO",
    }

    ENTITY_REGEX = r"\b((?:SKU|SUP|PO|SHPM|DC|NODE)-[A-Z0-9_-]+)\b"

    @classmethod
    def _extract_entity_from_text(cls, text: str) -> Optional[str]:
        """Extracts canonical AURIX entity identifier from a text string."""
        match = re.search(cls.ENTITY_REGEX, text, re.IGNORECASE)
        return match.group(1).upper() if match else None

    @classmethod
    def _resolve_from_conversation(
        cls, conversation_history: List[Dict[str, Any]]
    ) -> Tuple[Optional[str], Optional[Domain]]:
        """Extracts the most recently discussed entity and domain from chronological conversation messages."""
        if not conversation_history:
            return None, None

        for msg in reversed(conversation_history):
            content = str(msg.get("content", ""))
            ent = cls._extract_entity_from_text(content)
            if ent:
                detected_dom: Optional[Domain] = None
                clean_content = content.lower()
                for dom, patterns in cls.DOMAIN_PATTERNS.items():
                    if any(re.search(rf"\b{p}\b", clean_content) for p in patterns):
                        detected_dom = dom
                        break

                return ent, detected_dom

        return None, None

    @classmethod
    def route(
        cls,
        query: str,
        page_context: Optional[PageContext] = None,
        capability_states: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> RoutingDecision:
        """Evaluates a user query with multi-turn memory, page context, and safety rules."""
        clean_query = query.strip().lower()
        cap_map = capability_states or {}

        if not clean_query:
            return RoutingDecision(
                query=query,
                query_type=QueryType.CLARIFICATION_REQUIRED,
                confidence=RouterConfidence.LOW,
                clarification_prompt="Please provide a query regarding your supply chain or operations.",
            )

        # 1. Intercept Destructive Queries
        if any(re.search(rf"\b{kw}\b", clean_query) for kw in cls.DESTRUCTIVE_KEYWORDS):
            return RoutingDecision(
                query=query,
                query_type=QueryType.DESTRUCTIVE,
                confidence=RouterConfidence.HIGH,
                requires_ai=False,
                capability_available=False,
                rejection_reason="Destructive database operations and deletions are strictly blocked.",
            )

        # 2. Intercept Direct Operational Writes
        if any(re.search(rf"\b{kw}\b", clean_query) for kw in cls.WRITE_KEYWORDS):
            return RoutingDecision(
                query=query,
                query_type=QueryType.WRITE,
                confidence=RouterConfidence.HIGH,
                requires_ai=False,
                capability_available=False,
                rejection_reason="Direct operational ERP/WMS write operations are not supported in Phase 9.",
            )

        # 3. Entity Resolution Hierarchy
        detected_entity = cls._extract_entity_from_text(query)
        resolved_entity_id: Optional[str] = detected_entity
        resolved_entity_type: Optional[str] = None
        context_source = "DIRECT_QUERY"

        uses_referent = any(re.search(rf"\b{t}\b", clean_query) for t in cls.PRONOUN_TRIGGERS)

        if not resolved_entity_id and uses_referent:
            if page_context and page_context.active_entity_id:
                resolved_entity_id = page_context.active_entity_id.upper()
                resolved_entity_type = page_context.active_entity_type
                context_source = "PAGE_CONTEXT"
            elif conversation_history:
                conv_ent, _ = cls._resolve_from_conversation(conversation_history)
                if conv_ent:
                    resolved_entity_id = conv_ent
                    context_source = "CONVERSATION_MEMORY"

        # 4. Domain Resolution Hierarchy
        detected_domain: Optional[Domain] = None
        for domain, patterns in cls.DOMAIN_PATTERNS.items():
            if any(re.search(rf"\b{p}\b", clean_query) for p in patterns):
                detected_domain = domain
                break

        if detected_domain is None and page_context and page_context.current_page:
            page_clean = page_context.current_page.upper()
            for d in Domain:
                if d.value in page_clean:
                    detected_domain = d
                    break

        if detected_domain is None and conversation_history:
            _, conv_dom = cls._resolve_from_conversation(conversation_history)
            if conv_dom:
                detected_domain = conv_dom

        # 5. Classify Intent & Evaluate Fast-Path
        query_type = QueryType.ANALYZE
        confidence = RouterConfidence.HIGH
        fast_path = False
        requires_ai = True

        if any(kw in clean_query for kw in cls.SIMULATE_KEYWORDS):
            query_type = QueryType.SIMULATE
        elif any(kw in clean_query for kw in cls.COMPARE_KEYWORDS):
            query_type = QueryType.COMPARE
        elif any(clean_query.startswith(kw) or f" {kw} " in clean_query for kw in cls.EXPLAIN_KEYWORDS):
            query_type = QueryType.EXPLAIN
        elif any(clean_query.startswith(kw) or f" {kw} " in clean_query for kw in cls.RECOMMEND_KEYWORDS):
            query_type = QueryType.RECOMMEND
        elif any(clean_query.startswith(kw) for kw in cls.READ_KEYWORDS) and (resolved_entity_id or detected_domain):
            query_type = QueryType.READ
            fast_path = True
            requires_ai = False
        elif detected_domain is None and not resolved_entity_id:
            if any(w in clean_query for w in ["hello", "hi", "weather", "who are you", "joke"]):
                query_type = QueryType.OUT_OF_SCOPE
                confidence = RouterConfidence.OUT_OF_SCOPE
                requires_ai = False
            else:
                query_type = QueryType.CLARIFICATION_REQUIRED
                confidence = RouterConfidence.LOW
                requires_ai = False

        # 6. Capability Availability Check
        target_cap = cls.DEFAULT_CAPABILITY_MAP.get(detected_domain) if detected_domain else None
        capability_available = True
        rejection_reason = None

        if target_cap and target_cap in cap_map:
            cap_info = cap_map[target_cap]
            status_val = getattr(
                cap_info,
                "status",
                cap_info.get("status") if isinstance(cap_info, dict) else None,
            )
            if status_val in (
                CapabilityStatus.UNAVAILABLE.value,
                CapabilityStatus.BLOCKED.value,
                CapabilityStatus.WAITING_FOR_INPUT.value,
                CapabilityStatus.INSUFFICIENT_EVIDENCE.value,
            ):
                capability_available = False
                rejection_reason = (
                    f"Capability {target_cap} is currently {status_val}. "
                    "Additional canonical data is required."
                )

        prompt_str = (
            "Could you specify the SKU, supplier, or location you want to analyze?"
            if query_type == QueryType.CLARIFICATION_REQUIRED
            else None
        )

        return RoutingDecision(
            query=query,
            query_type=query_type,
            domain=detected_domain,
            target_capability=target_cap,
            confidence=confidence,
            requires_ai=requires_ai,
            fast_path_eligible=fast_path,
            capability_available=capability_available,
            resolved_entity_id=resolved_entity_id,
            resolved_entity_type=resolved_entity_type,
            context_source=context_source,
            rejection_reason=rejection_reason,
            clarification_prompt=prompt_str,
            routing_metadata={
                "page_context_applied": page_context is not None,
                "conversation_memory_applied": context_source == "CONVERSATION_MEMORY",
                "detected_entity": detected_entity,
            },
        )