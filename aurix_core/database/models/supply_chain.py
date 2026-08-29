"""Canonical supply chain and enterprise data fabric database models for AURIX Enterprise Platform."""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from aurix_core.database.engine import Base
from aurix_core.database.models.base import TenantMixin

# Reuse existing canonical Purchase Order models from Phase 16
from aurix_core.phase16.models import (
    PurchaseOrderModel as PurchaseOrder,
    PurchaseOrderLineModel as PurchaseOrderLine,
)


class Location(Base, TenantMixin):
    """Canonical representation of a supply chain node (facility, DC, store, warehouse, plant)."""

    __tablename__ = "locations"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    location_name = Column(String(255), nullable=False)
    location_type = Column(String(64), nullable=False, default="WAREHOUSE")
    country = Column(String(64), nullable=True)

    ingestion_run_id = Column(String(64), nullable=True, index=True)
    source_record_id = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Product(Base, TenantMixin):
    """Canonical representation of an item, SKU, or product entity."""

    __tablename__ = "products"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    sku_code = Column(String(128), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(128), nullable=True)
    unit_cost = Column(Float, nullable=True)

    ingestion_run_id = Column(String(64), nullable=True, index=True)
    source_record_id = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Supplier(Base, TenantMixin):
    """Canonical representation of a vendor or supplier entity."""

    __tablename__ = "suppliers"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    supplier_name = Column(String(255), nullable=False)
    country = Column(String(64), nullable=True)
    lead_time_days = Column(Float, nullable=True)

    ingestion_run_id = Column(String(64), nullable=True, index=True)
    source_record_id = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Customer(Base, TenantMixin):
    """Canonical representation of a commercial buyer or client account."""

    __tablename__ = "customers"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    customer_name = Column(String(255), nullable=False)
    customer_tier = Column(String(64), nullable=True, default="STANDARD")
    segment = Column(String(64), nullable=True, default="SMB")
    account_status = Column(String(32), nullable=False, default="ACTIVE")
    assigned_rep_id = Column(String(64), nullable=True)
    country = Column(String(64), nullable=True)
    credit_limit = Column(Float, nullable=True)

    ingestion_run_id = Column(String(64), nullable=True, index=True)
    source_record_id = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class InventoryPosition(Base, TenantMixin):
    """Canonical representation of SKU-Location inventory balance state."""

    __tablename__ = "inventory_positions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku_id = Column(String(64), ForeignKey("products.id"), nullable=False, index=True)
    location_id = Column(String(64), ForeignKey("locations.id"), nullable=False, index=True)
    on_hand = Column(Float, nullable=False, default=0.0)
    on_order = Column(Float, nullable=False, default=0.0)
    safety_stock = Column(Float, nullable=True)

    ingestion_run_id = Column(String(64), nullable=True, index=True)
    source_record_id = Column(String(128), nullable=True)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class InventoryTransaction(Base, TenantMixin):
    """Canonical log of physical inventory movements, adjustments, and receipts."""

    __tablename__ = "inventory_transactions"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    sku_id = Column(String(64), ForeignKey("products.id"), nullable=False, index=True)
    location_id = Column(String(64), ForeignKey("locations.id"), nullable=False, index=True)
    transaction_type = Column(String(64), nullable=False)
    quantity = Column(Float, nullable=False)
    reference_document = Column(String(128), nullable=True)

    ingestion_run_id = Column(String(64), nullable=True, index=True)
    source_record_id = Column(String(128), nullable=True)
    transaction_date = Column(DateTime, default=datetime.utcnow, nullable=False)


