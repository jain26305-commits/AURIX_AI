"""
AURIX Enterprise Sales & Commercial Intelligence — Master Orchestrator
Phase 22 Core Implementation.
Coordinates Account 360, Commercial OTIF, PVM, Channel, Velocity, and Commercial Anomalies.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from aurix_core.commercial.account_360 import Account360Engine
from aurix_core.commercial.anomaly_engine import CommercialAnomalyEngine
from aurix_core.commercial.channel_intelligence import ChannelIntelligenceEngine
from aurix_core.commercial.contracts import CommercialSummaryReport
from aurix_core.commercial.order_performance import OrderPerformanceEngine
from aurix_core.commercial.pricing_intelligence import PricingIntelligenceEngine
from aurix_core.commercial.product_velocity import ProductVelocityEngine

logger = logging.getLogger("aurix.commercial.orchestrator")


class CommercialOrchestrator:
    """Master sales and commercial intelligence coordinator."""

    _summary_cache: Dict[str, CommercialSummaryReport] = {}

    @classmethod
    def run_commercial_sweep(
        cls,
        tenant_id: str,
        customers: List[Dict[str, Any]],
        orders: List[Dict[str, Any]],
        products: List[Dict[str, Any]],
        order_lines: Optional[List[Dict[str, Any]]] = None,
        period_key: str = "CURRENT",
    ) -> CommercialSummaryReport:
        """Execute end-to-end commercial operating intelligence analysis."""
        # 1. Account 360
        accounts = Account360Engine.evaluate_accounts(tenant_id, customers, orders)

        # 2. Order OTIF
        otif_report = OrderPerformanceEngine.evaluate_order_performance(tenant_id, orders, period_key)

        # 3. Channel Intelligence
        channels = ChannelIntelligenceEngine.evaluate_channels(tenant_id, orders)

        # 4. Pricing & Discount Leakage
        leakage = PricingIntelligenceEngine.audit_discount_leakage(tenant_id, orders)

        # 5. Product Velocity
        velocity = ProductVelocityEngine.evaluate_velocity(products, order_lines or [], len(orders))

        # 6. Commercial Anomalies
        anomalies = CommercialAnomalyEngine.audit_commercial_anomalies(tenant_id, orders, accounts)

        gross_rev = sum(float(o.get("total_amount") or 0.0) for o in orders)
        net_rev = gross_rev - sum(float(o.get("discount_amount") or 0.0) for o in orders)
        aov = net_rev / max(1, len(orders))

        active_custs = len([a for a in accounts if a.health_status.value in ("THRIVING", "STABLE")])
        dormant_custs = len([a for a in accounts if a.health_status.value in ("AT_RISK", "DORMANT", "CHURNED")])
        top_channel = channels[0].channel_name if channels else "DIRECT"

        summary = CommercialSummaryReport(
            tenant_id=tenant_id,
            period_key=period_key,
            gross_revenue=round(gross_rev, 2),
            net_revenue=round(net_rev, 2),
            total_orders=len(orders),
            average_order_value=round(aov, 2),
            active_customers_count=active_custs,
            dormant_customers_count=dormant_custs,
            commercial_otif_pct=otif_report.otif_rate_pct,
            overall_discount_pct=leakage.overall_discount_rate_pct,
            top_growth_channel=top_channel,
            active_anomalies_count=len(anomalies),
        )

        cls._summary_cache[tenant_id] = summary
        return summary
