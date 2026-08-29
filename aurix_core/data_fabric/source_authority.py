"""
AURIX Enterprise Data Fabric — Source Authority & Conflict Matrix
Phase 19 Core Implementation.
Resolves multi-source data conflicts using domain priority rules without silent overwriting.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from aurix_core.data_fabric.contracts import CanonicalEntityType


class ConflictRecord(BaseModel):
    """Detailed log of a multi-source data discrepancy."""
    tenant_id: str
    entity_type: CanonicalEntityType
    entity_id: str
    attribute_name: str
    source_a: str
    value_a: Any
    source_b: str
    value_b: Any
    winning_source: str
    resolved_value: Any
    resolution_rule: str


class SourceAuthorityMatrix:
    """Manages domain-specific system authority hierarchies."""

    DEFAULT_PRECEDENCE: Dict[str, List[str]] = {
        "inventory_position": ["WMS", "SAP", "ODOO", "TALLY", "MANUAL_CSV"],
        "price": ["SAP", "ODOO", "TALLY", "CRM", "MANUAL_CSV"],
        "order": ["SHOPIFY", "ODOO", "SAP", "TALLY", "MANUAL_CSV"],
        "purchase_order": ["SAP", "ODOO", "TALLY", "MANUAL_CSV"],
        "supplier": ["SAP", "ODOO", "TALLY", "MANUAL_CSV"],
        "customer": ["CRM", "SHOPIFY", "ODOO", "SAP", "TALLY"],
    }

    def __init__(self, custom_rules: Optional[Dict[str, List[str]]] = None) -> None:
        self._rules = custom_rules or self.DEFAULT_PRECEDENCE

    def get_source_rank(self, domain: str, source_system: str) -> int:
        """Lower number indicates higher authoritative precedence."""
        precedence = self._rules.get(domain.lower(), [])
        src = source_system.upper()
        if src in precedence:
            return precedence.index(src)
        return 999

    def resolve_attribute_conflict(
        self,
        tenant_id: str,
        entity_type: CanonicalEntityType,
        entity_id: str,
        attribute_name: str,
        source_a: str,
        value_a: Any,
        source_b: str,
        value_b: Any,
    ) -> Tuple[Any, ConflictRecord]:
        """Determine authoritative value between two conflicting sources."""
        rank_a = self.get_source_rank(entity_type.value, source_a)
        rank_b = self.get_source_rank(entity_type.value, source_b)

        if rank_a <= rank_b:
            winning_source = source_a
            winning_value = value_a
            rule = f"Domain authority rule: {source_a} (rank {rank_a}) > {source_b} (rank {rank_b})"
        else:
            winning_source = source_b
            winning_value = value_b
            rule = f"Domain authority rule: {source_b} (rank {rank_b}) > {source_a} (rank {rank_a})"

        conflict = ConflictRecord(
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            attribute_name=attribute_name,
            source_a=source_a,
            value_a=value_a,
            source_b=source_b,
            value_b=value_b,
            winning_source=winning_source,
            resolved_value=winning_value,
            resolution_rule=rule,
        )

        return winning_value, conflict
