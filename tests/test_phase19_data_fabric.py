"""
AURIX Enterprise Data Fabric — Phase 19 Master Test Suite
Validates normalization, entity resolution, checkpointing, idempotency,
retry classification, quarantine isolation, drift detection, freshness,
source authority, backend aggregations, and runtime streaming.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest

from aurix_core.data_fabric.aggregations import DataFabricAggregator
from aurix_core.data_fabric.checkpointing import CheckpointManager
from aurix_core.data_fabric.contracts import (
    CanonicalEntityType,
    DataFreshnessState,
    DriftType,
    ResolutionStatus,
    SourceRecordEnvelope,
    SyncStatus,
)
from aurix_core.data_fabric.entity_resolution import EntityResolutionEngine
from aurix_core.data_fabric.freshness import FreshnessEngine
from aurix_core.data_fabric.idempotency import IdempotencyEngine
from aurix_core.data_fabric.normalization import DataNormalizer
from aurix_core.data_fabric.quarantine import QuarantineManager
from aurix_core.data_fabric.retry_policy import RetryPolicyEngine
from aurix_core.data_fabric.schema_drift import SchemaDriftDetector
from aurix_core.data_fabric.source_authority import SourceAuthorityMatrix
from aurix_core.integrations.runtime import ConnectorRuntime


def test_normalization_engine() -> None:
    """Test standard date, currency, unit, and identifier normalization."""
    # Timestamp parsing
    dt = DataNormalizer.normalize_timestamp("2026-08-22T02:30:00Z")
    assert dt is not None
    assert dt.year == 2026

    # Currency amount parsing
    amt, curr = DataNormalizer.normalize_currency_amount(" $1,450.75 ")
    assert amt == Decimal("1450.75")
    assert curr == "USD"

    # Unit conversion
    kg_in_lb = DataNormalizer.normalize_unit(10.0, "kg", "lb")
    assert round(kg_in_lb, 2) == 22.05

    # Full Envelope processing
    src_env = SourceRecordEnvelope(
        tenant_id="tenant-aurix-1",
        source_system="Tally",
        source_entity_type="invoice",
        source_record_id="INV-9901",
        payload={
            "invoice_id": "inv-9901",
            "invoice_date": "2026-08-20",
            "total_amount": "₹ 50,000.00",
            "customer_name": "Acme Industries Ltd",
        },
    )

    norm_env = DataNormalizer.process_envelope(
        envelope=src_env,
        canonical_type=CanonicalEntityType.INVOICE,
        canonical_id="CAN-INV-001",
    )

    assert norm_env.canonical_id == "CAN-INV-001"
    assert norm_env.normalized_data["invoice_id"] == "INV-9901"
    assert norm_env.normalized_data["total_amount"] == 50000.0
    assert norm_env.normalized_data["currency"] == "INR"
    assert norm_env.source_data_snapshot["customer_name"] == "Acme Industries Ltd"


def test_entity_resolution_flow() -> None:
    """Test exact, fuzzy, and alias entity resolution with confidence scoring."""
    engine = EntityResolutionEngine()
    tenant = "tenant-prod-1"

    # 1. First time encounter: Creates new canonical ID
    d1 = engine.resolve(
        tenant_id=tenant,
        entity_type=CanonicalEntityType.SUPPLIER,
        source_system="Tally",
        source_id="SUPP-001",
        candidate_name="Tata Steel Limited",
    )
    assert d1.is_new_entity is True
    assert d1.confidence_score == 1.0
    canonical_id = d1.canonical_id

    # 2. Subsequent encounter from another system with clean name match: Resolves
    d2 = engine.resolve(
        tenant_id=tenant,
        entity_type=CanonicalEntityType.SUPPLIER,
        source_system="Odoo",
        source_id="PARTNER-889",
        candidate_name="Tata Steel Ltd.",
    )
    assert d2.canonical_id == canonical_id
    assert d2.status in (ResolutionStatus.RESOLVED_EXACT, ResolutionStatus.RESOLVED_FUZZY)
    assert d2.confidence_score >= 0.85

    # 3. Re-encounter using registered alias: Exact instant match
    d3 = engine.resolve(
        tenant_id=tenant,
        entity_type=CanonicalEntityType.SUPPLIER,
        source_system="Odoo",
        source_id="PARTNER-889",
    )
    assert d3.canonical_id == canonical_id
    assert d3.status == ResolutionStatus.RESOLVED_ALIAS
    assert d3.confidence_score == 1.0


def test_checkpointing_and_idempotency() -> None:
    """Test checkpoint watermarking and duplicate payload suppression."""
    cp_mgr = CheckpointManager()
    idemp = IdempotencyEngine()
    tenant = "t-alpha"

    # Commit checkpoint
    cp = cp_mgr.commit_checkpoint(
        tenant_id=tenant,
        connector_id="conn-odoo",
        stream_name="orders",
        rows_processed=25,
    )
    assert cp.rows_synced_total == 25
    assert cp.last_successful_sync_at is not None

    # Idempotency hash verification
    key1 = idemp.generate_idempotency_key(tenant, "Odoo", "ORD-101", payload={"total": 500})
    assert idemp.is_duplicate(key1) is False
    idemp.register(key1)
    assert idemp.is_duplicate(key1) is True


def test_retry_policy_and_quarantine() -> None:
    """Test retry backoff calculation and quarantine defect recording."""
    # Test permanent error
    auth_err = Exception("401 Unauthorized token expired")
    dec_auth = RetryPolicyEngine.evaluate(auth_err, attempt=1)
    assert dec_auth.should_retry is False
    assert dec_auth.is_permanent is True

    # Test transient error
    net_err = Exception("503 Service Unavailable Connection Timeout")
    dec_net = RetryPolicyEngine.evaluate(net_err, attempt=1)
    assert dec_net.should_retry is True
    assert dec_net.delay_seconds > 0.0

    # Quarantine manager
    q_mgr = QuarantineManager()
    q_rec = q_mgr.quarantine_record(
        tenant_id="t-1",
        source_system="SFTP",
        source_entity="inventory.csv",
        raw_payload={"sku": "", "qty": "INVALID"},
        failure_stage="VALIDATION",
        failure_reason="Invalid numeric quantity",
        error_code="PARSE_ERR",
    )
    assert q_rec.quarantine_id is not None
    listed = q_mgr.list_quarantined("t-1", resolved=False)
    assert len(listed) == 1


def test_schema_drift_detector() -> None:
    """Test detection of added, removed, and type-altered columns."""
    baseline_records = [
        {"order_id": "O1", "amount": 100.50, "status": "OPEN"},
        {"order_id": "O2", "amount": 250.00, "status": "SHIPPED"},
    ]
    fingerprint = SchemaDriftDetector.generate_fingerprint(baseline_records)

    mutated_records = [
        {"order_id": "O3", "amount": "INVALID_STR", "status": "OPEN", "discount_code": "PROMO20"},
    ]
    drifts = SchemaDriftDetector.compare_schemas(fingerprint, mutated_records)
    drift_types = {d.drift_type for d in drifts}

    assert DriftType.FIELD_ADDED in drift_types
    assert DriftType.TYPE_CHANGED in drift_types


def test_freshness_engine() -> None:
    """Test dynamic SLA data freshness report generation."""
    cp_mgr = CheckpointManager()
    now = datetime.now(timezone.utc)

    # 1. Fresh Live Checkpoint
    cp_live = cp_mgr.commit_checkpoint("t-1", "conn-1", "sales", rows_processed=10)
    rep_live = FreshnessEngine.calculate_freshness(cp_live, sla_seconds=3600)
    assert rep_live.state == DataFreshnessState.LIVE
    assert rep_live.is_within_sla is True

    # 2. Stale Checkpoint
    cp_stale = cp_mgr.commit_checkpoint("t-1", "conn-2", "inventory", rows_processed=5)
    cp_stale.last_successful_sync_at = now - timedelta(hours=10)
    rep_stale = FreshnessEngine.calculate_freshness(cp_stale, sla_seconds=3600)
    assert rep_stale.state == DataFreshnessState.STALE
    assert rep_stale.is_within_sla is False


def test_source_authority_matrix() -> None:
    """Test domain-level multi-source conflict resolution."""
    matrix = SourceAuthorityMatrix()

    # WMS (rank 0) beats ERP (rank 1) for physical inventory quantity
    resolved_qty, conflict = matrix.resolve_attribute_conflict(
        tenant_id="t-1",
        entity_type=CanonicalEntityType.INVENTORY_POSITION,
        entity_id="SKU-STEEL-001",
        attribute_name="quantity",
        source_a="WMS",
        value_a=1214,
        source_b="SAP",
        value_b=1240,
    )
    assert resolved_qty == 1214
    assert conflict.winning_source == "WMS"


def test_backend_aggregations() -> None:
    """Test performant backend inventory and order aggregations."""
    positions = [
        {"sku": "SKU-A", "quantity": 100, "unit_cost": 15.0, "warehouse_id": "WH-1"},
        {"sku": "SKU-B", "quantity": 5, "unit_cost": 50.0, "warehouse_id": "WH-1"},
        {"sku": "SKU-C", "quantity": 200, "unit_cost": 2.5, "warehouse_id": "WH-2"},
    ]
    inv_summary = DataFabricAggregator.aggregate_inventory_positions(positions, safety_stock_threshold=10.0)
    assert inv_summary.total_skus == 3
    assert inv_summary.total_on_hand_units == 305.0
    assert inv_summary.total_inventory_valuation == 2250.0
    assert inv_summary.total_locations == 2
    assert inv_summary.low_stock_sku_count == 1


def test_end_to_end_connector_runtime() -> None:
    """Test complete stream ingestion lifecycle through ConnectorRuntime."""
    runtime = ConnectorRuntime()
    tenant = "tenant-e2e"

    raw_batch = [
        {"id": "ORD-1", "order_date": "2026-08-21", "total": "$1,200.00", "client": "Global Logistics"},
        {"id": "ORD-2", "order_date": "2026-08-22", "total": "$850.50", "client": "Apex Retail"},
        {"id": "", "order_date": "2026-08-22", "total": "$300.00"},  # Corrupted row (missing ID)
    ]

    records, summary = runtime.process_stream(
        tenant_id=tenant,
        connector_id="conn-rest-1",
        source_system="GenericREST",
        stream_name="orders",
        canonical_type=CanonicalEntityType.ORDER,
        raw_records=raw_batch,
        id_field="id",
        name_field="client",
    )

    assert len(records) == 2
    assert summary.rows_received == 3
    assert summary.rows_accepted == 2
    assert summary.rows_quarantined == 1
    assert summary.status == SyncStatus.PARTIAL_SUCCESS

    # Re-running same batch triggers duplicate suppression
    records_dup, summary_dup = runtime.process_stream(
        tenant_id=tenant,
        connector_id="conn-rest-1",
        source_system="GenericREST",
        stream_name="orders",
        canonical_type=CanonicalEntityType.ORDER,
        raw_records=raw_batch,
        id_field="id",
    )

    assert len(records_dup) == 0
    assert summary_dup.rows_deduplicated == 2
    assert summary_dup.rows_quarantined == 1
