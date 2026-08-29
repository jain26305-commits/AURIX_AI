"""
AURIX Continuous Assurance — Financial Leakage Exposure Quantifier
Phase 20 Core Implementation.
Aggregates financial exposure, at-risk capital, and recovered value rollups.
"""

from __future__ import annotations

from typing import Any, Dict, List
from aurix_core.assurance.contracts import AssuranceFinding, LeakageSeverity


class LeakageQuantifier:
    """Consolidates total financial exposure and audit risk metrics."""

    @staticmethod
    def quantify(
        tenant_id: str,
        findings: List[AssuranceFinding],
    ) -> Dict[str, Any]:
        """Aggregate total financial exposure and category breakdowns."""
        total_exposure = 0.0
        critical_count = 0
        high_count = 0
        domain_leakage: Dict[str, float] = {}
        domain_counts: Dict[str, int] = {}

        for f in findings:
            total_exposure += f.financial_exposure
            dom = f.domain.value
            domain_leakage[dom] = domain_leakage.get(dom, 0.0) + f.financial_exposure
            domain_counts[dom] = domain_counts.get(dom, 0) + 1

            if f.severity == LeakageSeverity.CRITICAL:
                critical_count += 1
            elif f.severity == LeakageSeverity.HIGH:
                high_count += 1

        return {
            "tenant_id": tenant_id,
            "total_findings_count": len(findings),
            "total_financial_leakage": round(total_exposure, 2),
            "critical_severity_count": critical_count,
            "high_severity_count": high_count,
            "leakage_by_domain": {k: round(v, 2) for k, v in domain_leakage.items()},
            "findings_count_by_domain": domain_counts,
        }
