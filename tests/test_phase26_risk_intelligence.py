"""
AURIX Risk, Causal & External Intelligence — Phase 26 Master Test Suite
Validates Enterprise Risk Engine, Exposure Math, Multi-Factor Prioritization, Risk Propagation,
Causal Classifications, External Reality Feeds, Signal Mapping, Opportunity Ranking, and Coverage.
"""

from datetime import datetime, timezone
import pytest

from aurix_core.risk.causal_engine import CausalEngine
from aurix_core.risk.contracts import (
    CausalClassification,
    RiskDomain,
    RiskSeverity,
    SignalType,
)
from aurix_core.risk.coverage_engine import RiskCoverageEngine
from aurix_core.risk.domain_signals import DomainSignalProcessors
from aurix_core.risk.exposure_engine import ExposureEngine
from aurix_core.risk.external_reality import ExternalRealityLayer
from aurix_core.risk.opportunity_engine import OpportunityEngine
from aurix_core.risk.orchestrator import RiskOrchestrator
from aurix_core.risk.prioritization_engine import PrioritizationEngine
from aurix_core.risk.propagation_engine import RiskPropagationEngine
from aurix_core.risk.risk_engine import RiskEngine
from aurix_core.risk.scenario_contracts import ScenarioContractBuilder
from aurix_core.risk.signal_mapping import SignalMappingEngine


def test_enterprise_risk_engine_and_exposure() -> None:
    """Test multi-domain risk evaluation and expected loss math."""
    tenant = "tenant-risk-01"

    suppliers = [{"id": "S-1", "supplier_name": "Apex Steel", "otif_rate": 65.0, "annual_spend": 200000.0}]
    customers = [{"id": "C-1", "customer_name": "Acme Retail", "health_score": 35.0, "period_revenue": 80000.0}]
    wos = [{"id": "WO-1", "status": "CONSTRAINED", "target_quantity": 500.0}]

    findings = RiskEngine.evaluate_risks(
        tenant_id=tenant,
        suppliers=suppliers,
        customers=customers,
        inventory_items=[],
        work_orders=wos,
        assurance_findings=[],
        process_bottlenecks=[],
    )

    assert len(findings) == 3
    # Supplier finding
    supp_f = [f for f in findings if f.risk_domain == RiskDomain.SUPPLIER][0]
    assert supp_f.severity == RiskSeverity.HIGH
    assert supp_f.exposure_amount_usd > 0

    # Expected loss rollup
    exposure_data = ExposureEngine.rollup_exposures(tenant, findings)
    assert exposure_data["total_expected_loss_usd"] > 0
    assert exposure_data["top_risk_domain"] in ("SUPPLIER", "CUSTOMER")


def test_multi_factor_business_impact_prioritization() -> None:
    """Test multi-factor risk prioritization score and descending sorting."""
    tenant = "tenant-prio-01"

    suppliers = [
        {"id": "S-LOW", "otif_rate": 80.0, "annual_spend": 20000.0},
        {"id": "S-CRIT", "otif_rate": 50.0, "annual_spend": 500000.0},
    ]

    findings = RiskEngine.evaluate_risks(
        tenant_id=tenant,
        suppliers=suppliers,
        customers=[],
        inventory_items=[],
        work_orders=[],
        assurance_findings=[],
        process_bottlenecks=[],
    )

    prioritized = PrioritizationEngine.prioritize_risks(findings)
    assert len(prioritized) == 2
    assert prioritized[0].entity_id == "S-CRIT"
    assert prioritized[0].priority_score > prioritized[1].priority_score


def test_risk_propagation_via_context_graph() -> None:
    """Test graph-guided downstream risk consequence traversal."""
    edges = [
        {"source_node_id": "SUPPLIER:S-1", "target_node_id": "PRODUCT:SKU-1"},
        {"source_node_id": "PRODUCT:SKU-1", "target_node_id": "ORDER:ORD-100"},
    ]
    nodes = {
        "PRODUCT:SKU-1": {"entity_type": "PRODUCT", "name": "Coil Wire", "attributes": {"total_amount": 0.0}},
        "ORDER:ORD-100": {"entity_type": "ORDER", "name": "Order #100", "attributes": {"total_amount": 75000.0}},
    }

    res = RiskPropagationEngine.propagate_risk("SUPPLIER:S-1", edges, nodes, max_hops=3)
    assert res["total_downstream_entities_affected"] == 2
    assert res["total_revenue_exposed_usd"] == 75000.0