class Order(Base, TenantMixin):
    """Canonical representation of a sales order."""

    __tablename__ = "orders"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    order_number = Column(String(128), nullable=False, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=True, index=True)
    order_status = Column(String(64), nullable=False, default="OPEN")
    channel = Column(String(64), nullable=False, default="DIRECT")
    sales_rep_id = Column(String(64), nullable=True)
    total_amount = Column(Float, nullable=False, default=0.0)
    discount_amount = Column(Float, nullable=False, default=0.0)
    currency = Column(String(16), nullable=False, default="USD")
    order_date = Column(DateTime, nullable=False)
    promised_delivery_date = Column(DateTime, nullable=True)
    delivered_date = Column(DateTime, nullable=True)

    ingestion_run_id = Column(String(64), nullable=True, index=True)
    source_record_id = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class OrderLine(Base, TenantMixin):
    """Canonical line-item for sales orders."""

    __tablename__ = "order_lines"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    order_id = Column(String(64), ForeignKey("orders.id"), nullable=False, index=True)
    sku_id = Column(String(64), ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    discount_amount = Column(Float, nullable=False, default=0.0)
    sales_channel = Column(String(64), nullable=True, default="DIRECT")
    line_total = Column(Float, nullable=False)

    ingestion_run_id = Column(String(64), nullable=True, index=True)
    source_record_id = Column(String(128), nullable=True)


class Shipment(Base, TenantMixin):
    """Canonical logistics shipment and transit record."""

    __tablename__ = "shipments"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    shipment_number = Column(String(128), nullable=False, index=True)
    origin_location_id = Column(String(64), ForeignKey("locations.id"), nullable=False)
    destination_location_id = Column(String(64), ForeignKey("locations.id"), nullable=False)
    carrier = Column(String(128), nullable=True)
    status = Column(String(64), nullable=False, default="IN_TRANSIT")
    shipped_date = Column(DateTime, nullable=True)
    estimated_arrival_date = Column(DateTime, nullable=True)
    actual_arrival_date = Column(DateTime, nullable=True)

    ingestion_run_id = Column(String(64), nullable=True, index=True)
    source_record_id = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Invoice(Base, TenantMixin):
    """Canonical commercial invoice."""

    __tablename__ = "invoices"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    invoice_number = Column(String(128), nullable=False, index=True)
    invoice_type = Column(String(64), nullable=False, default="ACCOUNTS_RECEIVABLE")
    entity_id = Column(String(64), nullable=False, index=True)
    total_amount = Column(Float, nullable=False)
    discount_amount = Column(Float, nullable=False, default=0.0)
    credit_note_amount = Column(Float, nullable=False, default=0.0)
    tax_amount = Column(Float, nullable=False, default=0.0)
    currency = Column(String(16), nullable=False, default="USD")
    status = Column(String(64), nullable=False, default="ISSUED")
    issue_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)

    ingestion_run_id = Column(String(64), nullable=True, index=True)
    source_record_id = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class InvoiceLine(Base, TenantMixin):
    """Canonical invoice line item."""

    __tablename__ = "invoice_lines"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    invoice_id = Column(String(64), ForeignKey("invoices.id"), nullable=False, index=True)
    sku_id = Column(String(64), ForeignKey("products.id"), nullable=True)
    description = Column(String(255), nullable=True)
    quantity = Column(Float, nullable=False, default=1.0)
    unit_price = Column(Float, nullable=False)
    discount_amount = Column(Float, nullable=False, default=0.0)
    variable_cost_amount = Column(Float, nullable=False, default=0.0)
    line_total = Column(Float, nullable=False)

    ingestion_run_id = Column(String(64), nullable=True, index=True)
    source_record_id = Column(String(128), nullable=True)


