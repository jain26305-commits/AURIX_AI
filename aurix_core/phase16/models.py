"""Persistent Phase 16 planning, execution, collaboration, and audit models.

These models deliberately reference canonical Phase 1-15 entities by identifier
rather than duplicating those master-data models.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import DateTime, Index, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from aurix_core.database.engine import Base
from aurix_core.database.models.base import TenantMixin


def _json_type() -> JSON:
    """Use JSONB on PostgreSQL while remaining portable to SQLite."""
    return JSON().with_variant(postgresql.JSONB(), "postgresql")


JSON_TYPE = _json_type()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PurchaseOrderModel(Base, TenantMixin):
    __tablename__ = "purchase_orders"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    supplier_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT", index=True)
    required_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source_request_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    total_amount: Mapped[Optional[float]] = mapped_column(
        Numeric(precision=14, scale=2, asdecimal=False), nullable=True
    )
    currency: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    supplier_reference: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    committed_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        Index("ix_phase16_po_tenant_supplier_status", "tenant_id", "supplier_id", "status"),
    )


class PurchaseOrderLineModel(Base, TenantMixin):
    __tablename__ = "purchase_order_lines"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    purchase_order_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    sku_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Numeric(precision=14, scale=4, asdecimal=False), nullable=False)
    received_quantity: Mapped[float] = mapped_column(
        Numeric(precision=14, scale=4, asdecimal=False), nullable=False, default=0.0
    )
    accepted_quantity: Mapped[float] = mapped_column(
        Numeric(precision=14, scale=4, asdecimal=False), nullable=False, default=0.0
    )
    rejected_quantity: Mapped[float] = mapped_column(
        Numeric(precision=14, scale=4, asdecimal=False), nullable=False, default=0.0
    )
    unit_price: Mapped[Optional[float]] = mapped_column(
        Numeric(precision=14, scale=4, asdecimal=False), nullable=True
    )
    currency: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        Index("ix_phase16_po_line_tenant_po_sku", "tenant_id", "purchase_order_id", "sku_id"),
    )


class PurchaseOrderRevisionModel(Base, TenantMixin):
    __tablename__ = "purchase_order_revisions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    purchase_order_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        UniqueConstraint("tenant_id", "purchase_order_id", "revision", name="uq_phase16_po_revision"),
    )


class SupplierCommitmentModel(Base, TenantMixin):
    __tablename__ = "supplier_commitments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    purchase_order_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    committed_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    committed_quantity: Mapped[Optional[float]] = mapped_column(
        Numeric(precision=14, scale=4, asdecimal=False), nullable=True
    )
    alternative_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    supplier_reference: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class AdvanceShipmentNoticeModel(Base, TenantMixin):
    __tablename__ = "advance_shipment_notices"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    purchase_order_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="RECEIVED")
    expected_arrival_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    carrier: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class AdvanceShipmentNoticeLineModel(Base, TenantMixin):
    __tablename__ = "advance_shipment_notice_lines"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    asn_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    purchase_order_line_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    shipped_quantity: Mapped[float] = mapped_column(Numeric(precision=14, scale=4, asdecimal=False), nullable=False)


class GoodsReceiptModel(Base, TenantMixin):
    __tablename__ = "goods_receipts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    purchase_order_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="RECEIVED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class GoodsReceiptLineModel(Base, TenantMixin):
    __tablename__ = "goods_receipt_lines"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    goods_receipt_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    purchase_order_line_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    received_quantity: Mapped[float] = mapped_column(Numeric(precision=14, scale=4, asdecimal=False), nullable=False)
    accepted_quantity: Mapped[float] = mapped_column(Numeric(precision=14, scale=4, asdecimal=False), nullable=False)
    rejected_quantity: Mapped[float] = mapped_column(Numeric(precision=14, scale=4, asdecimal=False), nullable=False)


class SupplierFinancialDocumentModel(Base, TenantMixin):
    __tablename__ = "supplier_financial_documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    purchase_order_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(32), nullable=False)
    document_number: Mapped[str] = mapped_column(String(128), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(precision=14, scale=2, asdecimal=False), nullable=False)
    currency: Mapped[str] = mapped_column(String(16), nullable=False)
    matched_receipt_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    reference_document_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    match_status: Mapped[str] = mapped_column(String(32), nullable=False, default="UNMATCHED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        UniqueConstraint("tenant_id", "document_number", name="uq_phase16_financial_document_number"),
    )


class SupplierFinancialDocumentLineModel(Base, TenantMixin):
    __tablename__ = "supplier_financial_document_lines"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    financial_document_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    purchase_order_line_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Numeric(precision=14, scale=4, asdecimal=False), nullable=False)
    unit_price: Mapped[Optional[float]] = mapped_column(Numeric(precision=14, scale=4, asdecimal=False), nullable=True)
    tax_amount: Mapped[float] = mapped_column(Numeric(precision=14, scale=2, asdecimal=False), nullable=False, default=0.0)
    freight_amount: Mapped[float] = mapped_column(Numeric(precision=14, scale=2, asdecimal=False), nullable=False, default=0.0)


class Phase16IdempotencyKeyModel(Base, TenantMixin):
    __tablename__ = "phase16_idempotency_keys"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    operation: Mapped[str] = mapped_column(String(128), nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False)
    external_record_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="IN_PROGRESS")
    result_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON_TYPE, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source_identity: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_phase16_idempotency_tenant_key"),
        Index("uq_phase16_idempotency_source_identity", "tenant_id", "source_identity", unique=True),
        Index("ix_phase16_idempotency_operation", "tenant_id", "operation"),
    )


class ReturnRequestModel(Base, TenantMixin):
    __tablename__ = "return_requests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_order_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    sku_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Numeric(precision=14, scale=4, asdecimal=False), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="REQUESTED", index=True)
    disposition: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    recovery_value: Mapped[Optional[float]] = mapped_column(Numeric(precision=14, scale=2, asdecimal=False), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class BOMHeaderModel(Base, TenantMixin):
    __tablename__ = "bom_headers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    parent_sku_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        Index("ix_phase16_bom_active_effective", "tenant_id", "parent_sku_id", "effective_from"),
    )


class BOMLineModel(Base, TenantMixin):
    __tablename__ = "bom_lines"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    bom_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    component_sku_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    quantity_per: Mapped[float] = mapped_column(Numeric(precision=14, scale=4, asdecimal=False), nullable=False)
    scrap_pct: Mapped[float] = mapped_column(Numeric(precision=6, scale=4, asdecimal=False), nullable=False, default=0.0)


class MRPRunModel(Base, TenantMixin):
    __tablename__ = "mrp_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="COMPLETED")
    requirements_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON_TYPE, nullable=False)
    results_json: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class CapacityCheckModel(Base, TenantMixin):
    __tablename__ = "capacity_checks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="COMPUTED")
    results_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON_TYPE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class SalesOrderModel(Base, TenantMixin):
    __tablename__ = "sales_orders"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="OPEN", index=True)
    requested_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class SalesOrderLineModel(Base, TenantMixin):
    __tablename__ = "sales_order_lines"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    sales_order_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    sku_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Numeric(precision=14, scale=4, asdecimal=False), nullable=False)
    allocated_quantity: Mapped[float] = mapped_column(Numeric(precision=14, scale=4, asdecimal=False), nullable=False, default=0.0)
    location_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class FulfillmentAllocationModel(Base, TenantMixin):
    __tablename__ = "fulfillment_allocations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    sales_order_line_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    sku_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Numeric(precision=14, scale=4, asdecimal=False), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="RESERVED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class Phase16ScenarioModel(Base, TenantMixin):
    __tablename__ = "phase16_scenarios"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scenario_type: Mapped[str] = mapped_column(String(64), nullable=False)
    parameters_json: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, nullable=False)
    result_json: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class Phase16ScenarioComparisonModel(Base, TenantMixin):
    __tablename__ = "phase16_scenario_comparisons"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scenario_ids_json: Mapped[list[str]] = mapped_column(JSON_TYPE, nullable=False)
    comparison_json: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, nullable=False)
    recommended_scenario_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class Phase16CaseModel(Base, TenantMixin):
    __tablename__ = "phase16_cases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="MEDIUM")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="OPEN")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    impact_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON_TYPE, nullable=True)
    recommended_action_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON_TYPE, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    owner: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    priority: Mapped[str] = mapped_column(String(32), nullable=False, default="NORMAL")
    sla_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON_TYPE, nullable=True)


class Phase16DecisionRecordModel(Base, TenantMixin):
    __tablename__ = "phase16_decision_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    answer_source: Mapped[str] = mapped_column(String(64), nullable=False)
    ai_provider: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    model_used: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    fact_pack_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    tool_calls_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON_TYPE, nullable=False)
    recommendation_json: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, nullable=False)
    provenance_json: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, nullable=False)
    outcome_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON_TYPE, nullable=True)
    expected_outcome_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON_TYPE, nullable=True)
    actual_outcome_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON_TYPE, nullable=True)
    approval_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    action_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    value_realized: Mapped[Optional[float]] = mapped_column(Numeric(precision=14, scale=2, asdecimal=False), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PROPOSED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
