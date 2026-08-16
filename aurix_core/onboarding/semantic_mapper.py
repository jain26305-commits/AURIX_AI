"""Semantic field mapping, alias dictionary matching, and ambiguity resolution engine for Phase 11."""

import difflib
import re
from typing import Dict, List, Optional, Set, Tuple

from aurix_core.onboarding.contracts import (
    FieldMapping,
    MappingConfidence,
    SchemaDiscoveryReport,
)

# Canonical alias dictionary mapping canonical field names to common industry aliases
CANONICAL_ALIASES: Dict[str, Set[str]] = {
    "sku_id": {
        "sku", "skuid", "skucode", "item", "itemid", "itemcode", "product",
        "productid", "productcode", "material", "materialnumber", "materialno",
        "partnumber", "partno", "articleid", "articleno", "code",
    },
    "date": {
        "date", "transactiondate", "orderdate", "period", "month", "week",
        "day", "timestamp", "ds", "postingdate", "invoicedate", "salesdate",
    },
    "quantity": {
        "quantity", "qty", "demand", "sales", "salesqty", "units", "volume",
        "qtysold", "actualdemand", "orderedqty", "demandqty", "amount",
    },
    "inventory_level": {
        "inventory", "inventorylevel", "stock", "stocklevel", "onhand",
        "onhandqty", "availableqty", "closingstock", "currentstock", "balance",
    },
    "reorder_point": {
        "reorderpoint", "rop", "reorderlevel", "minlevel", "threshold",
    },
    "safety_stock": {
        "safetystock", "bufferstock", "ss", "minstock", "safetylevel",
    },
    "supplier_id": {
        "supplier", "supplierid", "suppliercode", "vendor", "vendorid",
        "vendorcode", "sourcevendor", "sourcesupplier", "suppliername",
    },
    "lead_time_days": {
        "leadtime", "leadtimedays", "lt", "ltdays", "deliverydays",
        "procurementleadtime", "supplierleadtime",
    },
    "unit_cost": {
        "unitcost", "cost", "costprice", "itemcost", "purchaseprice",
        "price", "standardcost", "unitprice",
    },
    "holding_cost_annual": {
        "holdingcost", "holdingcostannual", "carryingcost", "storagecost",
        "annualholdingcost", "costofcarry",
    },
    "shipment_id": {
        "shipment", "shipmentid", "trackingnumber", "trackingid", "waybill",
        "consignmentid", "bol", "deliverynumber",
    },
    "origin_facility": {
        "originfacility", "origin", "fromlocation", "sourcewarehouse",
        "sourcefacility", "originlocation", "departurefacility",
    },
    "destination_facility": {
        "destinationfacility", "destination", "tolocation", "destwarehouse",
        "destfacility", "destinationlocation", "arrivalfacility",
    },
}

# Type constraints required for valid canonical mapping
CANONICAL_TYPE_REQUIREMENTS: Dict[str, Set[str]] = {
    "sku_id": {"string", "identifier", "integer"},
    "date": {"date", "string"},
    "quantity": {"float", "integer", "numeric"},
    "inventory_level": {"float", "integer", "numeric"},
    "reorder_point": {"float", "integer", "numeric"},
    "safety_stock": {"float", "integer", "numeric"},
    "supplier_id": {"string", "identifier", "integer"},
    "lead_time_days": {"float", "integer", "numeric"},
    "unit_cost": {"float", "integer", "numeric"},
    "holding_cost_annual": {"float", "integer", "numeric"},
    "shipment_id": {"string", "identifier", "integer"},
    "origin_facility": {"string", "identifier"},
    "destination_facility": {"string", "identifier"},
}


