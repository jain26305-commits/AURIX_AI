"""
AURIX Continuous Assurance — Master Assurance Orchestrator
Phase 20 Core Implementation.
Orchestrates multi-domain sweeps across 3-way match, double payments, shipments, inventory, and pricing.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from aurix_core.assurance.contracts import (
    AssuranceFinding,
    AssuranceRunSummary,
)
from aurix_core.assurance.double_payment import DoublePaymentEngine
from aurix_core.assurance.leakage_quantifier import LeakageQuantifier
from aurix_core.assurance.phantom_inventory import PhantomInventoryEngine
from aurix_core.assurance.price_variance import PriceVarianceEngine
from aurix_core.assurance.three_way_match import ThreeWayMatchEngine
from aurix_core.assurance.unbilled_shipments import UnbilledShipmentsEngine

logger = logging.getLogger("aurix.assurance.orchestrator")


class AssuranceOrchestrator:
    """Coordinates continuous multi-domain commercial audit sweeps."""

    _findings_store: Dict[str, List[AssuranceFinding]] = {}

    @classmethod
    def clear_test_store(cls) -> None:
        """Clear findings memory store for unit testing."""
        cls._findings_store.clear()

    @classmethod
    def run_assurance_sweep(
        cls,
        tenant_id: str,
        purchase_orders: List[Dict[str, Any]],
        receipts: List[Dict[str, Any]],
        invoices: List[Dict[str, Any]],
        payments: List[Dict[str, Any]],
        shipments: List[Dict[str, Any]],
        orders: List[Dict[str, Any]],
        inventory_positions: List[Dict[str, Any]],
        cycle_counts: Optional[List[Dict[str, Any]]] = None,
        price_book: Optional[Dict[str, float]] = None,
    ) -> Tuple[List[AssuranceFinding], AssuranceRunSummary]:
        """Execute complete continuous assurance audit across all 5 risk dimensions."""
        all_findings: List[AssuranceFinding] = []

        # 1. Three-Way Matching Sweep
        po_map = {str(p.get("id") or p.get("po_number") or ""): p for p in purchase_orders}
        rcpt_map = {str(r.get("po_id") or r.get("purchase_order_id") or ""): r for r in receipts}

        for inv in invoices:
            po_ref = str(inv.get("po_id") or inv.get("purchase_order_id") or "")
            po_data = po_map.get(po_ref, {})
            rcpt_data = rcpt_map.get(po_ref)

            if po_data:
                _, finding = ThreeWayMatchEngine.evaluate(
                    tenant_id=tenant_id,
                    po=po_data,
                    receipt=rcpt_data,
                    invoice=inv,
                )
                if finding:
                    all_findings.append(finding)

        # 2. Double Payment Sweep
        dp_findings = DoublePaymentEngine.evaluate_payments(
            tenant_id=tenant_id,
            payments=payments,
            invoices=invoices,
        )
        all_findings.extend(dp_findings)

        # 3. Unbilled Shipments Sweep
        unbilled_findings = UnbilledShipmentsEngine.evaluate_unbilled_shipments(
            tenant_id=tenant_id,
            shipments=shipments,
            orders=orders,
            invoices=invoices,
        )
        all_findings.extend(unbilled_findings)

        # 4. Phantom Inventory & Shrinkage Sweep
        inv_findings = PhantomInventoryEngine.evaluate_inventory(
            tenant_id=tenant_id,
            positions=inventory_positions,
            cycle_counts=cycle_counts,
        )
        all_findings.extend(inv_findings)

        # 5. Price Variance & PPV Sweep
        if price_book:
            pv_findings = PriceVarianceEngine.evaluate_po_pricing(
                tenant_id=tenant_id,
                purchase_orders=purchase_orders,
                price_book=price_book,
            )
            all_findings.extend(pv_findings)

        # Quantify & Store
        quant = LeakageQuantifier.quantify(tenant_id, all_findings)
        cls._findings_store[tenant_id] = all_findings

        summary = AssuranceRunSummary(
            tenant_id=tenant_id,
            total_findings=quant["total_findings_count"],
            total_financial_leakage=quant["total_financial_leakage"],
            critical_findings_count=quant["critical_severity_count"],
            high_findings_count=quant["high_severity_count"],
            domain_breakdown=quant["findings_count_by_domain"],
        )

        return all_findings, summary

    @classmethod
    def get_findings(
        cls,
        tenant_id: str,
        domain: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> List[AssuranceFinding]:
        """Retrieve stored assurance findings with tenant isolation."""
        tenant_findings = cls._findings_store.get(tenant_id, [])
        results = tenant_findings
        if domain:
            results = [f for f in results if f.domain.value == domain]
        if severity:
            results = [f for f in results if f.severity.value == severity]
        return results
