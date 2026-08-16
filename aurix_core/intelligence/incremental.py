"""Incremental data merge, historical correction validation, and impact analysis engine for Phase 9, 11 & 12."""

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field


class RecordChangeType(str, Enum):
    """Categorization of individual records in an incremental update."""
    NEW = "NEW"                        # Novel historical or future period record
    DUPLICATE = "DUPLICATE"            # Exact identical record already present (idempotent)
    CORRECTION = "CORRECTION"          # Validated revision of an existing historical record
    OUT_OF_ORDER = "OUT_OF_ORDER"      # Valid record arriving later than subsequent periods
    CONFLICT = "CONFLICT"              # Malformed or contradictory update rejected by validation


class RecordDiff(BaseModel):
    """Detailed diff for a single modified or corrected record."""
    record_key: str
    change_type: RecordChangeType
    prior_values: Optional[Dict[str, Any]] = None
    new_values: Dict[str, Any]
    event_timestamp: Optional[str] = None
    version: int = 1
    reason: Optional[str] = None


class IncrementalUpdateReport(BaseModel):
    """Comprehensive report summarizing the incremental merge and capability impact analysis."""
    entity_name: str
    total_incoming_records: int
    new_records_count: int = 0
    duplicates_count: int = 0
    corrections_count: int = 0
    out_of_order_count: int = 0
    conflicts_count: int = 0
    diffs: List[RecordDiff] = Field(default_factory=list)
    affected_entities: List[str] = Field(default_factory=list)
    affected_capabilities: List[str] = Field(default_factory=list)
    unaffected_capabilities: List[str] = Field(default_factory=list)
    requires_recomputation: bool = False
    merged_record_count: int = 0
    provenance: Dict[str, Any] = Field(default_factory=dict)


class MergeResult(BaseModel):
    """Result container for incremental dataset merges and capability dirty-tagging."""
    is_duplicate: bool = False
    appended_count: int = 0
    corrections_count: int = 0
    total_records: int = 0
    merged_records: List[Dict[str, Any]] = Field(default_factory=list)
    affected_capabilities: List[str] = Field(default_factory=list)


