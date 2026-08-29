"""
AURIX Enterprise Business Context Graph — Semantic Foundation & Ontology
Phase 24 Core Implementation.
Standardizes controlled vocabularies and maps external source concepts (Tally/Odoo/SAP) to canonical AURIX entities.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from aurix_core.context.contracts import EntityType, RelationshipType


class SemanticOntologyEngine:
    """Semantic mapping repository translating ERP/WMS/accounting entities into canonical terms."""

    # External source concept aliases
    _SOURCE_TERM_MAPPINGS: Dict[str, Dict[str, EntityType]] = {
        "TALLY": {
            "ledger_sundry_debtor": EntityType.CUSTOMER,
            "ledger_sundry_creditor": EntityType.SUPPLIER,
            "stock_item": EntityType.SKU,
            "sales_voucher": EntityType.ORDER,
            "purchase_voucher": EntityType.PURCHASE_ORDER,
            "receipt_voucher": EntityType.PAYMENT,
        },
        "ODOO": {
            "res.partner.customer": EntityType.CUSTOMER,
            "res.partner.supplier": EntityType.SUPPLIER,
            "product.product": EntityType.SKU,
            "product.template": EntityType.PRODUCT,
            "sale.order": EntityType.ORDER,
            "purchase.order": EntityType.PURCHASE_ORDER,
            "account.move.out_invoice": EntityType.INVOICE,
            "mrp.production": EntityType.WORK_ORDER,
        },
        "SAP": {
            "KNA1": EntityType.CUSTOMER,
            "LFA1": EntityType.SUPPLIER,
            "MARA": EntityType.PRODUCT,
            "MARC": EntityType.SKU,
            "VBAK": EntityType.ORDER,
            "EKKO": EntityType.PURCHASE_ORDER,
            "BKPF": EntityType.INVOICE,
            "AFKO": EntityType.WORK_ORDER,
        },
    }

    @classmethod
    def resolve_entity_type(cls, source_system: str, source_concept: str) -> EntityType:
        """Map external source system table/document type to canonical EntityType."""
        sys_key = source_system.upper()
        concept_key = source_concept.strip()

        sys_mappings = cls._SOURCE_TERM_MAPPINGS.get(sys_key, {})
        if concept_key in sys_mappings:
            return sys_mappings[concept_key]

        # Case-insensitive direct string matching
        for enum_val in EntityType:
            if enum_val.value.lower() == concept_key.lower():
                return enum_val

        return EntityType.SKU  # Standard safe fallback

    @classmethod
    def get_controlled_relationships(cls) -> List[str]:
        """Return all approved canonical relationship types."""
        return [r.value for r in RelationshipType]
