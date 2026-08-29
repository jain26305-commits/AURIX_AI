"""
Context-aware AURIX entity resolution.

Resolution hierarchy:

1. Explicit entity in current query
2. Typed contextual referent + page context
3. Typed contextual referent + conversation memory
4. Generic conversational reference + conversation memory
5. Explicit clarification requirement

The resolver is intentionally conservative:
it never invents an entity that was not present in the query,
page context, or conversation history.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


class EntityResolution:
    """Result of deterministic entity resolution."""

    def __init__(
        self,
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        source: str = "NONE",
        confidence: float = 0.0,
        clarification_required: bool = False,
    ) -> None:
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.source = source
        self.confidence = confidence
        self.clarification_required = clarification_required

    def __repr__(self) -> str:
        return (
            "EntityResolution("
            f"entity_id={self.entity_id!r}, "
            f"entity_type={self.entity_type!r}, "
            f"source={self.source!r}, "
            f"confidence={self.confidence!r}, "
            f"clarification_required={self.clarification_required!r}"
            ")"
        )


class ContextEntityResolver:
    """
    Deterministic resolver for explicit and conversational AURIX entities.
    """

    # Canonical identifiers used throughout AURIX.
    #
    # Important:
    #   AURIX-E2E-SKU-002 must be matched as one complete entity.
    #   The expression deliberately checks the AURIX form before generic
    #   SKU/SUP/SHPM identifiers.
    ENTITY_REGEX = re.compile(
        r"(?<![A-Z0-9_-])("
        r"AURIX-[A-Z0-9_-]+-(?:SKU|SUP|PO|SHPM|DC|NODE|WO|INV|ORD)-[A-Z0-9_-]+"
        r"|"
        r"(?:SKU|SUP|PO|SHPM|DC|NODE|WO|INV|ORD)-[A-Z0-9_-]+"
        r")"
        r"(?![A-Z0-9_-])",
        re.IGNORECASE,
    )

    # Strong typed contextual references.
    TYPED_REFERENTS = {
        "SKU": (
            r"\bthis sku\b",
            r"\bthe sku\b",
            r"\bthis item\b",
            r"\bthe item\b",
            r"\bthis product\b",
            r"\bthe product\b",
        ),
        "SUPPLIER": (
            r"\bthis supplier\b",
            r"\bthe supplier\b",
            r"\bthis vendor\b",
            r"\bthe vendor\b",
        ),
        "SHIPMENT": (
            r"\bthis shipment\b",
            r"\bthe shipment\b",
            r"\bthis delivery\b",
            r"\bthe delivery\b",
        ),
        "LOCATION": (
            r"\bthis location\b",
            r"\bthe location\b",
            r"\bthis dc\b",
            r"\bthe dc\b",
            r"\bthis warehouse\b",
            r"\bthe warehouse\b",
        ),
        "ORDER": (
            r"\bthis order\b",
            r"\bthe order\b",
            r"\bthis po\b",
            r"\bthe po\b",
            r"\bthis purchase order\b",
            r"\bthe purchase order\b",
        ),
        "WORK_ORDER": (
            r"\bthis work order\b",
            r"\bthe work order\b",
        ),
        "INVOICE": (
            r"\bthis invoice\b",
            r"\bthe invoice\b",
        ),
    }

    # Generic references cannot determine type on their own.
    GENERIC_REFERENTS = (
        r"\bit\b",
        r"\bthis\b",
        r"\bthat\b",
        r"\bthat one\b",
        r"\bthe same one\b",
        r"\bthe same\b",
    )

    ENTITY_TYPE_PREFIXES = {
        "SUP-": "SUPPLIER",
        "SHPM-": "SHIPMENT",
        "SKU-": "SKU",
        "PO-": "ORDER",
        "ORD-": "ORDER",
        "WO-": "WORK_ORDER",
        "INV-": "INVOICE",
        "DC-": "LOCATION",
        "NODE-": "LOCATION",
    }

    @classmethod
    def explicit_entity(cls, query: str) -> Optional[str]:
        """Extract the first complete canonical AURIX entity."""
        match = cls.ENTITY_REGEX.search(query or "")
        return match.group(1).upper() if match else None

    @classmethod
    def infer_entity_type(cls, entity_id: Optional[str]) -> Optional[str]:
        """
        Infer entity type from a canonical identifier.

        Supports AURIX-prefixed identifiers such as:
        AURIX-E2E-SKU-002
        """
        if not entity_id:
            return None

        upper = entity_id.upper()

        for prefix, entity_type in cls.ENTITY_TYPE_PREFIXES.items():
            if upper.startswith(prefix):
                return entity_type

        # AURIX-E2E-SKU-002 / AURIX-XYZ-SUP-001 etc.
        for prefix, entity_type in cls.ENTITY_TYPE_PREFIXES.items():
            if f"-{prefix}" in upper:
                return entity_type

        return None

    @classmethod
    def detect_typed_referent(
        cls,
        query: str,
    ) -> Optional[str]:
        """Return the semantic entity type implied by typed language."""
        clean = (query or "").lower()

        for entity_type, patterns in cls.TYPED_REFERENTS.items():
            if any(re.search(pattern, clean) for pattern in patterns):
                return entity_type

        return None

    @classmethod
    def has_generic_referent(cls, query: str) -> bool:
        """Detect generic conversational references such as 'it' or 'that'."""
        clean = (query or "").lower()
        return any(re.search(pattern, clean) for pattern in cls.GENERIC_REFERENTS)

    @classmethod
    def _is_compatible(
        cls,
        entity_id: str,
        expected_type: Optional[str],
    ) -> bool:
        """
        Check whether an entity can satisfy a requested semantic type.
        """
        if expected_type is None:
            return True

        actual_type = cls.infer_entity_type(entity_id)

        if actual_type is None:
            return False

        aliases = {
            "SKU": {"SKU"},
            "SUPPLIER": {"SUPPLIER"},
            "SHIPMENT": {"SHIPMENT"},
            "LOCATION": {"LOCATION"},
            "ORDER": {"ORDER"},
            "WORK_ORDER": {"WORK_ORDER"},
            "INVOICE": {"INVOICE"},
        }

        return actual_type in aliases.get(
            expected_type,
            {expected_type},
        )

    @classmethod
    def _resolve_from_history(
        cls,
        conversation_history: List[Dict[str, Any]],
        expected_type: Optional[str] = None,
    ) -> Optional[EntityResolution]:
        """
        Search the conversation backwards for the most recent compatible
        explicit AURIX entity.
        """
        if not conversation_history:
            return None

        for message in reversed(conversation_history):
            content = str(message.get("content", ""))
            entity = cls.explicit_entity(content)

            if not entity:
                continue

            inferred_type = cls.infer_entity_type(entity)

            if expected_type and not cls._is_compatible(
                entity,
                expected_type,
            ):
                continue

            return EntityResolution(
                entity_id=entity,
                entity_type=inferred_type,
                source="CONVERSATION_MEMORY",
                confidence=0.92 if expected_type else 0.90,
                clarification_required=False,
            )

        return None

    @classmethod
    def resolve(
        cls,
        query: str,
        page_context: Optional[Any] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> EntityResolution:
        """
        Resolve an entity deterministically.

        Explicit query entity always wins over context.
        """

        clean_query = (query or "").strip()

        # --------------------------------------------------------------
        # 1. Explicit entity in current query.
        # --------------------------------------------------------------
        explicit = cls.explicit_entity(clean_query)

        if explicit:
            return EntityResolution(
                entity_id=explicit,
                entity_type=cls.infer_entity_type(explicit),
                source="QUERY",
                confidence=1.0,
                clarification_required=False,
            )

        # --------------------------------------------------------------
        # 2. Typed referent.
        # --------------------------------------------------------------
        typed_type = cls.detect_typed_referent(clean_query)

        if typed_type:
            # 2A. Page context is the strongest implicit source.
            if page_context is not None:
                active_id = getattr(
                    page_context,
                    "active_entity_id",
                    None,
                )
                active_type = getattr(
                    page_context,
                    "active_entity_type",
                    None,
                )

                if active_id:
                    active_id_str = str(active_id).upper()

                    context_type = (
                        str(active_type).upper()
                        if active_type
                        else cls.infer_entity_type(active_id_str)
                    )

                    compatible = (
                        cls._is_compatible(
                            active_id_str,
                            typed_type,
                        )
                        or (
                            typed_type == "SKU"
                            and context_type in {
                                "PRODUCT",
                                "ITEM",
                                "SKU",
                            }
                        )
                    )

                    if compatible:
                        return EntityResolution(
                            entity_id=active_id_str,
                            entity_type=(
                                context_type
                                or typed_type
                            ),
                            source="PAGE_CONTEXT",
                            confidence=0.97,
                            clarification_required=False,
                        )

            # 2B. Fall back to conversation history.
            from_history = cls._resolve_from_history(
                conversation_history or [],
                expected_type=typed_type,
            )

            if from_history:
                return from_history

            # 2C. Typed reference exists, but entity is unavailable.
            return EntityResolution(
                source="UNRESOLVED_REFERENT",
                confidence=0.25,
                clarification_required=True,
            )

        # --------------------------------------------------------------
        # 3. Generic referent: it / this / that.
        # --------------------------------------------------------------
        if cls.has_generic_referent(clean_query):
            # Generic references intentionally prefer conversation history
            # because "it" has no semantic type on its own.
            from_history = cls._resolve_from_history(
                conversation_history or [],
                expected_type=None,
            )

            if from_history:
                return from_history

            # If page context has an active entity, use it conservatively.
            if page_context is not None:
                active_id = getattr(
                    page_context,
                    "active_entity_id",
                    None,
                )

                if active_id:
                    active_id_str = str(active_id).upper()

                    return EntityResolution(
                        entity_id=active_id_str,
                        entity_type=(
                            getattr(
                                page_context,
                                "active_entity_type",
                                None,
                            )
                            or cls.infer_entity_type(active_id_str)
                        ),
                        source="PAGE_CONTEXT",
                        confidence=0.88,
                        clarification_required=False,
                    )

            return EntityResolution(
                source="UNRESOLVED_REFERENT",
                confidence=0.25,
                clarification_required=True,
            )

        # --------------------------------------------------------------
        # 4. No entity reference at all.
        # --------------------------------------------------------------
        return EntityResolution()
