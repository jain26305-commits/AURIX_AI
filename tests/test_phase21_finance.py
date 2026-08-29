"""
AURIX Business Finance Intelligence — Phase 21 Master Test Suite
Validates P&L, Gross/Contribution Margins, Customer/SKU Profitability,
AR/AP Aging, Working Capital, CCC Decomposition, and Anomaly Detection.
"""

from datetime import datetime, timedelta, timezone
import pytest

from aurix_core.finance.anomaly_engine import FinancialAnomalyEngine
from aurix_core.finance.ap_engine import APEngine
from aurix_core.finance.ar_engine import AREngine
from aurix_core.finance.config import FinanceConfigManager, TenantFinanceConfig
from aurix_core.finance.contracts import DataAvailabilityStatus
from aurix_core.finance.margin_engine import MarginEngine
from aurix_core.finance.orchestrator import FinanceOrchestrator
from aurix_core.finance.profitability_engine import ProfitabilityEngine
from aurix_core.finance.reconciliation_engine import FinanceReconciliationEngine
from aurix_core.finance.revenue_engine import RevenueEngine
from aurix_core.finance.working_capital_engine import WorkingCapitalEngine


def test_revenue_and_margin_integrity() -> None:
    """Test Gross-to-Net revenue deductions and Gross/Contribution margin formulas."""
    tenant = "tenant-fin-01"

    orders = [
        {"id": "ORD-1", "total_amount": 1000.0, "discount_amount": 50.0, "customer_id": "CUST-A", "sku_id": "SKU-1"},
        {"id": "ORD-2", "total_amount": 2000.0, "discount_amount": 100.0, "customer_id": "CUST-B", "sku_id": "SKU-2"},
    ]
    returns = [{"recovery_value": 200.0}]

    rev = RevenueEngine.calculate_revenue(tenant, orders, returns=returns)
    assert rev.gross_revenue == 3000.0
    # Net = 3000 - 200 (returns) - 150 (discounts) = 2650.0
    assert rev.net_revenue == 2650.0

    # Margin with Variable Costs
    margin_with_vc = MarginEngine.calculate_margin(tenant, net_revenue=2650.0, cogs=1500.0, variable_costs=150.0)
    assert margin_with_vc.gross_profit == 1150.0
    assert margin_with_vc.gross_margin_pct == 43.40
    assert margin_with_vc.contribution_margin == 1000.0
    assert margin_with_vc.margin_status == DataAvailabilityStatus.AVAILABLE

    # Margin without Variable Costs (Zero-Fabrication Guard)
    margin_no_vc = MarginEngine.calculate_margin(tenant, net_revenue=2650.0, cogs=1500.0, variable_costs=None)
    assert margin_no_vc.contribution_margin is None
    assert margin_no_vc.margin_status == DataAvailabilityStatus.PARTIALLY_AVAILABLE


def test_customer_and_sku_profitability() -> None:
    """Test multi-tier customer and SKU margin ranking."""
    customers = [
        {"id": "CUST-1", "customer_name": "Apex Corp"},
        {"id": "CUST-2", "customer_name": "Bad Debt Ltd"},
    ]
    invoices = [
        {"entity_id": "CUST-1", "total_amount": 10000.0, "discount_amount": 0.0, "variable_cost_amount": 500.0},
        {"entity_id": "CUST-2", "total_amount": 2000.0, "discount_amount": 200.0, "variable_cost_amount": 100.0},
    ]
    cogs_map = {"CUST-1": 5000.0, "CUST-2": 1900.0}

    cust_prof = ProfitabilityEngine.evaluate_customer_profitability(customers, invoices, cogs_map)
    assert len(cust_prof) == 2
    assert cust_prof[0].customer_id == "CUST-1"
    assert cust_prof[0].contribution_margin == 4500.0  # 10000 - 5000 - 500
    assert cust_prof[0].profitability_tier == "HIGH_VALUE"


