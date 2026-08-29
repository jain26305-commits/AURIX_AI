"""
AURIX Business Finance Intelligence — Cash Intelligence Foundation
Phase 21 Core Implementation.
Models short-term operating cash flow trajectory and collections vs. disbursement timing.
"""

from __future__ import annotations

from typing import Any, Dict, List
from aurix_core.finance.contracts import CashFlowForecastSummary


class CashIntelligenceEngine:
    """Projects 30-day operating cash trajectory from AR/AP schedules."""

    @classmethod
    def project_operating_cash(
        cls,
        tenant_id: str,
        current_cash_balance: float,
        expected_ar_inflows: float,
        expected_ap_outflows: float,
        currency: str = "USD",
    ) -> CashFlowForecastSummary:
        """Calculate short-term projected operating cash position."""
        net_cash_30d = round(current_cash_balance + expected_ar_inflows - expected_ap_outflows, 2)

        return CashFlowForecastSummary(
            tenant_id=tenant_id,
            currency=currency,
            current_cash_position=round(current_cash_balance, 2),
            expected_inflows_30d=round(expected_ar_inflows, 2),
            expected_outflows_30d=round(expected_ap_outflows, 2),
            projected_net_operating_cash_30d=net_cash_30d,
        )
