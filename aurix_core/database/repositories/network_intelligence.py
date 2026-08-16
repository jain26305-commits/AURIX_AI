"""Tenant-isolated repositories for Phase 7 Network Intelligence persistence."""

from typing import Optional, List, TypeVar, Any

from sqlalchemy.orm import Session

from aurix_core.database.models.network_intelligence import (
    NetworkIntelligenceRun,
    NetworkNodeSnapshot,
    NetworkEdgeSnapshot,
    NetworkRiskEvent,
)
from aurix_core.database.repositories.base import BaseRepository


ModelT = TypeVar(
    "ModelT",
    NetworkIntelligenceRun,
    NetworkNodeSnapshot,
    NetworkEdgeSnapshot,
    NetworkRiskEvent,
)


class NetworkIntelligenceRunRepository(
    BaseRepository[NetworkIntelligenceRun]
):
    """Tenant-isolated repository for network intelligence execution runs."""

    def __init__(self, db: Session, tenant_id: str) -> None:
        # BaseRepository requires:
        #   (model, db, tenant_id)
        super().__init__(NetworkIntelligenceRun, db, tenant_id)

    def get_by_hash(
        self,
        dataset_hash: str,
    ) -> Optional[NetworkIntelligenceRun]:
        """Return the completed/existing run for this tenant and dataset hash."""
        return (
            self.db.query(NetworkIntelligenceRun)
            .filter(
                NetworkIntelligenceRun.tenant_id == self.tenant_id,
                NetworkIntelligenceRun.dataset_hash == dataset_hash,
            )
            .order_by(NetworkIntelligenceRun.created_at.desc())
            .first()
        )

    def get_by_run_id(
        self,
        run_id: Optional[Any],
    ) -> Optional[NetworkIntelligenceRun]:
        """
        Return a run by its canonical execution ID.

        IMPORTANT:
        No global fallback is permitted.
        A missing record returns None.
        """
        if run_id is None:
            return None

        run_id_str = str(run_id).strip()
        if not run_id_str:
            return None

        return (
            self.db.query(NetworkIntelligenceRun)
            .filter(
                NetworkIntelligenceRun.tenant_id == self.tenant_id,
                NetworkIntelligenceRun.id == run_id_str,
            )
            .first()
        )

    def get_by_id(
        self,
        id_val: Any,
    ) -> Optional[NetworkIntelligenceRun]:
        """
        Return a run by primary key.

        This method intentionally returns None when the requested record
        does not exist. It must never fabricate a record or return another
        tenant's record.
        """
        if id_val is None:
            return None

        id_str = str(id_val).strip()
        if not id_str:
            return None

        return (
            self.db.query(NetworkIntelligenceRun)
            .filter(
                NetworkIntelligenceRun.tenant_id == self.tenant_id,
                NetworkIntelligenceRun.id == id_str,
            )
            .first()
        )

    def get_latest_run(self) -> Optional[NetworkIntelligenceRun]:
        """Return the latest run belonging to the current tenant only."""
        return (
            self.db.query(NetworkIntelligenceRun)
            .filter(
                NetworkIntelligenceRun.tenant_id == self.tenant_id,
            )
            .order_by(NetworkIntelligenceRun.created_at.desc())
            .first()
        )

    def get_provenance(
        self,
        run_id: Optional[Any],
    ) -> dict[str, Any]:
        """Return persisted provenance for a specific tenant-scoped run."""
        run = self.get_by_run_id(run_id)

        if run is None:
            return {}

        provenance = run.provenance

        if not provenance:
            return {}

        try:
            import json

            parsed = json.loads(str(provenance))
        except (TypeError, ValueError):
            return {}

        return parsed if isinstance(parsed, dict) else {}


class NetworkNodeSnapshotRepository(
    BaseRepository[NetworkNodeSnapshot]
):
    """Tenant-isolated repository for network node snapshots."""

    def __init__(self, db: Session, tenant_id: str) -> None:
        super().__init__(NetworkNodeSnapshot, db, tenant_id)

    def list_by_run_id(
        self,
        run_id: str,
    ) -> List[NetworkNodeSnapshot]:
        """Return node snapshots for exactly this tenant and run."""
        return (
            self.db.query(NetworkNodeSnapshot)
            .filter(
                NetworkNodeSnapshot.tenant_id == self.tenant_id,
                NetworkNodeSnapshot.run_id == str(run_id),
            )
            .all()
        )


class NetworkEdgeSnapshotRepository(
    BaseRepository[NetworkEdgeSnapshot]
):
    """Tenant-isolated repository for network edge snapshots."""

    def __init__(self, db: Session, tenant_id: str) -> None:
        super().__init__(NetworkEdgeSnapshot, db, tenant_id)

    def list_by_run_id(
        self,
        run_id: str,
    ) -> List[NetworkEdgeSnapshot]:
        """Return edge snapshots for exactly this tenant and run."""
        return (
            self.db.query(NetworkEdgeSnapshot)
            .filter(
                NetworkEdgeSnapshot.tenant_id == self.tenant_id,
                NetworkEdgeSnapshot.run_id == str(run_id),
            )
            .all()
        )


class NetworkRiskEventRepository(
    BaseRepository[NetworkRiskEvent]
):
    """Tenant-isolated repository for network risk events."""

    def __init__(self, db: Session, tenant_id: str) -> None:
        super().__init__(NetworkRiskEvent, db, tenant_id)

    def list_by_run_id(
        self,
        run_id: str,
    ) -> List[NetworkRiskEvent]:
        """Return risk events for exactly this tenant and run."""
        return (
            self.db.query(NetworkRiskEvent)
            .filter(
                NetworkRiskEvent.tenant_id == self.tenant_id,
                NetworkRiskEvent.run_id == str(run_id),
            )
            .all()
        )


# Backward-compatible aliases used by some older Phase 7 code paths.
NetworkFlowRunRepository = NetworkIntelligenceRunRepository
NetworkRiskSnapshotRepository = NetworkRiskEventRepository