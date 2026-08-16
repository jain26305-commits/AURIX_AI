"""Data readiness, freshness, provenance, and source health evaluation engine for Phase 9."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class FreshnessState(str, Enum):
    """Explicit freshness states for canonical domain data."""
    LIVE = "LIVE"                  # < 24 hours old
    RECENT = "RECENT"              # 1 to 7 days old
    STALE = "STALE"                # 7 to 30 days old
    VERY_STALE = "VERY_STALE"      # > 30 days old
    UNKNOWN = "UNKNOWN"            # No source timestamp available


class SourceHealth(str, Enum):
    """Source health and synchronization status from upstream connectors."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    DELAYED = "DELAYED"
    FAILED = "FAILED"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    SCHEMA_ERROR = "SCHEMA_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    UNKNOWN = "UNKNOWN"


class ReadinessAssessment(BaseModel):
    """Assessment of readiness across four decoupled dimensions for an entity or domain."""
    entity_name: str
    available: bool = False
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    completeness_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    record_completeness_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    null_density_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    freshness: FreshnessState = FreshnessState.UNKNOWN
    freshness_age_hours: Optional[float] = None
    source_health: SourceHealth = SourceHealth.UNKNOWN
    missing_fields: List[str] = Field(default_factory=list)
    partially_populated_fields: List[str] = Field(default_factory=list)
    quality_issues: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)


