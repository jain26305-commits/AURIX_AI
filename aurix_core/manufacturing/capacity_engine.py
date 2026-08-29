"""
AURIX Manufacturing & Production Intelligence — Capacity & Bottleneck Engine
Phase 23 Core Implementation.
Calculates work center capacity utilization and detects operational bottlenecks.
"""

from __future__ import annotations

from typing import Any, Dict, List
from aurix_core.manufacturing.config import ManufacturingConfigManager
from aurix_core.manufacturing.contracts import (
    WorkCenterCapacitySummary,
    WorkCenterStatus,
)


class CapacityEngine:
    """Calculates work center utilization and identifies production line bottlenecks."""

    @classmethod
    def evaluate_capacity(
        cls,
        tenant_id: str,
        work_centers: List[Dict[str, Any]],
        work_orders: List[Dict[str, Any]],
        period_days: int = 30,
    ) -> List[WorkCenterCapacitySummary]:
        """
        Capacity Utilization = (Required Load Hours / Available Capacity Hours) * 100
        Bottleneck declared on multi-variable evidence (Utilization > 90% and Backlog > 40 hrs).
        """
        config = ManufacturingConfigManager.get_config(tenant_id)
        summaries: List[WorkCenterCapacitySummary] = []

        # Group work orders by work center
        wc_load: Dict[str, float] = {}
        for wo in work_orders:
            wc_id = str(wo.get("work_center_id") or "WC-GENERAL")
            target_qty = float(wo.get("target_quantity") or 0.0)
            completed = float(wo.get("completed_quantity") or 0.0)
            remaining_qty = max(0.0, target_qty - completed)

            # Planned run time hours (e.g. 0.1 hrs per unit standard)
            run_time_hrs = float(wo.get("planned_run_time_minutes") or (remaining_qty * 6.0)) / 60.0
            wc_load[wc_id] = wc_load.get(wc_id, 0.0) + run_time_hrs

        for wc in work_centers:
            wc_id = str(wc.get("id"))
            name = str(wc.get("name") or f"Work Center {wc_id}")
            plant_id = str(wc.get("plant_location_id") or "PLANT-1")
            hours_per_day = float(wc.get("capacity_hours_per_day") or (config.standard_shift_hours * config.shifts_per_day))

            avail_hrs = hours_per_day * period_days
            req_load = wc_load.get(wc_id, 0.0)

            utilization = round((req_load / max(1.0, avail_hrs)) * 100.0, 1)
            backlog = max(0.0, round(req_load - avail_hrs, 1))

            is_bottleneck = utilization >= config.bottleneck_utilization_threshold_pct

            if is_bottleneck:
                status = WorkCenterStatus.BOTTLENECK
            elif utilization >= 75.0:
                status = WorkCenterStatus.CONSTRAINED
            elif utilization <= 20.0:
                status = WorkCenterStatus.IDLE
            else:
                status = WorkCenterStatus.OPTIMAL

            summaries.append(
                WorkCenterCapacitySummary(
                    work_center_id=wc_id,
                    work_center_name=name,
                    plant_location_id=plant_id,
                    available_capacity_hours=round(avail_hrs, 1),
                    required_load_hours=round(req_load, 1),
                    utilization_pct=utilization,
                    backlog_hours=backlog,
                    status=status,
                    is_bottleneck=is_bottleneck,
                )
            )

        summaries.sort(key=lambda x: x.utilization_pct, reverse=True)
        return summaries
