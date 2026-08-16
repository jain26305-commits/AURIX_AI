"""Tenant-isolated repositories for AURIX Phase 3 Forecasting."""

from typing import List, Optional
from sqlalchemy.orm import Session

from aurix_core.database.models.forecasting import ForecastRun, ForecastPoint
from aurix_core.database.repositories.base import BaseRepository


class ForecastRunRepository(BaseRepository[ForecastRun]):
    """Repository for managing forecast execution runs and metadata."""

    def __init__(self, db: Session, tenant_id: str = "default_tenant") -> None:
        super().__init__(ForecastRun, db, tenant_id)

    def get_by_hash(self, dataset_hash: str) -> Optional[ForecastRun]:
        """Retrieves a completed forecast run by its deterministic dataset hash."""
        return (
            self._base_query()
            .filter(getattr(ForecastRun, "dataset_hash") == dataset_hash)
            .filter(getattr(ForecastRun, "status") == "COMPLETED")
            .first()
        )


class ForecastPointRepository(BaseRepository[ForecastPoint]):
    """Repository for managing individual canonical forecast data points."""

    def __init__(self, db: Session, tenant_id: str = "default_tenant") -> None:
        super().__init__(ForecastPoint, db, tenant_id)

    def list_by_run_id(self, run_id: str, limit: int = 1000, offset: int = 0) -> List[ForecastPoint]:
        """Retrieves all forecast points generated during a specific run."""
        return (
            self._base_query()
            .filter(getattr(ForecastPoint, "forecast_run_id") == run_id)
            .offset(offset)
            .limit(limit)
            .all()
        )

    def list_by_sku(self, sku_id: str, limit: int = 100, offset: int = 0) -> List[ForecastPoint]:
        """Retrieves historical forecast points for a specific SKU."""
        return (
            self._base_query()
            .filter(getattr(ForecastPoint, "sku_id") == sku_id)
            .order_by(getattr(ForecastPoint, "target_date").desc())
            .offset(offset)
            .limit(limit)
            .all()
        )