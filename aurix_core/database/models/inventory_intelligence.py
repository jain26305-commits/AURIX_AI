"""Canonical database models for AURIX Phase 4 Inventory Intelligence."""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from aurix_core.database.engine import Base
from aurix_core.database.models.base import TenantMixin


class InventoryIntelligenceRun(Base, TenantMixin):
    """
    Persistent representation of an inventory intelligence execution run.
    Tracks idempotency, provenance, and linkages to upstream forecasting models.
    """

    __tablename__ = "inventory_intelligence_runs"

    id = Column(String(64), primary_key=True, index=True)
    forecast_run_id = Column(String(64), nullable=True, index=True)
    dataset_hash = Column(String(128), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="COMPLETED")

    # Serialized JSON configuration and provenance tracking
    configuration = Column(String, nullable=True)
    provenance = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ReplenishmentPolicy(Base, TenantMixin):
    """
    Canonical representation of computed inventory parameters and replenishment decisions.
    Preserves unconstrained values, applied constraints (MOQ/Pack Size), and risk states.
    """

    __tablename__ = "replenishment_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(
        String(64), ForeignKey("inventory_intelligence_runs.id"), nullable=False, index=True
    )

    sku_id = Column(String(64), nullable=False, index=True)
    location_id = Column(String(64), nullable=True, index=True)

    # Policy Parameters (Nullable to satisfy zero-fabrication rules)
    expected_daily_demand = Column(Float, nullable=True)
    lead_time_days = Column(Float, nullable=True)
    safety_stock = Column(Float, nullable=True)
    reorder_point = Column(Float, nullable=True)
    eoq = Column(Float, nullable=True)

    # Replenishment Decision & Inventory State Actions
    reorder_triggered = Column(Boolean, nullable=False, default=False)
    reorder_reason = Column(String(128), nullable=True)
    raw_order_quantity = Column(Float, nullable=True)
    constrained_order_quantity = Column(Float, nullable=True)

    # Order Constraints & Provenance
    constraint_applied = Column(Boolean, nullable=False, default=False)
    constraint_reason = Column(String(128), nullable=True)

    # Deterministic Risk & Financials
    risk_status = Column(String(64), nullable=True)
    holding_cost_exposure = Column(Float, nullable=True)

    # Core Data State
    value_state = Column(String(32), nullable=False, default="COMPUTED")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
