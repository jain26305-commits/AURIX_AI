"""
AURIX Manufacturing & Production Intelligence — Master Orchestrator
Phase 23 Core Implementation.
Coordinates BOM, MRP, Capacity, OEE, Quality, Downtime, and Manufacturing Summary.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from aurix_core.manufacturing.anomaly_engine import ManufacturingAnomalyEngine
from aurix_core.manufacturing.capacity_engine import CapacityEngine
from aurix_core.manufacturing.contracts import (
    DataAvailabilityStatus,
    ManufacturingSummaryReport,
)
from aurix_core.manufacturing.downtime_engine import DowntimeEngine
from aurix_core.manufacturing.oee_engine import OEEEngine
from aurix_core.manufacturing.quality_engine import QualityEngine
from aurix_core.manufacturing.revenue_at_risk import RevenueAtRiskEngine

logger = logging.getLogger("aurix.manufacturing.orchestrator")


class ManufacturingOrchestrator:
    """Master manufacturing and production operating intelligence coordinator."""

    _summary_cache: Dict[str, ManufacturingSummaryReport] = {}

    @classmethod
    def run_manufacturing_sweep(
        cls,
        tenant_id: str,
        work_centers: List[Dict[str, Any]],
        work_orders: List[Dict[str, Any]],
        production_events: List[Dict[str, Any]],
        downtime_events: List[Dict[str, Any]],
        sales_orders: Optional[List[Dict[str, Any]]] = None,
        period_key: str = "CURRENT",
    ) -> ManufacturingSummaryReport:
        """Execute complete manufacturing intelligence analysis sweep."""
        # 1. Capacity & Bottlenecks
        cap_summaries = CapacityEngine.evaluate_capacity(tenant_id, work_centers, work_orders)
        bottleneck_count = len([c for c in cap_summaries if c.is_bottleneck])
        avg_utilization = round(sum(c.utilization_pct for c in cap_summaries) / max(1, len(cap_summaries)), 1) if cap_summaries else 0.0

        # 2. Quality & Scrap
        quality_summary = QualityEngine.evaluate_quality(tenant_id, production_events, period_key=period_key)

        # 3. Downtime Analysis
        downtime_summary = DowntimeEngine.analyze_downtime(tenant_id, downtime_events, period_key=period_key)

        # 4. Revenue at Risk
        delayed_wos = [w for w in work_orders if str(w.get("status")).upper() in ("SCHEDULED", "DELAYED", "CONSTRAINED")]
        risk_summary = RevenueAtRiskEngine.evaluate_revenue_at_risk(tenant_id, delayed_wos, sales_orders or [], period_key)

        # 5. OEE Calculation (Aggregated)
        total_run_mins = sum(float(w.get("actual_run_time_minutes") or 0.0) for w in work_orders)
        total_planned_mins = sum(float(w.get("planned_run_time_minutes") or 0.0) for w in work_orders)
        total_good = quality_summary.good_units_produced
        total_output = quality_summary.total_units_produced

        oee_metric = OEEEngine.calculate_oee(
            work_center_id="PLANT_AGGREGATE",
            period_key=period_key,
            planned_production_minutes=total_planned_mins,
            actual_run_time_minutes=total_run_mins,
            theoretical_output_units=total_output,
            actual_output_units=total_output,
            good_units=total_good,
        )

        # 6. Anomalies
        anomalies = ManufacturingAnomalyEngine.audit_anomalies(tenant_id, production_events)

        summary = ManufacturingSummaryReport(
            tenant_id=tenant_id,
            period_key=period_key,
            total_work_orders=len(work_orders),
            active_work_orders=len([w for w in work_orders if str(w.get("status")).upper() != "COMPLETED"]),
            plant_capacity_utilization_pct=avg_utilization,
            overall_oee_pct=oee_metric.oee_pct,
            oee_status=oee_metric.oee_status,
            first_pass_yield_pct=quality_summary.first_pass_yield_pct,
            scrap_rate_pct=quality_summary.scrap_rate_pct,
            total_downtime_hours=round(downtime_summary.total_downtime_minutes / 60.0, 1),
            total_production_revenue_at_risk=risk_summary.total_revenue_at_risk,
            bottleneck_work_centers_count=bottleneck_count,
            active_anomalies_count=len(anomalies),
        )

        cls._summary_cache[tenant_id] = summary
        return summary
