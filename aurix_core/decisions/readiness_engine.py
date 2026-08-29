"""
AURIX Deterministic Decision Engine 2.0 — Decision Readiness Assessor
Phase 27 Core Implementation.
Assesses data and constraint completeness across operating domains before sanctioning decision generation.
"""

from __future__ import annotations

from aurix_core.decisions.contracts import DecisionReadinessReport


class DecisionReadinessEngine:
    """Assesses domain data sufficiency before generating automated decisions."""

    @classmethod
    def evaluate_readiness(
        cls,
        tenant_id: str,
        suppliers_count: int,
        customers_count: int,
        work_orders_count: int,
        invoices_count: int,
    ) -> DecisionReadinessReport:
        """Compute verifiable readiness states across decision domains."""
        proc_ready = "HIGH" if suppliers_count >= 5 else ("PARTIAL" if suppliers_count > 0 else "LOW")
        inv_ready = "HIGH" if invoices_count >= 10 else "PARTIAL"
        price_ready = "HIGH" if customers_count >= 10 else "PARTIAL"
        mfg_ready = "HIGH" if work_orders_count >= 5 else "PARTIAL"

        scores = [
            1.0 if proc_ready == "HIGH" else 0.5,
            1.0 if inv_ready == "HIGH" else 0.5,
            1.0 if price_ready == "HIGH" else 0.5,
            1.0 if mfg_ready == "HIGH" else 0.5,
        ]
        avg_pct = round((sum(scores) / len(scores)) * 100.0, 1)

        return DecisionReadinessReport(
            tenant_id=tenant_id,
            procurement_readiness=proc_ready,
            inventory_readiness=inv_ready,
            pricing_readiness=price_ready,
            manufacturing_readiness=mfg_ready,
            overall_readiness_pct=avg_pct,
        )