class IncrementalMergeEngine:
    """Merges incremental canonical updates, tracks temporal versions, and evaluates recomputation graphs."""

    # Entity to Capability Dependency Mapping
    ENTITY_CAPABILITY_GRAPH: Dict[str, List[str]] = {
        "demand_history": [
            "DEMAND_CLASSIFICATION",
            "DEMAND_FORECASTING",
            "SAFETY_STOCK_ROP",
            "INVENTORY_POSITION_RISK",
            "INVENTORY_REBALANCING",
            "WORKING_CAPITAL_TCO",
            "SCENARIO_SIMULATION",
        ],
        "inventory_levels": [
            "SAFETY_STOCK_ROP",
            "INVENTORY_POSITION_RISK",
            "INVENTORY_REBALANCING",
            "WORKING_CAPITAL_TCO",
            "SCENARIO_SIMULATION",
        ],
        "purchase_orders": [
            "SUPPLIER_PERFORMANCE_RISK",
            "SUPPLIER_SELECTION",
        ],
        "supplier_catalog": [
            "SUPPLIER_SELECTION",
        ],
        "shipments": [
            "SHIPMENT_TRACKING_ETA",
        ],
        "network_nodes": [
            "NETWORK_TOPOLOGY_BOTTLENECK",
            "INVENTORY_REBALANCING",
        ],
        "rebalancing_candidates": [
            "INVENTORY_REBALANCING",
        ],
        "item_costs": [
            "WORKING_CAPITAL_TCO",
            "SCENARIO_SIMULATION",
        ],
        "scenario_parameters": [
            "SCENARIO_SIMULATION",
        ],
    }

    ALL_CAPABILITIES: List[str] = [
        "DEMAND_CLASSIFICATION",
        "DEMAND_FORECASTING",
        "SAFETY_STOCK_ROP",
        "INVENTORY_POSITION_RISK",
        "SUPPLIER_PERFORMANCE_RISK",
        "SUPPLIER_SELECTION",
        "SHIPMENT_TRACKING_ETA",
        "NETWORK_TOPOLOGY_BOTTLENECK",
        "INVENTORY_REBALANCING",
        "WORKING_CAPITAL_TCO",
        "SCENARIO_SIMULATION",
    ]

    @classmethod
    def _generate_record_key(cls, record: Dict[str, Any], key_fields: List[str]) -> str:
        """Generates a deterministic composite key for identifying canonical records."""
        parts = [str(record.get(f, "")).strip().upper() for f in key_fields]
        return "::".join(parts)

    @classmethod
    def diff_and_merge(
        cls,
        entity_name: str,
        existing_records: List[Dict[str, Any]],
        incoming_records: List[Dict[str, Any]],
        key_fields: List[str],
        timestamp_field: str = "date",
        value_fields: Optional[List[str]] = None,
        source_meta: Optional[Dict[str, Any]] = None,
        current_time: Optional[datetime] = None,
    ) -> Tuple[List[Dict[str, Any]], IncrementalUpdateReport]:
        """
        Idempotently merges incoming updates with existing canonical records.
        Handles new periods, historical revisions, duplicates, and out-of-order updates.
        """
        now = current_time or datetime.now(timezone.utc)
        meta = source_meta or {}

        # 1. Index Existing Records
        existing_map: Dict[str, Dict[str, Any]] = {}
        for rec in existing_records:
            k = cls._generate_record_key(rec, key_fields)
            existing_map[k] = dict(rec)

        merged_map: Dict[str, Dict[str, Any]] = dict(existing_map)
        diffs: List[RecordDiff] = []

        new_count = 0
        dup_count = 0
        corr_count = 0
        ooo_count = 0
        conf_count = 0

        # Find latest existing event timestamp to detect out-of-order records
        max_existing_ts: Optional[str] = None
        for rec in existing_records:
            ts = str(rec.get(timestamp_field, ""))
            if ts and (max_existing_ts is None or ts > max_existing_ts):
                max_existing_ts = ts

        # 2. Process Incoming Records
        for inc_rec in incoming_records:
            k = cls._generate_record_key(inc_rec, key_fields)
            inc_ts = str(inc_rec.get(timestamp_field, ""))

            # Validation check (Negative checks on numerical fields)
            is_valid = True
            for vf in (value_fields or []):
                val = inc_rec.get(vf)
                if isinstance(val, (int, float)) and val < 0 and "change" not in vf and "delta" not in vf:
                    is_valid = False
                    break

            if not is_valid:
                conf_count += 1
                diffs.append(
                    RecordDiff(
                        record_key=k,
                        change_type=RecordChangeType.CONFLICT,
                        new_values=inc_rec,
                        event_timestamp=inc_ts,
                        reason="INVALID_NEGATIVE_NUMERIC_FIELD",
                    )
                )
                continue

            if k not in merged_map:
                # Novel Record
                is_out_of_order = max_existing_ts is not None and inc_ts != "" and inc_ts < max_existing_ts
                change_type = RecordChangeType.OUT_OF_ORDER if is_out_of_order else RecordChangeType.NEW

                if is_out_of_order:
                    ooo_count += 1
                else:
                    new_count += 1

                augmented_rec = dict(inc_rec)
                augmented_rec["_version"] = 1
                augmented_rec["_updated_at"] = now.isoformat()
                merged_map[k] = augmented_rec

                diffs.append(
                    RecordDiff(
                        record_key=k,
                        change_type=change_type,
                        new_values=inc_rec,
                        event_timestamp=inc_ts,
                        version=1,
                    )
                )
            else:
                # Existing Key Check (Duplicate vs Correction)
                curr_rec = merged_map[k]
                fields_to_compare = value_fields or [
                    f for f in inc_rec.keys() if not str(f).startswith("_")
                ]

                has_changes = False
                for vf in fields_to_compare:
                    if curr_rec.get(vf) != inc_rec.get(vf):
                        has_changes = True
                        break

                if not has_changes:
                    # Identical Duplicate (Idempotent Hit)
                    dup_count += 1
                    diffs.append(
                        RecordDiff(
                            record_key=k,
                            change_type=RecordChangeType.DUPLICATE,
                            new_values=inc_rec,
                            event_timestamp=inc_ts,
                            version=int(curr_rec.get("_version", 1)),
                        )
                    )
                else:
                    # Validated Historical Correction
                    corr_count += 1
                    prior_version = int(curr_rec.get("_version", 1))
                    new_version = prior_version + 1

                    updated_rec = dict(curr_rec)
                    updated_rec.update(inc_rec)
                    updated_rec["_version"] = new_version
                    updated_rec["_updated_at"] = now.isoformat()
                    updated_rec["_prior_values"] = {
                        vf: curr_rec.get(vf) for vf in fields_to_compare
                    }
                    merged_map[k] = updated_rec

                    diffs.append(
                        RecordDiff(
                            record_key=k,
                            change_type=RecordChangeType.CORRECTION,
                            prior_values={vf: curr_rec.get(vf) for vf in fields_to_compare},
                            new_values=inc_rec,
                            event_timestamp=inc_ts,
                            version=new_version,
                            reason="HISTORICAL_VALUE_SUPERSEDED",
                        )
                    )

        # 3. Sort merged records deterministically by timestamp if available
        merged_records = list(merged_map.values())
        if timestamp_field:
            merged_records.sort(key=lambda x: str(x.get(timestamp_field, "")))

        # 4. Determine Affected Capabilities (Impact Analysis)
        requires_recompute = (new_count + corr_count + ooo_count) > 0
        affected_caps: Set[str] = set()
        if requires_recompute:
            affected_caps.update(cls.ENTITY_CAPABILITY_GRAPH.get(entity_name, []))

        unaffected_caps = [c for c in cls.ALL_CAPABILITIES if c not in affected_caps]

        report = IncrementalUpdateReport(
            entity_name=entity_name,
            total_incoming_records=len(incoming_records),
            new_records_count=new_count,
            duplicates_count=dup_count,
            corrections_count=corr_count,
            out_of_order_count=ooo_count,
            conflicts_count=conf_count,
            diffs=diffs,
            affected_entities=[entity_name] if requires_recompute else [],
            affected_capabilities=sorted(list(affected_caps)),
            unaffected_capabilities=unaffected_caps,
            requires_recomputation=requires_recompute,
            merged_record_count=len(merged_records),
            provenance={
                "source_system": meta.get("source_system", "INCREMENTAL_CONNECTOR"),
                "ingestion_run_id": meta.get("ingestion_run_id"),
                "merged_at": now.isoformat(),
            },
        )

        return merged_records, report

    @classmethod
    def merge_dataset(
        cls,
        existing_records: List[Dict[str, Any]],
        new_records: List[Dict[str, Any]],
        entity_name: str,
        key_field: str = "sku_id",
        timestamp_field: str = "date",
    ) -> MergeResult:
        """High-level interface returning MergeResult for onboarding and connector pipelines."""
        if not new_records:
            return MergeResult(
                is_duplicate=False,
                appended_count=0,
                corrections_count=0,
                total_records=len(existing_records),
                merged_records=existing_records,
                affected_capabilities=[],
            )

        # 1. Check for exact full-dataset identical duplicate
        existing_hash = hashlib.sha256(
            json.dumps(existing_records, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        new_hash = hashlib.sha256(
            json.dumps(new_records, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

        if existing_records and existing_hash == new_hash:
            return MergeResult(
                is_duplicate=True,
                appended_count=0,
                corrections_count=0,
                total_records=len(existing_records),
                merged_records=existing_records,
                affected_capabilities=[],
            )

        # 2. Derive composite key fields
        sample = new_records[0] if new_records else (existing_records[0] if existing_records else {})
        keys: List[str] = []
        if key_field in sample:
            keys.append(key_field)
        if timestamp_field in sample and timestamp_field != key_field:
            keys.append(timestamp_field)
        if not keys:
            keys = [str(k) for k in sample.keys() if not str(k).startswith("_")][:2] or ["id"]

        merged_records, report = cls.diff_and_merge(
            entity_name=entity_name,
            existing_records=existing_records,
            incoming_records=new_records,
            key_fields=keys,
            timestamp_field=timestamp_field,
        )

        is_dup = (
            len(existing_records) > 0
            and report.duplicates_count == len(new_records)
            and report.new_records_count == 0
            and report.corrections_count == 0
        )

        return MergeResult(
            is_duplicate=is_dup,
            appended_count=report.new_records_count + report.out_of_order_count,
            corrections_count=report.corrections_count,
            total_records=len(merged_records),
            merged_records=merged_records,
            affected_capabilities=report.affected_capabilities,
        )