class SemanticMapper:
    """Performs deterministic semantic field mapping, type validation, and ambiguity detection."""

    @staticmethod
    def normalize_header(name: str) -> str:
        """Normalizes column names by stripping spaces, special characters, and casing."""
        cleaned = re.sub(r"[^a-zA-Z0-9]", "", str(name).strip().lower())
        return cleaned

    @classmethod
    def calculate_similarity(cls, col_normalized: str, alias: str) -> float:
        """Calculates string similarity score between a column header and an alias."""
        if col_normalized == alias:
            return 1.0
        if alias in col_normalized or col_normalized in alias:
            return 0.88
        return difflib.SequenceMatcher(None, col_normalized, alias).ratio()

    @classmethod
    def map_field(
        cls,
        source_col: str,
        inferred_type: str,
        sample_values: Optional[List[object]] = None,
    ) -> FieldMapping:
        """Maps an individual source column to the best canonical candidate with confidence scoring."""
        col_norm = cls.normalize_header(source_col)
        sample_vals = sample_values or []

        best_canonical: Optional[str] = None
        best_score: float = 0.0

        for canonical_field, aliases in CANONICAL_ALIASES.items():
            for alias in aliases:
                score = cls.calculate_similarity(col_norm, alias)
                if score > best_score:
                    best_score = score
                    best_canonical = canonical_field

        # Type validation check
        type_compatible = True
        if best_canonical and best_canonical in CANONICAL_TYPE_REQUIREMENTS:
            allowed_types = CANONICAL_TYPE_REQUIREMENTS[best_canonical]
            if inferred_type not in allowed_types and inferred_type != "empty":
                type_compatible = False
                best_score *= 0.5  # Penalize score heavily if type is incompatible

        # Determine confidence level
        confidence: MappingConfidence
        if best_score >= 0.88 and type_compatible:
            confidence = MappingConfidence.HIGH_CONFIDENCE
        elif best_score >= 0.65 and type_compatible:
            confidence = MappingConfidence.MEDIUM_CONFIDENCE
        elif best_score >= 0.40:
            confidence = MappingConfidence.LOW_CONFIDENCE
        else:
            confidence = MappingConfidence.UNRESOLVED
            best_canonical = None

        is_ambiguous = confidence in (MappingConfidence.LOW_CONFIDENCE, MappingConfidence.UNRESOLVED)
        ambiguity_reasons = []
        if not type_compatible:
            ambiguity_reasons.append(
                f"Inferred data type '{inferred_type}' is incompatible with canonical field '{best_canonical}'."
            )
        if confidence == MappingConfidence.LOW_CONFIDENCE:
            ambiguity_reasons.append(f"Low semantic confidence ({best_score:.2f}) for column '{source_col}'.")

        return FieldMapping(
            source_column=source_col,
            canonical_field=best_canonical if confidence != MappingConfidence.UNRESOLVED else None,
            confidence=confidence,
            confidence_score=round(best_score, 3),
            inferred_type=inferred_type,
            sample_values=sample_vals,
            is_ambiguous=is_ambiguous,
            ambiguity_reasons=ambiguity_reasons,
        )

    @classmethod
    def map_schema(
        cls,
        discovery_report: SchemaDiscoveryReport,
    ) -> Tuple[SchemaDiscoveryReport, Dict[str, str]]:
        """
        Maps all columns in a discovery report, detects collisions, and returns
        the updated report alongside accepted canonical mappings.
        """
        updated_mappings: Dict[str, FieldMapping] = {}
        canonical_to_source: Dict[str, List[str]] = {}
        ambiguous_cols: List[str] = []
        unmapped_cols: List[str] = []
        accepted_mappings: Dict[str, str] = {}

        # 1. Map individual columns
        for col, existing_meta in discovery_report.field_mappings.items():
            mapping = cls.map_field(
                source_col=col,
                inferred_type=existing_meta.inferred_type,
                sample_values=existing_meta.sample_values,
            )
            updated_mappings[col] = mapping

            if mapping.canonical_field:
                canonical_to_source.setdefault(mapping.canonical_field, []).append(col)
            else:
                unmapped_cols.append(col)

        # 2. Collision detection (multiple source columns mapping to the same canonical field)
        for canon_field, source_cols in canonical_to_source.items():
            if len(source_cols) > 1:
                for sc in source_cols:
                    fm = updated_mappings[sc]
                    fm.is_ambiguous = True
                    fm.confidence = MappingConfidence.LOW_CONFIDENCE
                    fm.ambiguity_reasons.append(
                        f"Collision: Multiple columns {source_cols} map to canonical field '{canon_field}'."
                    )
                    ambiguous_cols.append(sc)
            else:
                sc = source_cols[0]
                fm = updated_mappings[sc]
                if not fm.is_ambiguous and fm.confidence in (
                    MappingConfidence.HIGH_CONFIDENCE,
                    MappingConfidence.MEDIUM_CONFIDENCE,
                ):
                    accepted_mappings[sc] = canon_field
                elif fm.is_ambiguous:
                    ambiguous_cols.append(sc)

        discovery_report.field_mappings = updated_mappings
        discovery_report.ambiguous_columns = ambiguous_cols
        discovery_report.unmapped_columns = unmapped_cols

        return discovery_report, accepted_mappings

    @classmethod
    def apply_manual_overrides(
        cls,
        discovery_report: SchemaDiscoveryReport,
        manual_mappings: Dict[str, str],
    ) -> Tuple[SchemaDiscoveryReport, Dict[str, str]]:
        """Applies explicit user mappings to resolve ambiguous or unmapped columns."""
        accepted_mappings: Dict[str, str] = {}
        for source_col, canon_field in manual_mappings.items():
            if source_col in discovery_report.field_mappings:
                fm = discovery_report.field_mappings[source_col]
                fm.canonical_field = canon_field
                fm.confidence = MappingConfidence.HIGH_CONFIDENCE
                fm.confidence_score = 1.0
                fm.is_ambiguous = False
                fm.ambiguity_reasons = []
                accepted_mappings[source_col] = canon_field

        # Re-evaluate unmapped / ambiguous column lists
        discovery_report.ambiguous_columns = [
            col for col, fm in discovery_report.field_mappings.items() if fm.is_ambiguous
        ]
        discovery_report.unmapped_columns = [
            col for col, fm in discovery_report.field_mappings.items() if not fm.canonical_field
        ]

        return discovery_report, accepted_mappings