"""Canonical database models for AURIX Phase 3 Forecasting."""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from aurix_core.database.engine import Base
from aurix_core.database.models.base import TenantMixin


class ForecastRun(Base, TenantMixin):
    """
    Persistent representation of a forecasting execution run.
    Acts as the forecast version and tracks provenance/idempotency.
    """

    __tablename__ = "forecast_runs"

    id = Column(String(64), primary_key=True, index=True)
    dataset_hash = Column(String(128), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="COMPLETED")

    # Run parameters
    frequency = Column(String(16), nullable=False)
    horizon = Column(Integer, nullable=False)

    # Serialized JSON configuration and provenance mapping
    configuration = Column(String, nullable=True)
    provenance = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ForecastPoint(Base, TenantMixin):
    """
    Canonical representation of a single forecast data point in time.
    Preserves raw model output, applied constraints, and uncertainty intervals.
    """

    __tablename__ = "forecast_points"

    id = Column(Integer, primary_key=True, autoincrement=True)
    forecast_run_id = Column(
        String(64), ForeignKey("forecast_runs.id"), nullable=False, index=True
    )

    sku_id = Column(String(64), nullable=False, index=True)
    location_id = Column(String(64), nullable=True, index=True)

    target_date = Column(DateTime, nullable=False, index=True)
    horizon_step = Column(Integer, nullable=False)

    # Core forecast values
    point_forecast = Column(Float, nullable=False)
    raw_model_forecast = Column(Float, nullable=False)
    lower_bound = Column(Float, nullable=True)
    upper_bound = Column(Float, nullable=True)

    # Model & State metadata
    model_id = Column(String(64), nullable=False)
    value_state = Column(String(32), nullable=False, default="COMPUTED")

    # Constraint provenance (Zero-fabrication rule)
    constraint_applied = Column(Boolean, default=False, nullable=False)
    constraint_reason = Column(String(128), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
