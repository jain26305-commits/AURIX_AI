"""Canonical database models for AURIX Phase 6 Logistics Intelligence."""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from aurix_core.database.engine import Base
from aurix_core.database.models.base import TenantMixin


class LogisticsIntelligenceRun(Base, TenantMixin):
    """
    Persistent representation of a logistics intelligence execution run.
    Tracks SHA-256 dataset hash for idempotency, configuration, and execution status.
    """

    __tablename__ = "logistics_intelligence_runs"

    id = Column(String(64), primary_key=True, index=True)
    dataset_hash = Column(String(128), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="COMPLETED")

    # Serialized JSON configuration and provenance tracking
    configuration = Column(String, nullable=True)
    provenance = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CarrierPerformance(Base, TenantMixin):
    """
    Canonical representation of computed historical carrier performance and risk.
    Preserves sample size to protect against statistically unreliable assertions.
    """

    __tablename__ = "carrier_performance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(
        String(64), ForeignKey("logistics_intelligence_runs.id"), nullable=False, index=True
    )

    carrier_id = Column(String(64), nullable=False, index=True)

    # Sample Size Safety
    evaluated_order_count = Column(Integer, nullable=False, default=0)

    # Empirical Metrics (Nullable to enforce Zero-Fabrication for missing data)
    otd_rate = Column(Float, nullable=True)
    in_full_rate = Column(Float, nullable=True)
    otif_rate = Column(Float, nullable=True)

    mean_transit_days = Column(Float, nullable=True)
    transit_std_days = Column(Float, nullable=True)

    # Risk Metrics
    risk_score = Column(Float, nullable=True)
    risk_level = Column(String(64), nullable=True)
    risk_drivers = Column(String, nullable=True)  # Serialized JSON list

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class LanePerformance(Base, TenantMixin):
    """
    Canonical representation of transportation lane performance between origin and destination.
    Stores percentile metrics (P90, P95) and median transit times.
    """

    __tablename__ = "lane_performance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(
        String(64), ForeignKey("logistics_intelligence_runs.id"), nullable=False, index=True
    )

    origin_id = Column(String(64), nullable=False, index=True)
    destination_id = Column(String(64), nullable=False, index=True)
    carrier_id = Column(String(64), nullable=True, index=True)

    # Sample Size Safety
    evaluated_shipment_count = Column(Integer, nullable=False, default=0)

    # Transit Percentiles & Central Tendency
    mean_transit_days = Column(Float, nullable=True)
    median_transit_days = Column(Float, nullable=True)
    p90_transit_days = Column(Float, nullable=True)
    p95_transit_days = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ShipmentEvaluation(Base, TenantMixin):
    """
    Persistent evaluation of active or historical shipments linking ETA intelligence,
    inventory consequence analysis, expedite recommendations, and freight financials.
    """

    __tablename__ = "shipment_evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(
        String(64), ForeignKey("logistics_intelligence_runs.id"), nullable=False, index=True
    )

    shipment_id = Column(String(64), nullable=False, index=True)
    order_id = Column(String(64), nullable=True, index=True)
    sku_id = Column(String(64), nullable=True, index=True)
    carrier_id = Column(String(64), nullable=True, index=True)
    origin_id = Column(String(64), nullable=True)
    destination_id = Column(String(64), nullable=True)

    # Quantities & Physical Weights
    quantity = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)

    # Timestamps & ETA Precedence Details
    dispatch_date = Column(DateTime, nullable=True)
    promised_delivery_date = Column(DateTime, nullable=True)
    estimated_delivery_date = Column(DateTime, nullable=True)
    actual_delivery_date = Column(DateTime, nullable=True)
    eta_source = Column(String(64), nullable=True)

    # Delay Tracking
    delay_hours = Column(Float, nullable=True)
    is_delayed = Column(Boolean, nullable=False, default=False)

    # Risk & Expedite Decision Engine
    logistics_risk_score = Column(Float, nullable=True)
    risk_level = Column(String(64), nullable=True)
    expedite_recommendation = Column(String(64), nullable=True)  # NORMAL, MONITOR, EXPEDITE_RECOMMENDED, EXPEDITE_CRITICAL
    recommendation_reason = Column(String, nullable=True)

    # Financials & Freight Unit Economics (Currency Isolation)
    freight_cost = Column(Float, nullable=True)
    cost_per_unit = Column(Float, nullable=True)
    cost_per_kg = Column(Float, nullable=True)
    currency = Column(String(16), nullable=True)

    # Value State
    value_state = Column(String(32), nullable=False, default="COMPUTED")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)