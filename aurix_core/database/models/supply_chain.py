"""Canonical supply chain database models for AURIX Enterprise Platform."""

from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from aurix_core.database.engine import Base
from aurix_core.database.models.base import TenantMixin


class Location(Base, TenantMixin):
    """Canonical representation of a supply chain node (facility, DC, store, warehouse)."""

    __tablename__ = "locations"

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

    id = Column(String(64), primary_key=True, index=True)
    supplier_name = Column(String(255), nullable=False)
    country = Column(String(64), nullable=True)
    lead_time_days = Column(Float, nullable=True)

    ingestion_run_id = Column(String(64), nullable=True, index=True)
    source_record_id = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class InventoryPosition(Base, TenantMixin):
    """Canonical representation of SKU-Location inventory balance state."""

    __tablename__ = "inventory_positions"

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