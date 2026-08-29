"""
AURIX Enterprise Sales & Commercial Intelligence — Channel & Regional Analytics
Phase 22 Core Implementation.
Evaluates revenue, margin, and order density across sales channels and geographies.
"""

from __future__ import annotations

from typing import Any, Dict, List
from aurix_core.commercial.contracts import ChannelPerformanceSummary


class ChannelIntelligenceEngine:
    """Compares commercial margin and velocity across Direct, Distributor, and E-Commerce channels."""

    @classmethod
    def evaluate_channels(
        cls,
        tenant_id: str,
        orders: List[Dict[str, Any]],
        cogs_rate: float = 0.60,
    ) -> List[ChannelPerformanceSummary]:
        """Aggregate sales performance by commercial channel."""
        channel_data: Dict[str, Dict[str, Any]] = {}
        total_net_rev = 0.0

        for o in orders:
            chan = str(o.get("channel") or "DIRECT").upper()
            amt = float(o.get("total_amount") or 0.0)
            disc = float(o.get("discount_amount") or 0.0)
            net_amt = amt - disc
            total_net_rev += net_amt

            if chan not in channel_data:
                channel_data[chan] = {"gross": 0.0, "net": 0.0, "orders": 0}

            channel_data[chan]["gross"] += amt
            channel_data[chan]["net"] += net_amt
            channel_data[chan]["orders"] += 1

        summaries: List[ChannelPerformanceSummary] = []
        for chan, data in channel_data.items():
            net = data["net"]
            cogs = net * cogs_rate
            gp = net - cogs
            gm_pct = round((gp / max(1.0, net)) * 100.0, 2)
            aov = net / max(1, data["orders"])
            contrib_pct = round((net / max(1.0, total_net_rev)) * 100.0, 2)

            summaries.append(
                ChannelPerformanceSummary(
                    channel_name=chan,
                    gross_revenue=round(data["gross"], 2),
                    net_revenue=round(net, 2),
                    cogs=round(cogs, 2),
                    gross_profit=round(gp, 2),
                    gross_margin_pct=gm_pct,
                    order_count=data["orders"],
                    average_order_value=round(aov, 2),
                    revenue_contribution_pct=contrib_pct,
                )
            )

        summaries.sort(key=lambda x: x.net_revenue, reverse=True)
        return summaries
