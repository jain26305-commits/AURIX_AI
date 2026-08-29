"""
AURIX Enterprise Business Context Graph — Master Context Orchestrator
Phase 24 Core Implementation.
Coordinates graph builder, memory retrieval, data contracts, Business DNA, and panoramic context rollups.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from aurix_core.context.business_dna import BusinessDNAEngine
from aurix_core.context.business_memory import BusinessMemoryEngine
from aurix_core.context.contracts import ContextSummaryReport
from aurix_core.context.data_contracts import DataContractRegistry
from aurix_core.context.graph_builder import OperatingGraphBuilder
from aurix_core.context.readiness_map import ReadinessMapEngine

logger = logging.getLogger("aurix.context.orchestrator")


class ContextOrchestrator:
    """Master business context coordinator managing graph projections and memory recall."""

    _summary_cache: Dict[str, ContextSummaryReport] = {}

    @classmethod
    def run_context_sweep(
        cls,
        tenant_id: str,
        customers: List[Dict[str, Any]],
        suppliers: List[Dict[str, Any]],
        products: List[Dict[str, Any]],
        orders: List[Dict[str, Any]],
        invoices: List[Dict[str, Any]],
        work_orders: List[Dict[str, Any]],
        findings: Optional[List[Dict[str, Any]]] = None,
        period_key: str = "CURRENT",
    ) -> ContextSummaryReport:
        """Execute complete panoramic business context graph build and evaluation."""
        # 1. Build Graph
        nodes, edges = OperatingGraphBuilder.build_operating_graph(
            tenant_id=tenant_id,
            customers=customers,
            suppliers=suppliers,
            products=products,
            orders=orders,
            invoices=invoices,
            work_orders=work_orders,
            findings=findings or [],
        )

        # 2. Derive Business DNA
        dna = BusinessDNAEngine.derive_business_dna(
            tenant_id=tenant_id,
            orders=orders,
            purchase_orders=[],
            inventory_valuation=150000.0,
            annual_revenue=sum(float(o.get("total_amount") or 0.0) for o in orders),
            period_key=period_key,
        )

        # 3. Evaluate Readiness
        readiness = ReadinessMapEngine.evaluate_readiness(
            tenant_id=tenant_id,
            orders_count=len(orders),
            invoices_count=len(invoices),
            work_orders_count=len(work_orders),
            assurance_findings_count=len(findings or []),
            suppliers_count=len(suppliers),
        )
        avg_readiness = round(sum(r.data_coverage_pct for r in readiness) / max(1, len(readiness)), 1)

        # 4. Query Memories and Contracts Count
        memories = BusinessMemoryEngine.query_memories(tenant_id)
        contracts = DataContractRegistry.get_contracts(tenant_id)

        summary = ContextSummaryReport(
            tenant_id=tenant_id,
            period_key=period_key,
            total_nodes_count=len(nodes),
            total_edges_count=len(edges),
            active_memories_count=len(memories),
            active_contracts_count=len(contracts),
            overall_readiness_pct=avg_readiness,
            business_dna_model=dna.operating_model,
        )

        cls._summary_cache[tenant_id] = summary
        return summary
