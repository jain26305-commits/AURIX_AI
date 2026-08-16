"""Tenant-isolated CRUD repositories for Phase 8 Financial Intelligence entities."""

from typing import List, Optional
from sqlalchemy.orm import Session
from aurix_core.database.repositories.base import BaseRepository
from aurix_core.database.models.economics import (
    FinancialIntelligenceRun,
    FinancialBaselineSnapshot,
    ScenarioRun,
    ScenarioMetricSnapshot,
)


class FinancialIntelligenceRunRepository(BaseRepository[FinancialIntelligenceRun]):
    """Repository for managing FinancialIntelligenceRun persistence with multi-tenant isolation."""

    def __init__(self, db: Session, tenant_id: str) -> None:
        super().__init__(FinancialIntelligenceRun, db, tenant_id)

    def get_by_hash(self, dataset_hash: str) -> Optional[FinancialIntelligenceRun]:
        """Retrieves a financial intelligence run by its canonical dataset hash."""
        return (
            self.db.query(FinancialIntelligenceRun)
            .filter(
                FinancialIntelligenceRun.tenant_id == self.tenant_id,
                FinancialIntelligenceRun.dataset_hash == dataset_hash,
            )
            .first()
        )


class FinancialBaselineSnapshotRepository(BaseRepository[FinancialBaselineSnapshot]):
    """Repository for managing FinancialBaselineSnapshot persistence with multi-tenant isolation."""

    def __init__(self, db: Session, tenant_id: str) -> None:
        super().__init__(FinancialBaselineSnapshot, db, tenant_id)

    def list_by_run_id(self, run_id: str) -> List[FinancialBaselineSnapshot]:
        """Lists all baseline snapshots associated with a specific run ID."""
        return (
            self.db.query(FinancialBaselineSnapshot)
            .filter(
                FinancialBaselineSnapshot.tenant_id == self.tenant_id,
                FinancialBaselineSnapshot.run_id == run_id,
            )
            .all()
        )


class ScenarioRunRepository(BaseRepository[ScenarioRun]):
    """Repository for managing ScenarioRun persistence with multi-tenant isolation."""

    def __init__(self, db: Session, tenant_id: str) -> None:
        super().__init__(ScenarioRun, db, tenant_id)

    def list_by_run_id(self, run_id: str) -> List[ScenarioRun]:
        """Lists all scenario runs associated with a specific run ID."""
        return (
            self.db.query(ScenarioRun)
            .filter(
                ScenarioRun.tenant_id == self.tenant_id,
                ScenarioRun.run_id == run_id,
            )
            .all()
        )


class ScenarioMetricSnapshotRepository(BaseRepository[ScenarioMetricSnapshot]):
    """Repository for managing ScenarioMetricSnapshot persistence with multi-tenant isolation."""

    def __init__(self, db: Session, tenant_id: str) -> None:
        super().__init__(ScenarioMetricSnapshot, db, tenant_id)

    def list_by_scenario_run_id(self, scenario_run_id: str) -> List[ScenarioMetricSnapshot]:
        """Lists metric snapshots associated with a specific scenario run ID."""
        return (
            self.db.query(ScenarioMetricSnapshot)
            .filter(
                ScenarioMetricSnapshot.tenant_id == self.tenant_id,
                ScenarioMetricSnapshot.scenario_run_id == scenario_run_id,
            )
            .all()
        )