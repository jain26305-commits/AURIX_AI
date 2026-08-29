"""
AURIX Manufacturing & Production Intelligence — Overall Equipment Effectiveness (OEE) Engine
Phase 23 Core Implementation.
Calculates Availability * Performance * Quality with strict Zero-Fabrication guards.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from aurix_core.manufacturing.contracts import (
    DataAvailabilityStatus,
    OEEMetrics,
)


class OEEEngine:
    """Computes Overall Equipment Effectiveness with verifiable data completeness checks."""

    @classmethod
    def calculate_oee(
        cls,
        work_center_id: str,
        period_key: str,
        planned_production_minutes: Optional[float],
        actual_run_time_minutes: Optional[float],
        theoretical_output_units: Optional[float],
        actual_output_units: Optional[float],
        good_units: Optional[float],
        scrap_units: Optional[float] = 0.0,
    ) -> OEEMetrics:
        """
        OEE = Availability * Performance * Quality
        Availability = Actual Run Time / Planned Production Time
        Performance  = Actual Output / Theoretical Output
        Quality      = Good Units / Actual Total Output
        """
        # Zero-Fabrication Guards
        if not planned_production_minutes or planned_production_minutes <= 0:
            return OEEMetrics(
                work_center_id=work_center_id,
                period_key=period_key,
                planned_production_time_minutes=0.0,
                actual_run_time_minutes=actual_run_time_minutes or 0.0,
                theoretical_output_units=theoretical_output_units or 0.0,
                actual_output_units=actual_output_units or 0.0,
                good_units=good_units or 0.0,
                scrap_units=scrap_units or 0.0,
                oee_status=DataAvailabilityStatus.UNAVAILABLE,
                notes="Planned production time telemetry unavailable; OEE cannot be fabricated.",
            )

        run_time = actual_run_time_minutes or 0.0
        avail_pct = min(100.0, round((run_time / planned_production_minutes) * 100.0, 2))

        perf_pct = None
        if theoretical_output_units and theoretical_output_units > 0 and actual_output_units is not None:
            perf_pct = min(100.0, round((actual_output_units / theoretical_output_units) * 100.0, 2))

        qual_pct = None
        if actual_output_units and actual_output_units > 0 and good_units is not None:
            qual_pct = min(100.0, round((good_units / actual_output_units) * 100.0, 2))

        if avail_pct is not None and perf_pct is not None and qual_pct is not None:
            oee = round((avail_pct / 100.0) * (perf_pct / 100.0) * (qual_pct / 100.0) * 100.0, 2)
            status = DataAvailabilityStatus.AVAILABLE
            notes = "Full OEE computed from validated Availability, Performance, and Quality."
        else:
            oee = None
            status = DataAvailabilityStatus.PARTIALLY_AVAILABLE
            notes = "Partial telemetry; some OEE component metrics are missing."

        return OEEMetrics(
            work_center_id=work_center_id,
            period_key=period_key,
            planned_production_time_minutes=planned_production_minutes,
            actual_run_time_minutes=run_time,
            theoretical_output_units=theoretical_output_units or 0.0,
            actual_output_units=actual_output_units or 0.0,
            good_units=good_units or 0.0,
            scrap_units=scrap_units or 0.0,
            availability_pct=avail_pct,
            performance_pct=perf_pct,
            quality_pct=qual_pct,
            oee_pct=oee,
            oee_status=status,
            notes=notes,
        )
