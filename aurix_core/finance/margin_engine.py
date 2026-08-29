"""
AURIX Business Finance Intelligence — Gross & Contribution Margin Engine
Phase 21 Core Implementation.
Calculates margin economics with strict Zero-Fabrication data availability guards.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from aurix_core.finance.contracts import DataAvailabilityStatus, MarginSummary


class MarginEngine:
    """Calculates Gross Margin and Variable-Cost Contribution Margin."""

    @classmethod
    def calculate_margin(
        cls,
        tenant_id: str,
        net_revenue: float,
        cogs: float,
        variable_costs: Optional[float] = None,
    ) -> MarginSummary:
        """
        Gross Profit = Net Revenue - COGS
        Contribution Margin = Net Revenue - COGS - Variable Costs
        """
        if net_revenue <= 0:
            return MarginSummary(
                tenant_id=tenant_id,
                gross_profit=0.0,
                gross_margin_pct=0.0,
                contribution_margin=None,
                contribution_margin_pct=None,
                margin_status=DataAvailabilityStatus.INSUFFICIENT_DATA,
                notes="Net revenue is zero or negative; margin is undefined.",
            )

        gross_profit = round(net_revenue - cogs, 2)
        gross_margin_pct = round((gross_profit / net_revenue) * 100.0, 2)

        if variable_costs is not None and variable_costs >= 0:
            contrib_margin = round(net_revenue - cogs - variable_costs, 2)
            contrib_margin_pct = round((contrib_margin / net_revenue) * 100.0, 2)
            status = DataAvailabilityStatus.AVAILABLE
            notes = "Full contribution margin computed with verified variable costs."
        else:
            contrib_margin = None
            contrib_margin_pct = None
            status = DataAvailabilityStatus.PARTIALLY_AVAILABLE
            notes = "Gross margin available; variable operating costs unavailable for contribution margin."

        return MarginSummary(
            tenant_id=tenant_id,
            gross_profit=gross_profit,
            gross_margin_pct=gross_margin_pct,
            contribution_margin=contrib_margin,
            contribution_margin_pct=contrib_margin_pct,
            margin_status=status,
            notes=notes,
        )
