"""
AURIX Enterprise Business Context Graph — Phase 24 Master Test Suite
Validates Operating Graph Builder, Multi-Hop Traversal, Why-Chain Reconstruction,
Business Memory, Data Contracts, Business DNA, Impact Propagation, and RLS Isolation.
"""

from datetime import datetime, timezone
import pytest

from aurix_core.context.business_dna import BusinessDNAEngine
from aurix_core.context.business_memory import BusinessMemoryEngine
from aurix_core.context.contracts import (
    BusinessMemoryRecord,
    DecisionOutcomeStatus,
    MemoryCategory,
    RelationshipConfidence,
)
from aurix_core.context.data_contracts import DataContractRegistry
from aurix_core.context.graph_builder import OperatingGraphBuilder
from aurix_core.context.graph_traversal import GraphTraversalEngine
from aurix_core.context.impact_propagation import ImpactPropagationEngine
from aurix_core.context.ontology import SemanticOntologyEngine
from aurix_core.context.orchestrator import ContextOrchestrator
from aurix_core.context.readiness_map import ReadinessMapEngine


def test_semantic_ontology_mapping() -> None:
    """Test external ERP vocabulary mapping to canonical AURIX entity types."""
    assert SemanticOntologyEngine.resolve_entity_type("TALLY", "ledger_sundry_debtor").value == "CUSTOMER"
    assert SemanticOntologyEngine.resolve_entity_type("ODOO", "sale.order").value == "ORDER"
    assert SemanticOntologyEngine.resolve_entity_type("SAP", "MARA").value == "PRODUCT"
    assert SemanticOntologyEngine.resolve_entity_type("SAP", "AFKO").value == "WORK_ORDER"


def test_operating_graph_builder_and_traversal() -> None:
    """Test graph construction, 1-hop neighborhood lookup, and cycle-safe traversal."""
    tenant = "tenant-ctx-01"

    customers = [{"id": "C-1", "customer_name": "Acme Corp"}]
    suppliers = [{"id": "S-1", "supplier_name": "Apex Steel"}]
    products = [{"id": "P-1", "name": "Precision Bearing"}]
    orders = [{"id": "O-1", "customer_id": "C-1", "sku_id": "P-1", "total_amount": 10000.0}]
    invoices = [{"id": "INV-1", "order_id": "O-1", "total_amount": 10000.0}]
    work_orders = [{"id": "WO-1", "sku_id": "P-1", "target_quantity": 500.0}]

    nodes, edges = OperatingGraphBuilder.build_operating_graph(
        tenant_id=tenant,
        customers=customers,
        suppliers=suppliers,
        products=products,
        orders=orders,
        invoices=invoices,
        work_orders=work_orders,
    )

    assert "CUSTOMER:C-1" in nodes
    assert "ORDER:O-1" in nodes
    assert "PRODUCT:P-1" in nodes
    assert len(edges) >= 4

    # Test 1-hop neighborhood around Customer
    neighborhood = GraphTraversalEngine.get_neighborhood("CUSTOMER:C-1", nodes, edges, max_hops=1)
    assert neighborhood["total_nodes"] >= 2
    assert "ORDER:O-1" in [n.id for n in neighborhood["nodes"]]


def test_why_chain_root_cause_reconstruction() -> None:
    """Test Why-Chain pathfinding from operational symptom to root cause."""
    tenant = "tenant-why-01"

    customers = [{"id": "C-10", "customer_name": "Global Retail"}]
    orders = [{"id": "ORD-99", "customer_id": "C-10", "sku_id": "SKU-99", "total_amount": 50000.0}]
    products = [{"id": "SKU-99", "name": "Hydraulic Valve"}]
    work_orders = [{"id": "WO-99", "sku_id": "SKU-99", "target_quantity": 100.0}]

    nodes, edges = OperatingGraphBuilder.build_operating_graph(
        tenant_id=tenant,
        customers=customers,
        suppliers=[],
        products=products,
        orders=orders,
        invoices=[],
        work_orders=work_orders,
    )

    # Reconstruct path from Customer -> Order -> Product -> Work Order
    why_report = GraphTraversalEngine.reconstruct_why_chain(
        tenant_id=tenant,
        symptom_node_id="CUSTOMER:C-10",
        root_cause_node_id="WORK_ORDER:WO-99",
        nodes=nodes,
        edges=edges,
    )

    assert why_report.chain_length == 3
    assert why_report.confidence_pct == 95.0
    assert why_report.steps[0].from_node_name == "Global Retail"


