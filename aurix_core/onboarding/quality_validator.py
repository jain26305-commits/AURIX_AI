"""Multi-dimensional data quality, completeness, and temporal coverage engine for Phase 11."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
import pandas as pd

from aurix_core.onboarding.contracts import (
    CompletenessSummary,
    DataQualitySummary,
    TemporalCoverage,
)

ENTITY_REQUIRED_FIELDS: Dict[str, Set[str]] = {
    "demand_history": {"sku_id", "date", "quantity"},
    "inventory_levels": {"sku_id", "location_id", "on_hand"},
    "purchase_orders": {"order_id", "supplier_id", "lead_time_days"},
    "supplier_profiles": {"supplier_id"},
    "shipments": {"shipment_id", "origin_facility", "destination_facility"},
    "network_nodes": {"node_id"},
    "item_costs": {"sku_id", "unit_cost"},
}

NON_NEGATIVE_NUMERIC_FIELDS = {
    "quantity",
    "on_hand",
    "on_order",
    "inventory_level",
    "reorder_point",
    "safety_stock",
    "lead_time_days",
    "unit_cost",
    "holding_cost_annual",
}


class QualityValidator:
    """Validates data hygiene, null densities, negative value constraints, and value validity."""

    @classmethod
    def validate_records(
        cls,
        records: List[Dict[str, Any]],
        canonical_fields: Set[str],
        allow_negative_fields: Optional[Set[str]] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], DataQualitySummary]:
        """Validates mapped records against canonical constraints."""
        if not records:
            return [], [], DataQualitySummary()

        accepted: List[Dict[str, Any]] = []
        rejected: List[Dict[str, Any]] = []
        error_breakdown: Dict[str, int] = {}
        allowed_negative_fields = allow_negative_fields or set()
        total_cells = len(records) * len(canonical_fields) if canonical_fields else 1
        null_cells = 0

        for row in records:
            row_errors: List[str] = []

            for field in canonical_fields:
                val = row.get(field)
                if val is None or str(val).strip() == "":
                    null_cells += 1
                    if field in ("sku_id", "date", "shipment_id", "order_id"):
                        row_errors.append(f"Missing required identifier: '{field}'")
                elif field in NON_NEGATIVE_NUMERIC_FIELDS:
                    try:
                        num_val = float(str(val).replace(",", "").replace("$", ""))
                        if num_val < 0 and field not in allowed_negative_fields:
                            row_errors.append(
                                f"Negative value ({num_val}) not permitted for '{field}'"
                            )
                    except ValueError:
                        row_errors.append(
                            f"Invalid numeric value '{val}' for '{field}'"
                        )

            if "date" in canonical_fields and row.get("date"):
                d_str = str(row["date"]).strip()
                try:
                    pd.to_datetime(d_str)
                except Exception:
                    row_errors.append(f"Invalid date format '{d_str}'")

            if row_errors:
                rejected.append(row)
                for err in row_errors:
                    err_key = err.split(":")[0]
                    error_breakdown[err_key] = error_breakdown.get(err_key, 0) + 1
            else:
                accepted.append(row)

        null_density_pct = round((null_cells / float(total_cells)) * 100.0, 2) if total_cells > 0 else 0.0
        quality_score = round(len(accepted) / float(len(records)), 4) if records else 1.0

        summary = DataQualitySummary(
            total_records=len(records),
            accepted_records=len(accepted),
            rejected_records=len(rejected),
            null_density_pct=null_density_pct,
            quality_score=quality_score,
            validation_errors_count=len(rejected),
            error_breakdown=error_breakdown,
        )

        return accepted, rejected, summary


class TemporalCoverageAnalyzer:
    """Analyzes historical timeline continuity, sequence integrity, frequencies, and gaps."""

    @classmethod
    def analyze(cls, records: List[Dict[str, Any]], date_field: str = "date") -> TemporalCoverage:
        """Evaluates temporal timeline properties from record collection."""
        date_records: List[Tuple[int, datetime]] = []

        for idx, row in enumerate(records):
            val = row.get(date_field) or row.get("date")
            if val is not None and str(val).strip():
                try:
                    dt = pd.to_datetime(str(val).strip()).to_pydatetime()
                    date_records.append((idx, dt))
                except Exception:
                    continue

        if not date_records:
            return TemporalCoverage(
                period_frequency="NONE",
                temporal_completeness_pct=0.0,
            )

        indices = [item[0] for item in date_records]
        timestamps = [item[1] for item in date_records]
        sorted_indices = sorted(indices, key=lambda i: timestamps[indices.index(i)])
        has_out_of_order = indices != sorted_indices

        min_dt = min(timestamps)
        max_dt = max(timestamps)
        unique_dates = sorted(list(set(timestamps)))

        freq_str = "IRREGULAR"
        missing_periods: List[str] = []
        if len(unique_dates) >= 2:
            is_all_day_1 = all(d.day == 1 for d in unique_dates)
            diffs = [(unique_dates[i] - unique_dates[i - 1]).days for i in range(1, len(unique_dates))]
            median_diff = sorted(diffs)[len(diffs) // 2]

            if is_all_day_1:
                freq_str = "MONTHLY"
            elif median_diff == 1:
                freq_str = "DAILY"
            elif 6 <= median_diff <= 8:
                freq_str = "WEEKLY"
            elif 28 <= median_diff <= 31:
                freq_str = "MONTHLY"
            else:
                freq_str = "IRREGULAR"

            if freq_str in ("DAILY", "WEEKLY", "MONTHLY"):
                expected_range = pd.date_range(
                    start=min_dt,
                    end=max_dt,
                    freq="D" if freq_str == "DAILY" else ("W" if freq_str == "WEEKLY" else "MS"),
                )
                actual_date_set = set(d.strftime("%Y-%m-%d") for d in unique_dates)
                for exp_dt in expected_range:
                    exp_str = exp_dt.strftime("%Y-%m-%d")
                    if exp_str not in actual_date_set:
                        missing_periods.append(exp_str)

        is_partial = False
        if max_dt.day not in (28, 29, 30, 31) and freq_str == "MONTHLY":
            is_partial = True

        total_detected = len(unique_dates)
        completeness = 100.0
        if missing_periods:
            expected_total = total_detected + len(missing_periods)
            completeness = round((total_detected / float(expected_total)) * 100.0, 2)

        return TemporalCoverage(
            min_date=min_dt.strftime("%Y-%m-%d"),
            max_date=max_dt.strftime("%Y-%m-%d"),
            total_periods_detected=total_detected,
            period_frequency=freq_str,
            missing_periods=missing_periods[:20],
            has_out_of_order_records=has_out_of_order,
            is_partial_month=is_partial,
            temporal_completeness_pct=completeness,
        )


class CompletenessEvaluator:
    """Evaluates 4-dimensional completeness: schema, record, domain, and temporal."""

    @classmethod
    def evaluate(
        cls,
        entity_name: Optional[str],
        mapped_fields: Set[str],
        quality_summary: DataQualitySummary,
        temporal_coverage: TemporalCoverage,
    ) -> CompletenessSummary:
        """Calculates 4-dimensional completeness metrics."""
        required = ENTITY_REQUIRED_FIELDS.get(entity_name or "", set())

        missing_req = [f for f in required if f not in mapped_fields]
        schema_comp = 100.0
        if required:
            schema_comp = round(((len(required) - len(missing_req)) / float(len(required))) * 100.0, 2)

        record_comp = 0.0
        if quality_summary.total_records > 0:
            record_comp = round(
                (quality_summary.accepted_records / float(quality_summary.total_records)) * 100.0,
                2,
            )

        temp_comp = temporal_coverage.temporal_completeness_pct
        domain_comp = round((schema_comp * 0.4) + (record_comp * 0.4) + (temp_comp * 0.2), 2)

        return CompletenessSummary(
            schema_completeness_pct=schema_comp,
            record_completeness_pct=record_comp,
            domain_completeness_pct=domain_comp,
            temporal_completeness_pct=temp_comp,
            missing_required_fields=missing_req,
            missing_optional_fields=[],
        )


class OnboardingQualityEngine:
    """Master evaluator coordinating quality, temporal, and completeness analysis."""

    @classmethod
    def evaluate(
        cls,
        records: List[Dict[str, Any]],
        entity_name: Optional[str],
        mapped_fields: Set[str],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], DataQualitySummary, TemporalCoverage, CompletenessSummary]:
        """Performs full quality validation, temporal coverage, and completeness assessment."""
        allow_negative_fields: Set[str] = set()

        if entity_name == "inventory_movement_history":
            # Historical inventory ledgers may legitimately record a
            # negative closing balance representing an inventory deficit.
            # Preserve the source fact rather than silently rejecting it.
            allow_negative_fields.add("on_hand")

        accepted, rejected, quality = QualityValidator.validate_records(
            records,
            mapped_fields,
            allow_negative_fields=allow_negative_fields,
        )

        temporal_field = (
            "period"
            if entity_name == "inventory_movement_history"
            else "date"
        )

        temporal = TemporalCoverageAnalyzer.analyze(
            accepted,
            date_field=temporal_field,
        )
        completeness = CompletenessEvaluator.evaluate(entity_name, mapped_fields, quality, temporal)

        return accepted, rejected, quality, temporal, completeness