class DataReadinessEngine:
    """Evaluates availability, quality, completeness, and freshness across canonical datasets."""

    # Default Freshness Thresholds (in hours)
    LIVE_THRESHOLD_HOURS: float = 24.0
    RECENT_THRESHOLD_HOURS: float = 168.0      # 7 days
    STALE_THRESHOLD_HOURS: float = 720.0       # 30 days

    @classmethod
    def evaluate_freshness(
        cls,
        source_timestamp: Optional[Any],
        reference_time: Optional[datetime] = None,
    ) -> Tuple[FreshnessState, Optional[float]]:
        """
        Computes the freshness state and age in hours from a source timestamp.
        Zero-fabrication: returns UNKNOWN and None if no timestamp exists.
        """
        if source_timestamp is None:
            return FreshnessState.UNKNOWN, None

        ref_time = reference_time or datetime.now(timezone.utc)
        parsed_time: Optional[datetime] = None

        if isinstance(source_timestamp, datetime):
            parsed_time = source_timestamp
        elif isinstance(source_timestamp, str):
            try:
                clean_ts = source_timestamp.replace("Z", "+00:00")
                parsed_time = datetime.fromisoformat(clean_ts)
            except (ValueError, TypeError):
                return FreshnessState.UNKNOWN, None

        if parsed_time is None:
            return FreshnessState.UNKNOWN, None

        if parsed_time.tzinfo is None:
            parsed_time = parsed_time.replace(tzinfo=timezone.utc)
        if ref_time.tzinfo is None:
            ref_time = ref_time.replace(tzinfo=timezone.utc)

        age_seconds = (ref_time - parsed_time).total_seconds()
        age_hours = 0.0 if age_seconds < 0 else age_seconds / 3600.0

        if age_hours <= cls.LIVE_THRESHOLD_HOURS:
            return FreshnessState.LIVE, round(age_hours, 2)
        elif age_hours <= cls.RECENT_THRESHOLD_HOURS:
            return FreshnessState.RECENT, round(age_hours, 2)
        elif age_hours <= cls.STALE_THRESHOLD_HOURS:
            return FreshnessState.STALE, round(age_hours, 2)
        else:
            return FreshnessState.VERY_STALE, round(age_hours, 2)

    @classmethod
    def evaluate_entity_readiness(
        cls,
        entity_name: str,
        records: List[Dict[str, Any]],
        required_fields: List[str],
        optional_fields: Optional[List[str]] = None,
        source_meta: Optional[Dict[str, Any]] = None,
        reference_time: Optional[datetime] = None,
    ) -> ReadinessAssessment:
        """
        Evaluates a collection of entity records for availability, completeness, quality, and freshness.
        Computes record-level null density across all rows.
        """
        opt_fields = optional_fields or []
        meta = source_meta or {}
        total_records = len(records)

        if total_records == 0:
            return ReadinessAssessment(
                entity_name=entity_name,
                available=False,
                quality_score=0.0,
                completeness_pct=0.0,
                record_completeness_pct=0.0,
                null_density_pct=100.0,
                freshness=FreshnessState.UNKNOWN,
                freshness_age_hours=None,
                source_health=SourceHealth(meta.get("source_health", SourceHealth.UNKNOWN.value)),
                missing_fields=list(required_fields),
                partially_populated_fields=[],
                quality_issues=["NO_RECORDS_FOUND"],
                provenance=meta.get("provenance", {}),
            )

        # 1. Dataset-Wide Record Completeness and Null Density
        missing_fields: List[str] = []
        partially_populated: List[str] = []
        total_required_cells = total_records * len(required_fields)
        populated_required_cells = 0

        for req in required_fields:
            populated_count = sum(
                1 for r in records if req in r and r[req] is not None and str(r[req]).strip() != ""
            )
            populated_required_cells += populated_count

            if populated_count == 0:
                missing_fields.append(req)
            elif populated_count < total_records:
                partially_populated.append(req)

        # Overall field presence (Schema + Optional Completeness)
        total_fields_to_check = len(required_fields) + len(opt_fields)
        schema_present_count = sum(
            1 for f in (required_fields + opt_fields) if any(f in r for r in records)
        )
        completeness_pct = (
            round((schema_present_count / total_fields_to_check) * 100.0, 2)
            if total_fields_to_check > 0
            else 100.0
        )

        record_completeness_pct = (
            round((populated_required_cells / total_required_cells) * 100.0, 2)
            if total_required_cells > 0
            else 0.0
        )
        null_density_pct = round(100.0 - record_completeness_pct, 2)

        # Available only if all required fields are present and populated >= 95% of records
        is_available = len(missing_fields) == 0 and record_completeness_pct >= 95.0

        # 2. Record-Level Quality Checks
        quality_issues: List[str] = []
        invalid_record_count = 0

        for rec in records:
            has_error = False
            for k, v in rec.items():
                if isinstance(v, (int, float)) and v < 0 and "change" not in k and "delta" not in k:
                    has_error = True
                    issue = f"NEGATIVE_VALUE_IN_{k.upper()}"
                    if issue not in quality_issues:
                        quality_issues.append(issue)
            if has_error:
                invalid_record_count += 1

        quality_score = (
            round(max(0.0, (total_records - invalid_record_count) / total_records), 2)
            if total_records > 0
            else 0.0
        )

        # 3. Freshness Evaluation
        source_ts = (
            meta.get("source_timestamp")
            or (records[0].get("timestamp") if records else None)
            or (records[0].get("date") if records else None)
        )
        freshness, age_hours = cls.evaluate_freshness(source_ts, reference_time)

        # 4. Source Health
        health_str = str(meta.get("source_health", SourceHealth.UNKNOWN.value)).upper()
        try:
            source_health = SourceHealth(health_str)
        except ValueError:
            source_health = SourceHealth.UNKNOWN

        return ReadinessAssessment(
            entity_name=entity_name,
            available=is_available,
            quality_score=quality_score,
            completeness_pct=completeness_pct,
            record_completeness_pct=record_completeness_pct,
            null_density_pct=null_density_pct,
            freshness=freshness,
            freshness_age_hours=age_hours,
            source_health=source_health,
            missing_fields=missing_fields,
            partially_populated_fields=partially_populated,
            quality_issues=quality_issues,
            provenance={
                "source_system": meta.get("source_system", "UNKNOWN"),
                "ingestion_run_id": meta.get("ingestion_run_id"),
                "record_count": total_records,
                "null_density_pct": null_density_pct,
                "evaluated_at": (reference_time or datetime.now(timezone.utc)).isoformat(),
            },
        )