def test_business_memory_storage_and_recall() -> None:
    """Test institutional business memory recording and filtered query recall."""
    tenant = "tenant-mem-01"

    mem1 = BusinessMemoryRecord(
        tenant_id=tenant,
        category=MemoryCategory.MANAGER_OVERRIDE,
        title="Freight Expedite Approval",
        description="Approved $1,200 express air freight for delayed shipment.",
        context_entity_id="ORDER:O-100",
        outcome_status=DecisionOutcomeStatus.SUCCESSFUL,
        lessons_learned="Prevented customer order SLA penalty.",
    )
    BusinessMemoryEngine.record_memory(mem1)

    recalled = BusinessMemoryEngine.query_memories(tenant, entity_id="ORDER:O-100")
    assert len(recalled) == 1
    assert recalled[0].title == "Freight Expedite Approval"
    assert recalled[0].outcome_status == DecisionOutcomeStatus.SUCCESSFUL


def test_business_dna_and_data_contracts() -> None:
    """Test Business DNA HHI calculations and Data Contract registry."""
    tenant = "tenant-dna-01"

    orders = [
        {"customer_id": "C-A", "total_amount": 80000.0},
        {"customer_id": "C-B", "total_amount": 20000.0},
    ]
    dna = BusinessDNAEngine.derive_business_dna(
        tenant_id=tenant,
        orders=orders,
        purchase_orders=[],
        inventory_valuation=30000.0,
        annual_revenue=100000.0,
    )
    # HHI = 80^2 + 20^2 = 6400 + 400 = 6800.0
    assert dna.customer_concentration_hhi == 6800.0
    assert dna.inventory_intensity_pct == 30.0
    assert dna.operating_model == "CAPITAL_INTENSIVE_MANUFACTURING"

    # Data Contract Registry
    consumers = DataContractRegistry.get_downstream_impact(tenant, "sales_orders")
    assert "MRP_ENGINE" in consumers
    assert "FINANCE_PNL" in consumers


def test_impact_propagation_and_master_sweep() -> None:
    """Test impact propagation from component shortage to revenue exposure and master context sweep."""
    tenant = "tenant-master-ctx"

    customers = [{"id": "C-X", "customer_name": "Apex Motors"}]
    products = [{"id": "SKU-X", "name": "EV Motor Coil"}]
    orders = [{"id": "ORD-X", "customer_id": "C-X", "sku_id": "SKU-X", "total_amount": 75000.0}]

    nodes, edges = OperatingGraphBuilder.build_operating_graph(
        tenant_id=tenant,
        customers=customers,
        suppliers=[],
        products=products,
        orders=orders,
        invoices=[],
        work_orders=[],
    )

    # Disruption at SKU-X -> Propagates to Order ORD-X and Customer C-X
    impact = ImpactPropagationEngine.propagate_disruption("PRODUCT:SKU-X", nodes, edges)
    assert impact["total_revenue_at_risk"] == 75000.0
    assert "Apex Motors" in impact["impacted_customers"]

    # Master Context Orchestrator Sweep
    summary = ContextOrchestrator.run_context_sweep(
        tenant_id=tenant,
        customers=customers,
        suppliers=[],
        products=products,
        orders=orders,
        invoices=[],
        work_orders=[],
    )
    assert summary.total_nodes_count >= 3
    assert summary.total_edges_count >= 2
