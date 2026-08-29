"""Tenant-isolated CRUD repositories for Phase 9 & Phase 10 Executive Intelligence entities."""

from typing import List, Optional
from sqlalchemy.orm import Session

from aurix_core.database.models.intelligence import (
    AIAuditLogModel,
    BusinessSignalModel,
    CapabilityStateModel,
    ConversationMessageModel,
    ConversationModel,
    ExecutiveSummaryModel,
    IntelligenceRunModel,
    IntelligenceSnapshotModel,
    PrioritizedActionModel,
)
from aurix_core.database.repositories.base import BaseRepository


class IntelligenceRunRepository(BaseRepository[IntelligenceRunModel]):
    """Repository for managing IntelligenceRunModel persistence with multi-tenant isolation."""

    def __init__(self, db: Session, tenant_id: str) -> None:
        super().__init__(IntelligenceRunModel, db, tenant_id)

    def get_by_id(self, run_id: str) -> Optional[IntelligenceRunModel]:
        """Retrieves a specific run by ID for the active tenant."""
        return (
            self.db.query(IntelligenceRunModel)
            .filter(
                IntelligenceRunModel.tenant_id == self.tenant_id,
                IntelligenceRunModel.id == run_id,
            )
            .first()
        )

    def get_by_hash(self, dataset_hash: str) -> Optional[IntelligenceRunModel]:
        """Retrieves an intelligence run by its canonical dataset hash."""
        return (
            self.db.query(IntelligenceRunModel)
            .filter(
                IntelligenceRunModel.tenant_id == self.tenant_id,
                IntelligenceRunModel.dataset_hash == dataset_hash,
            )
            .first()
        )

    def get_latest(self) -> Optional[IntelligenceRunModel]:
        """Retrieves the latest intelligence run for the active tenant."""
        return (
            self.db.query(IntelligenceRunModel)
            .filter(IntelligenceRunModel.tenant_id == self.tenant_id)
            .first()
        )


class CapabilityStateRepository(BaseRepository[CapabilityStateModel]):
    """Repository for managing discovered capability states with multi-tenant isolation."""

    def __init__(self, db: Session, tenant_id: str) -> None:
        super().__init__(CapabilityStateModel, db, tenant_id)

    def list_by_run_id(self, run_id: str) -> List[CapabilityStateModel]:
        """Lists all capability states evaluated during a specific run ID."""
        return (
            self.db.query(CapabilityStateModel)
            .filter(
                CapabilityStateModel.tenant_id == self.tenant_id,
                CapabilityStateModel.run_id == run_id,
            )
            .all()
        )

    def get_by_name(self, run_id: str, capability_name: str) -> Optional[CapabilityStateModel]:
        """Retrieves a specific capability state by name and run ID."""
        return (
            self.db.query(CapabilityStateModel)
            .filter(
                CapabilityStateModel.tenant_id == self.tenant_id,
                CapabilityStateModel.run_id == run_id,
                CapabilityStateModel.capability_name == capability_name,
            )
            .first()
        )


class IntelligenceSnapshotRepository(BaseRepository[IntelligenceSnapshotModel]):
    """Repository for managing verified intelligence snapshots with multi-tenant isolation."""

    def __init__(self, db: Session, tenant_id: str) -> None:
        super().__init__(IntelligenceSnapshotModel, db, tenant_id)

    def get_latest_snapshot(self) -> Optional[IntelligenceSnapshotModel]:
        """Retrieves the most recent verified intelligence snapshot for the tenant."""
        return (
            self.db.query(IntelligenceSnapshotModel)
            .filter(IntelligenceSnapshotModel.tenant_id == self.tenant_id)
            .first()
        )

    def get_by_run_id(self, run_id: str) -> Optional[IntelligenceSnapshotModel]:
        """Retrieves the snapshot associated with a specific run ID."""
        return (
            self.db.query(IntelligenceSnapshotModel)
            .filter(
                IntelligenceSnapshotModel.tenant_id == self.tenant_id,
                IntelligenceSnapshotModel.run_id == run_id,
            )
            .first()
        )


class BusinessSignalRepository(BaseRepository[BusinessSignalModel]):
    """Repository for managing business signals with multi-tenant isolation."""

    def __init__(self, db: Session, tenant_id: str) -> None:
        super().__init__(BusinessSignalModel, db, tenant_id)

    def list_by_run_id(self, run_id: str) -> List[BusinessSignalModel]:
        """Lists business signals associated with a specific run ID."""
        return (
            self.db.query(BusinessSignalModel)
            .filter(
                BusinessSignalModel.tenant_id == self.tenant_id,
                BusinessSignalModel.run_id == run_id,
            )
            .all()
        )