def test_ar_ap_aging_and_working_capital() -> None:
    """Test AR/AP aging buckets, DSO, DPO, Working Capital, and CCC."""
    tenant = "tenant-wc-01"
    now = datetime.now(timezone.utc)

    # Invoices for AR and AP
    invoices = [
        {"invoice_type": "ACCOUNTS_RECEIVABLE", "total_amount": 50000.0, "due_date": now - timedelta(days=15), "status": "OPEN", "entity_id": "CUST-1"},
        {"invoice_type": "ACCOUNTS_RECEIVABLE", "total_amount": 250000.0, "due_date": now + timedelta(days=15), "status": "OPEN", "entity_id": "CUST-2"},
        {"invoice_type": "ACCOUNTS_PAYABLE", "total_amount": 120000.0, "due_date": now + timedelta(days=20), "status": "OPEN", "entity_id": "SUPP-1"},
    ]

    ar = AREngine.calculate_ar_aging(tenant, invoices, annual_revenue=1200000.0)
    assert ar.total_receivables == 300000.0
    assert ar.total_overdue == 50000.0
    assert ar.dso_days == 91.2  # (300,000 / 1,200,000) * 365

    ap = APEngine.calculate_ap_aging(tenant, invoices, annual_cogs=720000.0)
    assert ap.total_payables == 120000.0
    assert ap.dpo_days == 60.8  # (120,000 / 720,000) * 365

    wc = WorkingCapitalEngine.calculate_working_capital(
        tenant_id=tenant,
        inventory_valuation=200000.0,
        accounts_receivable=ar.total_receivables,
        accounts_payable=ap.total_payables,
        annual_revenue=1200000.0,
        annual_cogs=720000.0,
    )
    assert wc.operating_working_capital == 380000.0  # 200,000 + 300,000 - 120,000
    assert wc.dio_days == 101.4  # (200,000 / 720,000) * 365
    # CCC = DSO (91.2) + DIO (101.4) - DPO (60.8) = 131.8
    assert wc.cash_conversion_cycle_days == 131.8


def test_financial_anomaly_detection() -> None:
    """Test statistical invoice spike outlier detection."""
    tenant = "tenant-anom-01"

    # Series of normal invoices around 1,000 with one 25,000 spike
    invoices = [{"total_amount": 1000.0, "invoice_number": f"INV-{i}"} for i in range(10)]
    invoices.append({"total_amount": 25000.0, "invoice_number": "INV-SPIKE"})

    anomalies = FinancialAnomalyEngine.audit_transactions(tenant, invoices, z_threshold=2.0)
    assert len(anomalies) >= 1
    assert anomalies[0].entity_id == "INV-SPIKE"
    assert anomalies[0].detected_metric_value == 25000.0


def test_master_finance_orchestrator_sweep() -> None:
    """Test master FinanceOrchestrator summary generation."""
    tenant = "tenant-master-fin"
    now = datetime.now(timezone.utc)

    orders = [
        {"id": "O-1", "total_amount": 10000.0, "quantity": 100, "sku_id": "SKU-A"},
    ]
    invoices = [
        {"id": "INV-1", "invoice_type": "ACCOUNTS_RECEIVABLE", "total_amount": 10000.0, "due_date": now + timedelta(days=10)},
    ]
    payments = [
        {"amount": 10000.0, "payment_type": "INBOUND"},
    ]
    products = [
        {"id": "SKU-A", "unit_cost": 40.0},
    ]
    inventory = [
        {"sku_id": "SKU-A", "on_hand": 50.0},
    ]

    summary = FinanceOrchestrator.run_financial_analysis(
        tenant_id=tenant,
        orders=orders,
        invoices=invoices,
        payments=payments,
        products=products,
        inventory_positions=inventory,
    )

    assert summary.gross_revenue == 10000.0
    assert summary.net_revenue == 10000.0
    assert summary.cogs == 4000.0
    assert summary.gross_profit == 6000.0
    assert summary.gross_margin_pct == 60.0
    assert summary.operating_working_capital > 0
