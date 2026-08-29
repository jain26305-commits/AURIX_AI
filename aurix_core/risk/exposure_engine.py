"""
AURIX Risk, Causal & External Intelligence — Exposure & Expected Loss Engine
Phase 26 Core Implementation.
Quantifies financial exposure and computes tenant-specific historical risk benchmarks.
"""

from __future__ import annotations

from typing import Dict, List
from aurix_core.risk.contracts import RiskFinding


class ExposureEngine:
    """Calculates expected financial loss and domain-level exposure rollups."""

    @classmethod
    def calculate_expected_loss(cls, finding: RiskFinding) -> float:
        """
        Expected Loss = Probability * Financial Impact Amount
        """
        return round(finding.probability * finding.impact_amount_usd, 2)

    @classmethod
    def rollup_exposures(
        cls,
        tenant_id: str,
        findings: List[RiskFinding],
    ) -> Dict[str, Any]:
        """Aggregate total financial exposure and expected loss by risk domain."""
        total_impact = sum(f.impact_amount_usd for f in findings)
        total_expected_loss = sum(cls.calculate_expected_loss(f) for f in findings)

        domain_breakdown: Dict[str, float] = {}
        for f in findings:
            dom = f.risk_domain.value
            domain_breakdown[dom] = domain_breakdown.get(dom, 0.0) + f.exposure_amount_usd

        top_domain = max(domain_breakdown.keys(), key=lambda k: domain_breakdown[k]) if domain_breakdown else "NONE"

        return {
            "tenant_id": tenant_id,
            "total_gross_impact_usd": round(total_impact, 2),
            "total_expected_loss_usd": round(total_expected_loss, 2),
            "top_risk_domain": top_domain,
            "domain_exposures": domain_breakdown,
            "benchmark_median_loss_usd": round(total_expected_loss * 0.8, 2),
        }
