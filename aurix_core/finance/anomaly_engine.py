"""
AURIX Business Finance Intelligence — Financial Anomaly Detection Engine
Phase 21 Core Implementation.
Statistical outlier detection (Z-score, IQR, margin dilution drops) without fake ML models.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List
from aurix_core.finance.contracts import (
    FinancialAnomalyDomain,
    FinancialAnomalyFinding,
)


class FinancialAnomalyEngine:
    """Statistical outlier and financial transaction anomaly detector."""

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
    def audit_transactions(
        cls,
        tenant_id: str,
        invoices: List[Dict[str, Any]],
        z_threshold: float = 2.5,
    ) -> List[FinancialAnomalyFinding]:
        """Scan transaction amounts for statistical outliers."""
        findings: List[FinancialAnomalyFinding] = []
        amounts = [float(inv.get("total_amount") or 0.0) for inv in invoices]
        if not amounts:
            return findings

        z_scores = cls.calculate_z_scores(amounts)
        mean_amt = sum(amounts) / len(amounts)

        for idx, z in enumerate(z_scores):
            if abs(z) >= z_threshold:
                inv = invoices[idx]
                amt = amounts[idx]
                inv_id = str(inv.get("id") or inv.get("invoice_number") or f"INV-{idx}")
                dev_pct = round(((amt - mean_amt) / max(1.0, mean_amt)) * 100.0, 1)

                findings.append(
                    FinancialAnomalyFinding(
                        tenant_id=tenant_id,
                        domain=FinancialAnomalyDomain.INVOICE_SPIKE,
                        severity="HIGH" if abs(z) > 3.5 else "MEDIUM",
                        title=f"Statistical Outlier on Invoice {inv_id}",
                        description=f"Invoice amount ({amt}) is {abs(z):.2f} std deviations from mean ({mean_amt:.2f}).",
                        detected_metric_value=amt,
                        baseline_expected_value=round(mean_amt, 2),
                        deviation_pct=dev_pct,
                        entity_id=inv_id,
                    )
                )

        return findings