class Payment(Base, TenantMixin):
    """Canonical payment receipt or disbursement."""

    __tablename__ = "payments"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    payment_number = Column(String(128), nullable=False, index=True)
    invoice_id = Column(String(64), ForeignKey("invoices.id"), nullable=True, index=True)
    payment_type = Column(String(64), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(16), nullable=False, default="USD")
    payment_date = Column(DateTime, nullable=False)
    status = Column(String(64), nullable=False, default="COMPLETED")

    ingestion_run_id = Column(String(64), nullable=True, index=True)
    source_record_id = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Bom(Base, TenantMixin):
    """Canonical Bill of Materials hierarchy."""

    __tablename__ = "boms"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    parent_sku_id = Column(String(64), ForeignKey("products.id"), nullable=False, index=True)
    component_sku_id = Column(String(64), ForeignKey("products.id"), nullable=False, index=True)
    quantity_required = Column(Float, nullable=False, default=1.0)
    unit_of_measure = Column(String(32), nullable=False, default="PCS")
    scrap_factor = Column(Float, nullable=False, default=0.0)

    ingestion_run_id = Column(String(64), nullable=True, index=True)
    source_record_id = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class WorkOrder(Base, TenantMixin):
    """Canonical manufacturing production order."""

    __tablename__ = "work_orders"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    work_order_number = Column(String(128), nullable=False, index=True)
    sku_id = Column(String(64), ForeignKey("products.id"), nullable=False, index=True)
    plant_location_id = Column(String(64), ForeignKey("locations.id"), nullable=False)
    work_center_id = Column(String(64), nullable=True, index=True)
    target_quantity = Column(Float, nullable=False)
    completed_quantity = Column(Float, nullable=False, default=0.0)
    scrap_quantity = Column(Float, nullable=False, default=0.0)
    planned_run_time_minutes = Column(Float, nullable=True)
    actual_run_time_minutes = Column(Float, nullable=True)
    status = Column(String(64), nullable=False, default="SCHEDULED")
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    ingestion_run_id = Column(String(64), nullable=True, index=True)
    source_record_id = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ProductionEvent(Base, TenantMixin):
    """Canonical shop-floor manufacturing event log."""

    __tablename__ = "production_events"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    work_order_id = Column(String(64), ForeignKey("work_orders.id"), nullable=False, index=True)
    work_center_id = Column(String(64), nullable=True, index=True)
    machine_id = Column(String(64), nullable=True, index=True)
    event_type = Column(String(64), nullable=False)
    quantity = Column(Float, nullable=False, default=0.0)
    good_quantity = Column(Float, nullable=False, default=0.0)
    scrap_quantity = Column(Float, nullable=False, default=0.0)
    duration_minutes = Column(Float, nullable=True)
    reason_code = Column(String(64), nullable=True)
    event_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    ingestion_run_id = Column(String(64), nullable=True, index=True)
    source_record_id = Column(String(128), nullable=True)


class ReturnRecord(Base, TenantMixin):
    """Canonical reverse logistics return record."""

    __tablename__ = "returns"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    rma_number = Column(String(128), nullable=False, index=True)
    order_id = Column(String(64), ForeignKey("orders.id"), nullable=True, index=True)
    sku_id = Column(String(64), ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    disposition = Column(String(64), nullable=False, default="PENDING_INSPECTION")
    reason = Column(String(255), nullable=True)

    ingestion_run_id = Column(String(64), nullable=True, index=True)
    source_record_id = Column(String(128), nullable=True)
    return_date = Column(DateTime, default=datetime.utcnow, nullable=False)


class Contract(Base, TenantMixin):
    """Canonical vendor or customer commercial contract."""

    __tablename__ = "contracts"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    contract_number = Column(String(128), nullable=False, index=True)
    counterparty_id = Column(String(64), nullable=False, index=True)
    contract_type = Column(String(64), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    committed_value = Column(Float, nullable=True)
    terms = Column(Text, nullable=True)

    ingestion_run_id = Column(String(64), nullable=True, index=True)
    source_record_id = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PriceRecord(Base, TenantMixin):
    """Canonical price book and cost master."""

    __tablename__ = "prices"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    sku_id = Column(String(64), ForeignKey("products.id"), nullable=False, index=True)
    price_type = Column(String(64), nullable=False, default="BASE_LIST")
    amount = Column(Float, nullable=False)
    currency = Column(String(16), nullable=False, default="USD")
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime, nullable=True)

    ingestion_run_id = Column(String(64), nullable=True, index=True)
    source_record_id = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CustomerCredit(Base, TenantMixin):
    """Canonical customer credit ledger and balance evaluation."""

    __tablename__ = "customer_credits"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    credit_limit = Column(Float, nullable=False)
    outstanding_balance = Column(Float, nullable=False, default=0.0)
    risk_rating = Column(String(32), nullable=True, default="LOW")

    ingestion_run_id = Column(String(64), nullable=True, index=True)
    source_record_id = Column(String(128), nullable=True)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class SupplierPerformance(Base, TenantMixin):
    """Canonical vendor scorecard evaluation metrics."""

    __tablename__ = "supplier_performances"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    supplier_id = Column(String(64), ForeignKey("suppliers.id"), nullable=False, index=True)
    evaluation_period = Column(String(32), nullable=False)
    otif_rate = Column(Float, nullable=True)
    quality_yield_rate = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)

    ingestion_run_id = Column(String(64), nullable=True, index=True)
    source_record_id = Column(String(128), nullable=True)
    evaluated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
