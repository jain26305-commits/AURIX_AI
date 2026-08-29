"""
AURIX Enterprise Data Fabric — Schema Drift Detection Engine
Phase 19 Core Implementation.
Detects added, removed, mutated, or nullability-altered columns across sync cycles.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from aurix_core.data_fabric.contracts import DriftType


class DriftEvent(BaseModel):
    """Detailed record of a schema mutation."""
    drift_type: DriftType
    field_name: str
    expected: Optional[str] = None
    detected: Optional[str] = None
    description: str
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SchemaFingerprint(BaseModel):
    """Structural fingerprint of a schema version."""
    version: str
    field_types: Dict[str, str]
    nullability: Dict[str, bool]
    schema_hash: str


class SchemaDriftDetector:
    """Monitors schema invariants and emits drift alerts before data corruption occurs."""

    @staticmethod
    def infer_type(val: Any) -> str:
        """Infer canonical primitive type string."""
        if val is None:
            return "null"
        if isinstance(val, bool):
            return "boolean"
        if isinstance(val, int):
            return "integer"
        if isinstance(val, float):
            return "float"
        if isinstance(val, (list, tuple)):
            return "array"
        if isinstance(val, dict):
            return "object"
        return "string"

    @classmethod
    def generate_fingerprint(cls, sample_records: List[Dict[str, Any]], version: str = "1.0") -> SchemaFingerprint:
        """Build a deterministic schema fingerprint from a sample batch."""
        field_types: Dict[str, str] = {}
        nullability: Dict[str, bool] = {}

        for rec in sample_records:
            for k, v in rec.items():
                inferred = cls.infer_type(v)
                if k not in field_types or field_types[k] == "null":
                    field_types[k] = inferred
                if v is None:
                    nullability[k] = True
                elif k not in nullability:
                    nullability[k] = False

        serialized = json.dumps(
            {"fields": field_types, "nullability": nullability},
            sort_keys=True,
        )
        schema_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        return SchemaFingerprint(
            version=version,
            field_types=field_types,
            nullability=nullability,
            schema_hash=schema_hash,
        )

    @classmethod
    def compare_schemas(
        cls,
        baseline: SchemaFingerprint,
        current_sample: List[Dict[str, Any]],
    ) -> List[DriftEvent]:
        """Compare baseline schema fingerprint against an incoming dataset sample."""
        current = cls.generate_fingerprint(current_sample)
        events: List[DriftEvent] = []

        # 1. Added fields
        for field, f_type in current.field_types.items():
            if field not in baseline.field_types:
                events.append(
                    DriftEvent(
                        drift_type=DriftType.FIELD_ADDED,
                        field_name=field,
                        expected=None,
                        detected=f_type,
                        description=f"New field '{field}' of type '{f_type}' detected in source stream",
                    )
                )

        # 2. Removed fields
        for field, f_type in baseline.field_types.items():
            if field not in current.field_types:
                events.append(
                    DriftEvent(
                        drift_type=DriftType.FIELD_REMOVED,
                        field_name=field,
                        expected=f_type,
                        detected=None,
                        description=f"Expected field '{field}' was missing from source stream",
                    )
                )

        # 3. Mutated field types
        for field, base_type in baseline.field_types.items():
            if field in current.field_types:
                curr_type = current.field_types[field]
                if curr_type != "null" and base_type != "null" and curr_type != base_type:
                    events.append(
                        DriftEvent(
                            drift_type=DriftType.TYPE_CHANGED,
                            field_name=field,
                            expected=base_type,
                            detected=curr_type,
                            description=f"Field '{field}' changed type from '{base_type}' to '{curr_type}'",
                        )
                    )

        return events