class PrioritizedActionRepository(BaseRepository[PrioritizedActionModel]):
    """Repository for managing prioritized actions with multi-tenant isolation."""

    def __init__(self, db: Session, tenant_id: str) -> None:
        super().__init__(PrioritizedActionModel, db, tenant_id)

    def list_by_run_id(self, run_id: str) -> List[PrioritizedActionModel]:
        """Lists prioritized actions associated with a specific run ID."""
        return (
            self.db.query(PrioritizedActionModel)
            .filter(
                PrioritizedActionModel.tenant_id == self.tenant_id,
                PrioritizedActionModel.run_id == run_id,
            )
            .all()
        )


class ExecutiveSummaryRepository(BaseRepository[ExecutiveSummaryModel]):
    """Repository for managing executive summaries with multi-tenant isolation."""

    def __init__(self, db: Session, tenant_id: str) -> None:
        super().__init__(ExecutiveSummaryModel, db, tenant_id)

    def get_latest(self) -> Optional[ExecutiveSummaryModel]:
        """Retrieves the latest executive summary record for the tenant."""
        return (
            self.db.query(ExecutiveSummaryModel)
            .filter(ExecutiveSummaryModel.tenant_id == self.tenant_id)
            .first()
        )

    def get_latest_summary(self) -> Optional[ExecutiveSummaryModel]:
        """Alias for get_latest."""
        return self.get_latest()

    def get_by_run_id(self, run_id: str) -> Optional[ExecutiveSummaryModel]:
        """Retrieves the executive summary associated with a specific run ID."""
        return (
            self.db.query(ExecutiveSummaryModel)
            .filter(
                ExecutiveSummaryModel.tenant_id == self.tenant_id,
                ExecutiveSummaryModel.run_id == run_id,
            )
            .first()
        )


class ConversationRepository(BaseRepository[ConversationModel]):
    """Repository for managing conversational sessions with strict tenant isolation."""

    def __init__(self, db: Session, tenant_id: str) -> None:
        super().__init__(ConversationModel, db, tenant_id)

    def get_conversation(self, conversation_id: str) -> Optional[ConversationModel]:
        """Securely retrieves a conversation ensuring it strictly belongs to the current tenant."""
        return (
            self.db.query(ConversationModel)
            .filter(
                ConversationModel.tenant_id == self.tenant_id,
                ConversationModel.id == conversation_id,
            )
            .first()
        )


class ConversationMessageRepository(BaseRepository[ConversationMessageModel]):
    """Repository for managing conversation message history with tenant isolation."""

    def __init__(self, db: Session, tenant_id: str) -> None:
        super().__init__(ConversationMessageModel, db, tenant_id)

    def list_by_conversation(
        self,
        conversation_id: str,
        limit: int = 50,
    ) -> List[ConversationMessageModel]:
        """
        Return the latest messages for a conversation in chronological order.

        The database selects the newest ``limit`` records deterministically,
        then the result is reversed for downstream oldest-to-newest processing.
        Tenant isolation remains enforced by the query predicate.
        """
        if limit <= 0:
            return []

        messages = (
            self.db.query(ConversationMessageModel)
            .filter(
                ConversationMessageModel.tenant_id == self.tenant_id,
                ConversationMessageModel.conversation_id == conversation_id,
            )
            .order_by(
                ConversationMessageModel.created_at.desc(),
                ConversationMessageModel.id.desc(),
            )
            .limit(limit)
            .all()
        )

        return list(reversed(messages))

class AIAuditLogRepository(BaseRepository[AIAuditLogModel]):
    """Repository for auditing AI interactions with multi-tenant isolation."""

    def __init__(self, db: Session, tenant_id: str) -> None:
        super().__init__(AIAuditLogModel, db, tenant_id)

    def list_by_conversation(self, conversation_id: str) -> List[AIAuditLogModel]:
        """Lists audit logs associated with a conversation session."""
        return (
            self.db.query(AIAuditLogModel)
            .filter(
                AIAuditLogModel.tenant_id == self.tenant_id,
                AIAuditLogModel.conversation_id == conversation_id,
            )
            .all()
        )


# Backward compatibility aliases
EarlyWarningSignalRepository = BusinessSignalRepository
AutonomousActionRepository = PrioritizedActionRepository
