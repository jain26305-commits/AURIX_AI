"""Tenant-isolated repositories for AURIX Phase 4 Inventory Intelligence."""

from typing import List, Optional
from sqlalchemy.orm import Session

from aurix_core.database.models.inventory_intelligence import InventoryIntelligenceRun, ReplenishmentPolicy
from aurix_core.database.repositories.base import BaseRepository


class InventoryIntelligenceRunRepository(BaseRepository[InventoryIntelligenceRun]):
    """Repository for managing inventory intelligence execution runs and metadata."""

    def __init__(self, db: Session, tenant_id: str = "default_tenant") -> None:
        super().__init__(InventoryIntelligenceRun, db, tenant_id)

    def get_by_hash(self, dataset_hash: str) -> Optional[InventoryIntelligenceRun]:
        """Retrieves a completed inventory run by its deterministic dataset hash for idempotency."""
        return (
            self._base_query()
            .filter(getattr(InventoryIntelligenceRun, "dataset_hash") == dataset_hash)
            .filter(getattr(InventoryIntelligenceRun, "status") == "COMPLETED")
            .first()
        )


class ReplenishmentPolicyRepository(BaseRepository[ReplenishmentPolicy]):
    """Repository for managing calculated inventory parameters and replenishment decisions."""

    def __init__(self, db: Session, tenant_id: str = "default_tenant") -> None:
        super().__init__(ReplenishmentPolicy, db, tenant_id)

    def list_by_run_id(self, run_id: str, limit: int = 1000, offset: int = 0) -> List[ReplenishmentPolicy]:
        """Retrieves all replenishment policies generated during a specific run."""
        return (
            self._base_query()
            .filter(getattr(ReplenishmentPolicy, "run_id") == run_id)
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_latest_by_sku(self, sku_id: str) -> Optional[ReplenishmentPolicy]:
        """Retrieves the most recent replenishment policy for a specific SKU."""
        return (
            self._base_query()
            .filter(getattr(ReplenishmentPolicy, "sku_id") == sku_id)
            .order_by(getattr(ReplenishmentPolicy, "created_at").desc())
            .first()
        )