"""Tenant-isolated repositories for AURIX Phase 5 Supply Intelligence."""

from typing import List, Optional
from sqlalchemy.orm import Session

from aurix_core.database.models.supply_intelligence import (
    SupplyIntelligenceRun,
    SupplierPerformance,
    ReplenishmentRecommendation,
)
from aurix_core.database.repositories.base import BaseRepository


class SupplyIntelligenceRunRepository(BaseRepository[SupplyIntelligenceRun]):
    """Repository for managing supply intelligence execution runs and metadata."""

    def __init__(self, db: Session, tenant_id: str = "default_tenant") -> None:
        super().__init__(SupplyIntelligenceRun, db, tenant_id)

    def get_by_hash(self, dataset_hash: str) -> Optional[SupplyIntelligenceRun]:
        """Retrieves a completed supply run by its deterministic dataset hash for idempotency."""
        return (
            self._base_query()
            .filter(getattr(SupplyIntelligenceRun, "dataset_hash") == dataset_hash)
            .filter(getattr(SupplyIntelligenceRun, "status") == "COMPLETED")
            .first()
        )


class SupplierPerformanceRepository(BaseRepository[SupplierPerformance]):
    """Repository for managing calculated supplier performance metrics and risk evaluations."""

    def __init__(self, db: Session, tenant_id: str = "default_tenant") -> None:
        super().__init__(SupplierPerformance, db, tenant_id)

    def list_by_run_id(self, run_id: str, limit: int = 1000, offset: int = 0) -> List[SupplierPerformance]:
        """Retrieves all supplier performance records generated during a specific run."""
        return (
            self._base_query()
            .filter(getattr(SupplierPerformance, "run_id") == run_id)
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_latest_by_supplier(self, supplier_id: str) -> Optional[SupplierPerformance]:
        """Retrieves the most recent calculated performance metrics for a specific supplier."""
        return (
            self._base_query()
            .filter(getattr(SupplierPerformance, "supplier_id") == supplier_id)
            .order_by(getattr(SupplierPerformance, "created_at").desc())
            .first()
        )


class ReplenishmentRecommendationRepository(BaseRepository[ReplenishmentRecommendation]):
    """Repository for managing procurement decisions and supplier recommendations."""

    def __init__(self, db: Session, tenant_id: str = "default_tenant") -> None:
        super().__init__(ReplenishmentRecommendation, db, tenant_id)

    def list_by_run_id(
        self, run_id: str, limit: int = 1000, offset: int = 0
    ) -> List[ReplenishmentRecommendation]:
        """Retrieves all replenishment recommendations generated during a specific run."""
        return (
            self._base_query()
            .filter(getattr(ReplenishmentRecommendation, "run_id") == run_id)
            .offset(offset)
            .limit(limit)
            .all()
        )

    def list_by_sku(
        self, sku_id: str, limit: int = 100, offset: int = 0
    ) -> List[ReplenishmentRecommendation]:
        """Retrieves historical recommendations for a specific SKU ordered by creation date."""
        return (
            self._base_query()
            .filter(getattr(ReplenishmentRecommendation, "sku_id") == sku_id)
            .order_by(getattr(ReplenishmentRecommendation, "created_at").desc())
            .offset(offset)
            .limit(limit)
            .all()
        )