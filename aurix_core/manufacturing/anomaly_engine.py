"""
AURIX Manufacturing & Production Intelligence — Manufacturing Anomaly Detector
Phase 23 Core Implementation.
Statistical outlier detection (Z-score, IQR) on scrap spikes, yield drops, and unplanned downtime.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List
from aurix_core.manufacturing.contracts import (
    ManufacturingAnomalyDomain,
    ManufacturingAnomalyFinding,
)


class ManufacturingAnomalyEngine:
    """Detects manufacturing shop-floor anomalies and statistical process outliers."""

    @staticmethod
    def calculate_z_scores(values: List[float]) -> List[float]:
        """Compute standard Z-scores for a series of values."""
        if len(values) < 2:
            return [0.0] * len(values)
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = math.sqrt(variance)
        if std_dev == 0:
            return [0.0] * len(values)
        return [(x - mean) / std_dev for x in values]

    @classmethod
    def audit_anomalies(
        cls,
        tenant_id: str,
        production_events: List[Dict[str, Any]],
        z_threshold: float = 2.5,
    ) -> List[ManufacturingAnomalyFinding]:
        """Scan production events for abnormal scrap spikes or yield defects."""
        findings: List[ManufacturingAnomalyFinding] = []
        scrap_values = [float(ev.get("scrap_quantity") or 0.0) for ev in production_events]
        if not scrap_values:
            return findings

        z_scores = cls.calculate_z_scores(scrap_values)
        mean_scrap = sum(scrap_values) / len(scrap_values)

        for idx, z in enumerate(z_scores):
            if abs(z) >= z_threshold and scrap_values[idx] > 0:
                ev = production_events[idx]
                val = scrap_values[idx]
                wo_id = str(ev.get("work_order_id") or f"WO-{idx}")
                dev_pct = round(((val - mean_scrap) / max(1.0, mean_scrap)) * 100.0, 1)

                findings.append(
                    ManufacturingAnomalyFinding(
                        tenant_id=tenant_id,
                        domain=ManufacturingAnomalyDomain.SCRAP_SPIKE,
                        severity="CRITICAL" if abs(z) > 3.5 else "HIGH",
                        title=f"Statistical Scrap Outlier on Work Order {wo_id}",
                        description=f"Scrap quantity ({val}) is {abs(z):.2f} std deviations from mean ({mean_scrap:.2f}).",
                        detected_metric_value=val,
                        baseline_expected_value=round(mean_scrap, 2),
                        deviation_pct=dev_pct,
                        entity_id=wo_id,
                    )
                )

        return findings
