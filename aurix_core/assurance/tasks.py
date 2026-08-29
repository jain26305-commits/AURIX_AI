"""
AURIX Continuous Assurance — Celery Background Tasks
Phase 20 Core Implementation.
Executes scheduled background audit sweeps and auto-proposes remediations.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List
from aurix_core.assurance.contracts import LeakageSeverity
from aurix_core.assurance.orchestrator import AssuranceOrchestrator
from aurix_core.assurance.remediation import AssuranceRemediationBridge

logger = logging.getLogger("aurix.assurance.tasks")


def execute_tenant_assurance_job(
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
) -> Dict[str, Any]:
    """Synchronous worker execution unit for continuous assurance sweep."""
    logger.info("Starting scheduled Continuous Assurance sweep for tenant [%s]", tenant_id)

    findings, summary = AssuranceOrchestrator.run_assurance_sweep(
        tenant_id=tenant_id,
        purchase_orders=purchase_orders,
        receipts=receipts,
        invoices=invoices,
        payments=payments,
        shipments=shipments,
        orders=orders,
        inventory_positions=inventory_positions,
        cycle_counts=cycle_counts,
        price_book=price_book,
    )

    proposed_actions = []
    for f in findings:
        if f.severity in (LeakageSeverity.CRITICAL, LeakageSeverity.HIGH):
            action_proposal = AssuranceRemediationBridge.create_action_proposal(f)
            proposed_actions.append(action_proposal)

    logger.info(
        "Assurance sweep completed for tenant [%s]: %d findings, %d critical/high actions proposed",
        tenant_id,
        len(findings),
        len(proposed_actions),
    )

    return {
        "tenant_id": tenant_id,
        "run_id": summary.run_id,
        "total_findings": summary.total_findings,
        "financial_leakage": summary.total_financial_leakage,
        "actions_proposed_count": len(proposed_actions),
        "actions": proposed_actions,
    }
