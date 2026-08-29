"""
AURIX Enterprise Sales & Commercial Intelligence — Phase 22 Master Test Suite
Validates Account 360, Commercial OTIF, Price-Volume-Mix (PVM) Decomposition,
Discount Leakage, Product Velocity, and Commercial Anomalies.
"""

from datetime import datetime, timedelta, timezone
import pytest

from aurix_core.commercial.account_360 import Account360Engine
from aurix_core.commercial.anomaly_engine import CommercialAnomalyEngine
from aurix_core.commercial.channel_intelligence import ChannelIntelligenceEngine
from aurix_core.commercial.contracts import ParetoTier
from aurix_core.commercial.order_performance import OrderPerformanceEngine
from aurix_core.commercial.orchestrator import CommercialOrchestrator
from aurix_core.commercial.pricing_intelligence import PricingIntelligenceEngine
from aurix_core.commercial.product_velocity import ProductVelocityEngine


def test_account_360_and_pareto_tiering() -> None:
    """Test customer Pareto ABC 80-20 concentration and health scoring."""
    tenant = "tenant-comm-01"
    now = datetime.now(timezone.utc)

    customers = [
        {"id": "C-1", "customer_name": "Mega Retailer", "segment": "ENTERPRISE"},
        {"id": "C-2", "customer_name": "Mid-tier Store", "segment": "SMB"},
        {"id": "C-3", "customer_name": "Tail Buyer", "segment": "SMB"},
    ]
    orders = [
        {"customer_id": "C-1", "total_amount": 85000.0, "discount_amount": 1000.0, "order_date": now - timedelta(days=5)},
        {"customer_id": "C-2", "total_amount": 12000.0, "discount_amount": 200.0, "order_date": now - timedelta(days=20)},
        {"customer_id": "C-3", "total_amount": 3000.0, "discount_amount": 0.0, "order_date": now - timedelta(days=80)},  # Dormant
    ]

    accounts = Account360Engine.evaluate_accounts(tenant, customers, orders)
    assert len(accounts) == 3
    assert accounts[0].customer_id == "C-1"
    assert accounts[0].pareto_tier == ParetoTier.TIER_A
    assert accounts[0].health_score > 80.0

    assert accounts[2].customer_id == "C-3"
    assert accounts[2].pareto_tier == ParetoTier.TIER_C
    assert accounts[2].health_status.value in ("AT_RISK", "DORMANT")


def test_commercial_otif_performance() -> None:
    """Test On-Time In-Full from customer delivery perspective."""
    tenant = "tenant-otif-01"
    now = datetime.now(timezone.utc)

    orders = [
        {"order_status": "DELIVERED", "promised_delivery_date": now, "delivered_date": now - timedelta(days=1)},  # On time & Full
        {"order_status": "DELIVERED", "promised_delivery_date": now - timedelta(days=2), "delivered_date": now},  # Late
        {"order_status": "CANCELLED"},
    ]

    report = OrderPerformanceEngine.evaluate_order_performance(tenant, orders)
    assert report.total_orders == 3
    assert report.otif_orders == 1
    assert report.otif_rate_pct == 50.0  # 1 / 2 valid orders
    assert report.cancellation_rate_pct == 33.3


def test_price_volume_mix_decomposition() -> None:
    """Test deterministic Price-Volume-Mix (PVM) variance decomposition."""
    tenant = "tenant-pvm-01"

    # Baseline Period: 100 units @ $10 = $1,000
    baseline = [{"sku_id": "SKU-A", "quantity": 100, "unit_price": 10.0}]
    # Current Period: 120 units @ $12 = $1,440 (Total Change = +$440)
    # Price Effect = (12 - 10) * 120 = +$240
    # Volume Effect = (120 - 100) * 10 = +$200
    # Mix Effect = 440 - 240 - 200 = $0
    current = [{"sku_id": "SKU-A", "quantity": 120, "unit_price": 12.0}]

    pvm = PricingIntelligenceEngine.decompose_pvm(tenant, baseline, current)
    assert pvm.total_revenue_change == 440.0
    assert pvm.price_effect == 240.0
    assert pvm.volume_effect == 200.0
    assert pvm.mix_effect == 0.0


def test_discount_leakage_and_commercial_anomalies() -> None:
    """Test off-invoice discount leakage and anomaly generation."""
    tenant = "tenant-leakage-01"

    orders = [
        {"id": "O-1", "customer_id": "C-1", "total_amount": 10000.0, "discount_amount": 500.0},    # 5% (Authorized)
        {"id": "O-2", "customer_id": "C-2", "total_amount": 10000.0, "discount_amount": 2500.0},   # 25% (Rogue Discount Spike)
    ]

    leakage = PricingIntelligenceEngine.audit_discount_leakage(tenant, orders)
    assert leakage.leakage_count == 1
    assert leakage.unauthorized_discounts_total == 1500.0  # 2500 - 10% of 10000 (1000)

    anomalies = CommercialAnomalyEngine.audit_commercial_anomalies(tenant, orders)
    assert len(anomalies) == 1
    assert anomalies[0].entity_id == "O-2"
    assert anomalies[0].domain.value == "UNAUTHORIZED_DISCOUNT"


def test_master_commercial_orchestrator_sweep() -> None:
    """Test full master CommercialOrchestrator sweep."""
    tenant = "tenant-comm-master"
    now = datetime.now(timezone.utc)

    customers = [{"id": "C-A", "customer_name": "Alpha Corp"}]
    orders = [{"id": "ORD-1", "customer_id": "C-A", "total_amount": 5000.0, "discount_amount": 100.0, "channel": "DIRECT", "order_status": "DELIVERED", "order_date": now}]
    products = [{"id": "SKU-1", "name": "Item 1"}]
    order_lines = [{"order_id": "ORD-1", "sku_id": "SKU-1", "quantity": 10, "unit_price": 500.0}]

    summary = CommercialOrchestrator.run_commercial_sweep(
        tenant_id=tenant,
        customers=customers,
        orders=orders,
        products=products,
        order_lines=order_lines,
    )

    assert summary.gross_revenue == 5000.0
    assert summary.net_revenue == 4900.0
    assert summary.total_orders == 1
    assert summary.active_customers_count == 1
