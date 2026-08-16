"""Canonical database models for AURIX Phase 5 Supply Intelligence."""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from aurix_core.database.engine import Base
from aurix_core.database.models.base import TenantMixin


class SupplyIntelligenceRun(Base, TenantMixin):
    """
    Persistent representation of a supply intelligence execution run.
    Tracks idempotency, configuration, and execution status.
    """

    __tablename__ = "supply_intelligence_runs"

    id = Column(String(64), primary_key=True, index=True)
    dataset_hash = Column(String(128), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="COMPLETED")

    # Serialized JSON configuration and provenance tracking
    configuration = Column(String, nullable=True)
    provenance = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class SupplierPerformance(Base, TenantMixin):
    """
    Canonical representation of computed supplier historical performance and risk.
    Preserves sample size to protect against statistically unreliable assertions.
    """

    __tablename__ = "supplier_performance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(
        String(64), ForeignKey("supply_intelligence_runs.id"), nullable=False, index=True
    )

    supplier_id = Column(String(64), nullable=False, index=True)

    # Sample Size Safety
    evaluated_order_count = Column(Integer, nullable=False, default=0)

    # Empirical Metrics (Nullable to enforce Zero-Fabrication for missing data)
    otd_rate = Column(Float, nullable=True)
    in_full_rate = Column(Float, nullable=True)
    otif_rate = Column(Float, nullable=True)
    fill_rate = Column(Float, nullable=True)

    lead_time_mean = Column(Float, nullable=True)
    lead_time_std = Column(Float, nullable=True)
    defect_rate = Column(Float, nullable=True)

    # Deterministic Risk
    risk_score = Column(Float, nullable=True)
    risk_level = Column(String(64), nullable=True)
    risk_drivers = Column(String, nullable=True)  # JSON serialized list of risk factors

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ReplenishmentRecommendation(Base, TenantMixin):
    """
    Links a Phase 4 replenishment requirement to a deterministically selected supplier.
    Preserves order constraints, currency isolation, and selection provenance.
    """

    __tablename__ = "replenishment_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(
        String(64), ForeignKey("supply_intelligence_runs.id"), nullable=False, index=True
    )

    # Upstream integration with Phase 4 Inventory Intelligence
    replenishment_policy_id = Column(
        Integer, ForeignKey("replenishment_policies.id"), nullable=True, index=True
    )

    sku_id = Column(String(64), nullable=False, index=True)
    supplier_id = Column(String(64), nullable=False, index=True)

    # Quantity & Constraint Tracking
    raw_quantity = Column(Float, nullable=False)
    constrained_quantity = Column(Float, nullable=False)
    moq_applied = Column(Boolean, nullable=False, default=False)
    pack_size_applied = Column(Boolean, nullable=False, default=False)

    # Financials & Currency Safety (Zero-Fabrication)
    unit_price = Column(Float, nullable=True)
    total_purchase_cost = Column(Float, nullable=True)
    currency = Column(String(16), nullable=True)

    # Deterministic Selection Evidence
    selection_rank = Column(Integer, nullable=False)
    selection_reason = Column(String, nullable=True)
    single_source_dependency = Column(Boolean, nullable=False, default=False)

    # Core Data State
    value_state = Column(String(32), nullable=False, default="COMPUTED")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)