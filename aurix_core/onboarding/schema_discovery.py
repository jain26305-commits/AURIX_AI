"""Schema discovery, statistical type inference, and entity detection engine for Phase 11."""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from aurix_core.onboarding.contracts import (
    FieldMapping,
    MappingConfidence,
    SchemaDiscoveryReport,
)

# Common regex patterns for type detection
DATE_PATTERNS = [
    re.compile(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$"),          # 2026-08-14, 2026/08/14
    re.compile(r"^\d{1,2}[-/]\d{1,2}[-/]\d{4}$"),          # 14-08-2026, 08/14/2026
    re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}"),  # ISO Timestamp
]
CURRENCY_REGEX = re.compile(r"^[\$\€\£\¥\₹\s]*[\d,]+(\.\d+)?[\s]*[A-Z]{0,3}$")
NUMERIC_CLEAN_REGEX = re.compile(r"[\$,\s\€\£\¥\₹]")


class TypeInferenceEngine:
    """Infers statistical and semantic data types from raw value arrays."""

    @staticmethod
    def is_date(val_str: str) -> bool:
        """Checks if a string conforms to recognizable date/datetime patterns."""
        cleaned = val_str.strip()
        for pat in DATE_PATTERNS:
            if pat.match(cleaned):
                return True
        # Secondary fallback using standard date parse
        try:
            if len(cleaned) >= 8 and any(sep in cleaned for sep in ("-", "/", ".")):
                datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
                return True
        except Exception:
            pass
        return False

    @staticmethod
    def is_numeric(val_str: str) -> bool:
        """Checks if a string represents an integer or float after cleaning."""
        cleaned = NUMERIC_CLEAN_REGEX.sub("", val_str.strip())
        try:
            float(cleaned)
            return True
        except ValueError:
            return False

    @classmethod
    def infer_column_type(cls, values: List[Any]) -> str:
        """Infers primary column type based on non-null value distribution."""
        valid_vals = [v for v in values if v is not None and str(v).strip() != ""]
        if not valid_vals:
            return "empty"

        sample_size = min(len(valid_vals), 100)
        sample = valid_vals[:sample_size]

        date_hits = sum(1 for v in sample if cls.is_date(str(v)))
        if date_hits / sample_size >= 0.75:
            return "date"

        numeric_hits = sum(1 for v in sample if cls.is_numeric(str(v)))
        if numeric_hits / sample_size >= 0.85:
            # Distinguish float vs integer
            has_decimal = any("." in str(v) for v in sample)
            return "float" if has_decimal else "integer"

        # Check if values look like boolean flags
        bool_hits = sum(1 for v in sample if str(v).strip().lower() in ("true", "false", "1", "0", "y", "n"))
        if bool_hits / sample_size >= 0.90:
            return "boolean"

        # Check uniqueness for identifier detection
        unique_ratio = len(set(str(v) for v in sample)) / sample_size
        if unique_ratio > 0.85 and any(char.isdigit() for v in sample for char in str(v)):
            return "identifier"

        return "string"


class EntityCandidateDetector:
    """Evaluates column signatures against canonical supply chain domain entities."""

    ENTITY_SIGNATURES: Dict[str, Set[str]] = {
        "demand_history": {"sku", "date", "quantity", "sales", "demand", "order", "units"},
        "inventory_levels": {"sku", "inventory", "stock", "on_hand", "warehouse", "facility", "location"},
        "purchase_orders": {"order_id", "po", "supplier", "vendor", "lead_time", "status", "delivery"},
        "supplier_profiles": {"supplier", "vendor", "otd", "defect_rate", "tier", "score", "capacity"},
        "shipments": {"shipment", "tracking", "carrier", "origin", "destination", "eta", "status"},
        "network_nodes": {"node", "facility", "plant", "dc", "warehouse", "capacity", "location"},
        "item_costs": {"sku", "cost", "unit_cost", "holding_cost", "currency", "price"},
    }

    @classmethod
    def detect_entity(cls, columns: List[str]) -> Tuple[Optional[str], MappingConfidence]:
        """Scores column names against entity signatures to find the best domain match."""
        cleaned_cols = [c.lower().replace("_", "").replace(" ", "").replace("-", "") for c in columns]

        best_entity: Optional[str] = None
        highest_score = 0

        for entity, keywords in cls.ENTITY_SIGNATURES.items():
            matches = 0
            for kw in keywords:
                kw_clean = kw.replace("_", "")
                if any(kw_clean in col for col in cleaned_cols):
                    matches += 1

            if matches > highest_score:
                highest_score = matches
                best_entity = entity

        if highest_score >= 3:
            return best_entity, MappingConfidence.HIGH_CONFIDENCE
        elif highest_score >= 2:
            return best_entity, MappingConfidence.MEDIUM_CONFIDENCE
        elif highest_score == 1:
            return best_entity, MappingConfidence.LOW_CONFIDENCE

        return None, MappingConfidence.UNRESOLVED


class SchemaDiscoveryEngine:
    """Coordinates column profiling, type inference, and schema discovery."""

    @classmethod
    def discover_schema(
        cls,
        records: List[Dict[str, Any]],
        source_columns: Optional[List[str]] = None,
    ) -> SchemaDiscoveryReport:
        """Analyzes records to produce a complete SchemaDiscoveryReport."""
        if not records:
            return SchemaDiscoveryReport(
                source_columns=source_columns or [],
                detected_entity_name=None,
                entity_confidence=MappingConfidence.UNRESOLVED,
            )

        cols = source_columns if source_columns else list(records[0].keys())
        field_mappings: Dict[str, FieldMapping] = {}

        for col in cols:
            values = [row.get(col) for row in records]
            inferred_type = TypeInferenceEngine.infer_column_type(values)
            non_null_samples = [v for v in values if v is not None][:5]

            field_mappings[col] = FieldMapping(
                source_column=col,
                inferred_type=inferred_type,
                sample_values=non_null_samples,
                confidence=MappingConfidence.UNRESOLVED,
            )

        detected_entity, entity_conf = EntityCandidateDetector.detect_entity(cols)

        return SchemaDiscoveryReport(
            source_columns=cols,
            detected_entity_name=detected_entity,
            entity_confidence=entity_conf,
            field_mappings=field_mappings,
            ambiguous_columns=[],
            unmapped_columns=list(cols),
            total_columns_detected=len(cols),
            sample_record_count=len(records),
        )
