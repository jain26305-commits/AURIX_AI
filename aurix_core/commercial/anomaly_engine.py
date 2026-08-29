"""
AURIX Enterprise Sales & Commercial Intelligence — Commercial Anomaly Detector
Phase 22 Core Implementation.
Detects rogue discount concessions, sudden customer volume drop-offs, and defection risks.
"""

from __future__ import annotations

from typing import Any, Dict, List
from aurix_core.commercial.config import CommercialConfigManager
from aurix_core.commercial.contracts import (
    CommercialAnomalyDomain,
    CommercialAnomalyFinding,
)


class CommercialAnomalyEngine:
    """Detects commercial risk anomalies and behavioral outliers."""

    @classmethod
    def audit_commercial_anomalies(
        cls,
        tenant_id: str,
        orders: List[Dict[str, Any]],
        account_summaries: Optional[List[Any]] = None,
    ) -> List[CommercialAnomalyFinding]:
        """Scan orders and accounts for commercial exceptions."""
        config = CommercialConfigManager.get_config(tenant_id)
        findings: List[CommercialAnomalyFinding] = []

        # 1. Detect Rogue / Unauthorized Discount Spikes
        for o in orders:
            amt = float(o.get("total_amount") or 0.0)
            disc = float(o.get("discount_amount") or 0.0)
            o_id = str(o.get("id") or o.get("order_number") or "ORD-UNKNOWN")

            if amt > 0:
                rate = (disc / amt) * 100.0
                if rate > (config.max_authorized_discount_pct * 1.5):  # 150% of threshold
                    findings.append(
                        CommercialAnomalyFinding(
                            tenant_id=tenant_id,
                            domain=CommercialAnomalyDomain.UNAUTHORIZED_DISCOUNT,
                            severity="HIGH" if disc > 1000 else "MEDIUM",
                            title=f"Rogue Discount on Order {o_id}",
                            description=f"Discount of {rate:.1f}% (${disc}) exceeds authorized limit of {config.max_authorized_discount_pct}%.",
                            impact_amount=round(disc, 2),
                            entity_id=o_id,
                        )
                    )

        # 2. Detect Account Dormancy & Defection Risk
        if account_summaries:
            for acc in account_summaries:
                if acc.health_status.value in ("AT_RISK", "DORMANT") and acc.pareto_tier.value == "TIER_A":
                    findings.append(
                        CommercialAnomalyFinding(
                            tenant_id=tenant_id,
                            domain=CommercialAnomalyDomain.ACCOUNT_DORMANCY,
                            severity="CRITICAL",
                            title=f"Top-Tier Account At Risk: {acc.customer_name}",
                            description=f"Tier-A customer ({acc.customer_id}) has been inactive for {acc.days_since_last_order} days.",
                            impact_amount=acc.period_revenue,
                            entity_id=acc.customer_id,
                        )
                    )

        return findings