def test_causal_evidence_classification() -> None:
    """Test mathematical causal evidence classification vs correlation."""
    tenant = "tenant-causal-01"

    # Fully controlled causal link
    c1 = CausalEngine.evaluate_relationship(
        tenant_id=tenant,
        cause_entity_id="SUPPLIER:S-1",
        effect_entity_id="OTIF_DECLINE",
        has_temporal_precedence=True,
        correlation_coefficient=0.88,
        has_controlled_confounders=True,
    )
    assert c1.relationship_classification == CausalClassification.CAUSAL
    assert c1.confidence_score >= 0.90

    # Uncontrolled correlation
    c2 = CausalEngine.evaluate_relationship(
        tenant_id=tenant,
        cause_entity_id="RAIN_EVENT",
        effect_entity_id="REVENUE_DROP",
        has_temporal_precedence=False,
        correlation_coefficient=0.70,
        has_controlled_confounders=False,
    )
    assert c2.relationship_classification == CausalClassification.CORRELATED
    assert "SEASONALITY" in c2.known_confounders


def test_external_signal_ingestion_and_mapping() -> None:
    """Test external signal normalization and tenant entity binding."""
    tenant = "tenant-ext-01"

    sig = DomainSignalProcessors.process_port_congestion_feed("SGSIN", 85.0)
    assert sig.signal_type == SignalType.PORT_CONGESTION
    assert sig.severity == RiskSeverity.CRITICAL

    suppliers = [{"id": "S-SG", "country": "SINGAPORE"}]
    shipments = [{"id": "SHP-1", "carrier": "MAERSK"}]

    mappings = SignalMappingEngine.map_signals_to_entities(tenant, [sig], suppliers, shipments)
    assert len(mappings) >= 1
    assert mappings[0].entity_id in ("S-SG", "SHP-1")


def test_opportunity_detection_and_ranking() -> None:
    """Test working capital release and early-payment discount discovery."""
    tenant = "tenant-opp-01"

    inv_items = [{"sku_id": "SKU-EXCESS", "on_hand": 100.0, "safety_stock": 20.0, "unit_cost": 150.0}]
    invoices = [{"id": "INV-100", "total_amount": 50000.0}]

    opps = OpportunityEngine.detect_opportunities(tenant, [], inv_items, invoices)
    assert len(opps) == 2
    # Working capital release: (100 - 40) * 150 = 9000.0
    # Early payment discount: 50000 * 0.02 = 1000.0
    assert opps[0].potential_value_usd == 9000.0


def test_master_risk_orchestrator_sweep() -> None:
    """Test master RiskOrchestrator coordination sweep and coverage assessment."""
    tenant = "tenant-risk-master"

    suppliers = [{"id": "S-1", "otif_rate": 70.0, "annual_spend": 100000.0}]
    customers = [{"id": "C-1", "health_score": 80.0, "period_revenue": 50000.0}]
    inventory = [{"sku_id": "SKU-1", "on_hand": 50.0, "safety_stock": 10.0, "unit_cost": 40.0}]
    wos = [{"id": "WO-1", "status": "IN_PROGRESS", "target_quantity": 100.0}]

    summary = RiskOrchestrator.run_risk_sweep(
        tenant_id=tenant,
        suppliers=suppliers,
        customers=customers,
        inventory_items=inventory,
        work_orders=wos,
        invoices=[],
        assurance_findings=[],
        process_bottlenecks=[],
    )

    assert summary.total_active_risks_count >= 1
    assert summary.total_exposure_usd > 0
    assert summary.overall_risk_coverage_pct > 0
