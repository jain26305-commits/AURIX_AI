"""Schema discovery, statistical type inference, and entity detection engine for Phase 11 & Phase 19."""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from aurix_core.data_fabric.schema_drift import SchemaDriftDetector
from aurix_core.onboarding.contracts import (
    FieldMapping,
    MappingConfidence,
    SchemaDiscoveryReport,
)

DATE_PATTERNS = [
    re.compile(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$"),
    re.compile(r"^\d{1,2}[-/]\d{1,2}[-/]\d{4}$"),
    re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}"),
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
            has_decimal = any("." in str(v) for v in sample)
            return "float" if has_decimal else "integer"

        bool_hits = sum(1 for v in sample if str(v).strip().lower() in ("true", "false", "1", "0", "y", "n"))
        if bool_hits / sample_size >= 0.90:
            return "boolean"

        unique_ratio = len(set(str(v) for v in sample)) / sample_size
        if unique_ratio > 0.85 and any(char.isdigit() for v in sample for char in str(v)):
            return "identifier"

        return "string"


class EntityCandidateDetector:
    """
    Deterministic entity classifier for enterprise onboarding datasets.

    Uses weighted discriminative signatures instead of simple substring
    counting. Generic fields contribute little; entity-specific identifiers
    contribute substantially more. Ambiguous top candidates are rejected
    instead of guessed.
    """

    ENTITY_SIGNATURES: Dict[str, Dict[str, int]] = {
        "demand_history": {
            "sku": 2,
            "sku_id": 3,
            "product": 2,
            "product_code": 3,
            "date": 2,
            "date_val": 2,
            "order_date": 2,
            "quantity": 3,
            "demand": 4,
            "sales": 3,
            "sales_qty": 3,
            "units": 2,
            "volume": 3,
        },
        "inventory_levels": {
            "sku": 2,
            "inventory": 4,
            "stock": 4,
            "on_hand": 5,
            "warehouse": 3,
            "facility": 3,
            "location": 2,
        },
        "purchase_orders": {
            "po_number": 6,
            "purchase_order_id": 6,
            "order_id": 4,
            "supplier_id": 4,
            "supplier": 3,
            "vendor": 3,
            "required_date": 4,
            "delivery": 2,
            "lead_time": 2,
            "status": 1,
        },
        "supplier_profiles": {
            "supplier_id": 5,
            "supplier_name": 6,
            "supplier": 3,
            "vendor": 3,
            "otd": 4,
            "defect_rate": 5,
            "tier": 2,
            "capacity": 2,
            "score": 2,
        },
        "shipments": {
            "shipment_id": 6,
            "shipment_number": 6,
            "tracking_number": 6,
            "tracking": 4,
            "carrier": 4,
            "origin": 3,
            "destination": 3,
            "eta": 4,
            "status": 1,
        },
        "network_nodes": {
            "node_id": 6,
            "facility_id": 5,
            "facility": 3,
            "plant": 4,
            "dc": 4,
            "warehouse": 4,
            "capacity": 2,
            "location": 2,
        },
        "item_costs": {
            "sku": 2,
            "sku_id": 3,
            "cost": 4,
            "unit_cost": 6,
            "holding_cost": 5,
            "currency": 2,
            "price": 3,
        },
        "invoices": {
            "invoice_id": 6,
            "invoice_number": 6,
            "invoice_type": 4,
            "entity_id": 3,
            "total_amount": 4,
            "tax_amount": 5,
            "issue_date": 4,
            "due_date": 4,
        },
        "boms": {
            "bom_id": 6,
            "parent_sku": 6,
            "component_sku": 6,
            "quantity_required": 5,
            "scrap_factor": 5,
        },
        "customers": {
            "customer_id": 7,
            "customer_name": 7,
            "account_status": 5,
            "segment": 3,
            "customer_tier": 4,
            "credit_limit": 3,
        },
        "orders": {
            "order_id": 7,
            "order_number": 7,
            "customer_id": 4,
            "order_status": 5,
            "channel": 4,
            "total_amount": 3,
            "discount_amount": 2,
            "currency": 2,
            "order_date": 5,
        },
        "order_lines": {
            "order_id": 6,
            "order_number": 5,
            "sku_id": 4,
            "quantity": 4,
            "unit_price": 4,
            "line_total": 5,
        },
        "purchase_order_lines": {
            "purchase_order_id": 7,
            "po_id": 6,
            "sku_id": 3,
            "quantity": 4,
            "unit_price": 4,
            "received_quantity": 5,
        },
        "payments": {
            "payment_id": 7,
            "payment_number": 6,
            "invoice_id": 5,
            "amount": 4,
            "payment_date": 5,
            "payment_type": 3,
        },
        "work_orders": {
            "work_order_id": 7,
            "work_order_number": 7,
            "sku_id": 2,
            "plant_location_id": 6,
            "plant": 4,
            "target_quantity": 5,
            "completed_quantity": 5,
            "scrap_quantity": 5,
            "status": 1,
        },
        "production_events": {
            "production_event_id": 7,
            "work_order_id": 6,
            "event_type": 4,
            "quantity": 3,
            "good_quantity": 5,
            "scrap_quantity": 5,
            "event_timestamp": 5,
        },
        "contracts": {
            "contract_id": 7,
            "contract_number": 7,
            "counterparty_id": 5,
            "contract_type": 4,
            "start_date": 4,
            "end_date": 4,
        },
        "returns": {
            "return_id": 7,
            "rma": 5,
            "rma_number": 7,
            "order_id": 3,
            "sku_id": 2,
            "quantity": 3,
            "disposition": 4,
        },
    }

    GENERIC_FIELDS = {
        "status",
        "date",
        "quantity",
        "amount",
        "currency",
        "price",
        "cost",
        "supplier",
        "vendor",
        "sku",
        "id",
    }

    @staticmethod
    def _normalize(value: str) -> str:
        return (
            str(value)
            .strip()
            .lower()
            .replace("_", "")
            .replace("-", "")
            .replace(" ", "")
        )

    @classmethod
    def _matches(cls, normalized_column: str, token: str) -> bool:
        normalized_token = cls._normalize(token)

        if normalized_column == normalized_token:
            return True

        # Avoid allowing extremely generic tokens to match arbitrary names.
        if normalized_token in {
            "status",
            "date",
            "id",
            "amount",
            "quantity",
            "cost",
            "price",
        }:
            return normalized_token == normalized_column

        return normalized_token in normalized_column

    @classmethod
    def score_entity(
        cls,
        entity: str,
        columns: List[str],
    ) -> Tuple[int, Set[str]]:
        normalized_columns = [cls._normalize(c) for c in columns]
        signature = cls.ENTITY_SIGNATURES[entity]

        score = 0
        matched: Set[str] = set()

        for token, weight in signature.items():
            if any(cls._matches(column, token) for column in normalized_columns):
                score += weight
                matched.add(token)

        return score, matched

    @classmethod
    def detect_entity(
        cls,
        columns: List[str],
    ) -> Tuple[Optional[str], MappingConfidence]:
        if not columns:
            return None, MappingConfidence.UNRESOLVED

        normalized_columns = {
            cls._normalize(column)
            for column in columns
        }

        scored: List[Tuple[str, int, Set[str]]] = []

        for entity in cls.ENTITY_SIGNATURES:
            score, matched = cls.score_entity(entity, columns)
            scored.append((entity, score, matched))

        scored.sort(key=lambda x: x[1], reverse=True)

        # Explicit precedence for demand-shaped schemas.
        #
        # A demand-history dataset may contain a generic date-like field
        # named Order_Date because legacy ERP exports use order date as the
        # observation date. Do not classify that as an orders dataset unless
        # an actual order identifier is present.
        demand_score, demand_matches = cls.score_entity(
            "demand_history",
            columns,
        )

        demand_signal = (
            bool(
                {
                    "sku",
                    "skuid",
                    "product",
                    "productcode",
                }
                & normalized_columns
            )
            and bool(
                {
                    "date",
                    "dateval",
                    "orderdate",
                    "postingdate",
                    "transactiondate",
                    "period",
                }
                & normalized_columns
            )
            and bool(
                {
                    "quantity",
                    "sales",
                    "salesqty",
                    "units",
                    "demand",
                    "volume",
                }
                & normalized_columns
            )
        )

        order_identifier_signal = bool(
            {
                "orderid",
                "ordernumber",
            }
            & normalized_columns
        )

        if demand_signal and not order_identifier_signal:
            if demand_score >= 5:
                if demand_score >= 9:
                    return (
                        "demand_history",
                        MappingConfidence.MEDIUM_CONFIDENCE,
                    )

                return (
                    "demand_history",
                    MappingConfidence.LOW_CONFIDENCE,
                )

        best_entity, best_score, best_matches = scored[0]

        if best_score <= 0:
            return None, MappingConfidence.UNRESOLVED

        second_score = scored[1][1] if len(scored) > 1 else 0

        strong_matches = sum(
            1
            for field in best_matches
            if field not in cls.GENERIC_FIELDS
        )

        if strong_matches == 0:
            return None, MappingConfidence.UNRESOLVED

        # When a demand-shaped dataset narrowly loses to order_lines because
        # of the generic quantity+sku overlap, prefer demand history.
        if (
            demand_signal
            and best_entity in {"order_lines", "orders"}
            and not order_identifier_signal
        ):
            return (
                "demand_history",
                (
                    MappingConfidence.MEDIUM_CONFIDENCE
                    if demand_score >= 7
                    else MappingConfidence.LOW_CONFIDENCE
                ),
            )

        # Very close candidates are unsafe to auto-classify.
        if second_score > 0 and best_score - second_score <= 2:
            return None, MappingConfidence.UNRESOLVED

        if best_score >= 14:
            confidence = MappingConfidence.HIGH_CONFIDENCE
        elif best_score >= 9:
            confidence = MappingConfidence.MEDIUM_CONFIDENCE
        elif best_score >= 5:
            confidence = MappingConfidence.LOW_CONFIDENCE
        else:
            confidence = MappingConfidence.UNRESOLVED

        return best_entity, confidence


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
            non_null_samples = [
                value
                for value in values
                if value is not None
            ][:5]

            field_mappings[col] = FieldMapping(
                source_column=col,
                inferred_type=inferred_type,
                sample_values=non_null_samples,
                confidence=MappingConfidence.UNRESOLVED,
            )

        detected_entity, entity_conf = (
            EntityCandidateDetector.detect_entity(cols)
        )

        return SchemaDiscoveryReport(
            source_columns=cols,
            detected_entity_name=detected_entity,
            entity_confidence=entity_conf,
            field_mappings=field_mappings,
            ambiguous_columns=[],
            unmapped_columns=list(cols),
            total_columns_detected=len(cols),
            sample_record_count=len(records),
            total_records=len(records),
        )
