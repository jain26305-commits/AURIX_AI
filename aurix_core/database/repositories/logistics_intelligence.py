"""Tenant-isolated repositories for AURIX Phase 6 Logistics Intelligence."""

from typing import List, Optional
from sqlalchemy.orm import Session

from aurix_core.database.models.logistics_intelligence import (
    LogisticsIntelligenceRun,
    CarrierPerformance,
    LanePerformance,
    ShipmentEvaluation,
)
from aurix_core.database.repositories.base import BaseRepository


class LogisticsIntelligenceRunRepository(BaseRepository[LogisticsIntelligenceRun]):
    """Repository for managing logistics intelligence execution runs and metadata."""

    def __init__(self, db: Session, tenant_id: str = "default_tenant") -> None:
        super().__init__(LogisticsIntelligenceRun, db, tenant_id)

    def get_by_hash(self, dataset_hash: str) -> Optional[LogisticsIntelligenceRun]:
        """Retrieves a completed logistics run by its deterministic dataset hash for idempotency."""
        return (
            self._base_query()
            .filter(getattr(LogisticsIntelligenceRun, "dataset_hash") == dataset_hash)
            .filter(getattr(LogisticsIntelligenceRun, "status") == "COMPLETED")
            .first()
        )


class CarrierPerformanceRepository(BaseRepository[CarrierPerformance]):
    """Repository for managing computed carrier performance and risk evaluations."""

    def __init__(self, db: Session, tenant_id: str = "default_tenant") -> None:
        super().__init__(CarrierPerformance, db, tenant_id)

    def list_by_run_id(
        self, run_id: str, limit: int = 1000, offset: int = 0
    ) -> List[CarrierPerformance]:
        """Retrieves all carrier performance records for a specific run."""
        return (
            self._base_query()
            .filter(getattr(CarrierPerformance, "run_id") == run_id)
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_latest_by_carrier(self, carrier_id: str) -> Optional[CarrierPerformance]:
        """Retrieves the most recent calculated performance metrics for a specific carrier."""
        return (
            self._base_query()
            .filter(getattr(CarrierPerformance, "carrier_id") == carrier_id)
            .order_by(getattr(CarrierPerformance, "created_at").desc())
            .first()
        )


class LanePerformanceRepository(BaseRepository[LanePerformance]):
    """Repository for managing transportation lane transit and percentile metrics."""

    def __init__(self, db: Session, tenant_id: str = "default_tenant") -> None:
        super().__init__(LanePerformance, db, tenant_id)

    def list_by_run_id(
        self, run_id: str, limit: int = 1000, offset: int = 0
    ) -> List[LanePerformance]:
        """Retrieves all lane performance records for a specific run."""
        return (
            self._base_query()
            .filter(getattr(LanePerformance, "run_id") == run_id)
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_latest_by_lane(
        self, origin_id: str, destination_id: str, carrier_id: Optional[str] = None
    ) -> Optional[LanePerformance]:
        """Retrieves the latest lane metrics for an origin-destination pair."""
        query = (
            self._base_query()
            .filter(getattr(LanePerformance, "origin_id") == origin_id)
            .filter(getattr(LanePerformance, "destination_id") == destination_id)
        )
        if carrier_id:
            query = query.filter(getattr(LanePerformance, "carrier_id") == carrier_id)
        return query.order_by(getattr(LanePerformance, "created_at").desc()).first()


class ShipmentEvaluationRepository(BaseRepository[ShipmentEvaluation]):
    """Repository for managing active shipment evaluations and expedite recommendations."""

    def __init__(self, db: Session, tenant_id: str = "default_tenant") -> None:
        super().__init__(ShipmentEvaluation, db, tenant_id)

    def list_by_run_id(
        self, run_id: str, limit: int = 1000, offset: int = 0
    ) -> List[ShipmentEvaluation]:
        """Retrieves all shipment evaluations generated during a specific run."""
        return (
            self._base_query()
            .filter(getattr(ShipmentEvaluation, "run_id") == run_id)
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_by_shipment_id(self, shipment_id: str) -> Optional[ShipmentEvaluation]:
        """Retrieves the latest evaluation for a specific shipment."""
        return (
            self._base_query()
            .filter(getattr(ShipmentEvaluation, "shipment_id") == shipment_id)
            .order_by(getattr(ShipmentEvaluation, "created_at").desc())
            .first()
        )