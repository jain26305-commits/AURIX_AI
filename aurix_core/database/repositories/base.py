"""
AURIX Enterprise Platform - Base Repository Layer

Canonical generic repository with tenant-scoped reads, write-time tenant
assignment, and compatibility helpers used by the existing domain services.
"""

from __future__ import annotations

from typing import Any, Generic, List, Optional, Sequence, Type, TypeVar

from sqlalchemy.orm import Query, Session

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Generic repository preserving the established AURIX repository semantics.

    Important compatibility rule:
    - the repository owns query scoping;
    - create/create_batch fill a missing tenant_id;
    - callers own transaction commit/rollback;
    - update() only flushes the supplied tracked entity.
    """

    def __init__(
        self,
        model_class: Type[T],
        db: Session,
        tenant_id: Optional[str],
    ) -> None:
        if tenant_id is None or not str(tenant_id).strip():
            raise ValueError("tenant_id must be a non-empty string")

        self.model_class: Type[T] = model_class
        self.db: Session = db
        self.tenant_id: str = str(tenant_id)

    def _base_query(self) -> Query[T]:
        """
        Return the canonical tenant-scoped query.

        Existing Phase 2-6 repositories rely on this compatibility method
        for idempotency and tenant-isolated lookups.
        """
        query: Query[T] = self.db.query(self.model_class)

        tenant_column = getattr(
            self.model_class,
            "tenant_id",
            None,
        )

        if tenant_column is not None:
            query = query.filter(tenant_column == self.tenant_id)

        return query

    def _scoped_query(self) -> Query[T]:
        """Compatibility alias for the canonical tenant-scoped query."""
        return self._base_query()

    def get_by_id(self, id: Any) -> Optional[T]:
        """
        Retrieve a single entity by primary key within the current tenant.

        Returns None when the ID is missing, the model has no conventional
        ``id`` attribute, or the record is outside the current tenant.
        """
        if id is None:
            return None

        id_column = getattr(
            self.model_class,
            "id",
            None,
        )

        if id_column is None:
            return None

        return self._base_query().filter(
            id_column == str(id)
        ).first()

    def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[T]:
        """Retrieve a tenant-scoped paginated collection."""
        if limit < 0:
            raise ValueError("limit must be non-negative")

        if offset < 0:
            raise ValueError("offset must be non-negative")

        return (
            self._base_query()
            .offset(offset)
            .limit(limit)
            .all()
        )

    def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[T]:
        """Backward-compatible alias for get_all()."""
        return self.get_all(
            limit=limit,
            offset=offset,
        )

    def create(self, entity: T) -> T:
        """
        Stage and flush an entity without committing.

        Preserve the established behavior: a missing entity tenant is filled
        from this repository; an explicitly supplied tenant is not rewritten.
        """
        if hasattr(entity, "tenant_id"):
            current_tenant = getattr(
                entity,
                "tenant_id",
                None,
            )

            if not current_tenant:
                setattr(
                    entity,
                    "tenant_id",
                    self.tenant_id,
                )

        self.db.add(entity)
        self.db.flush()
        return entity

    def create_batch(
        self,
        entities: Sequence[T],
    ) -> List[T]:
        """Stage and flush multiple entities without committing."""
        materialized = list(entities)

        for entity in materialized:
            if hasattr(entity, "tenant_id"):
                current_tenant = getattr(
                    entity,
                    "tenant_id",
                    None,
                )

                if not current_tenant:
                    setattr(
                        entity,
                        "tenant_id",
                        self.tenant_id,
                    )

        self.db.add_all(materialized)
        self.db.flush()
        return materialized

    def update(self, entity: T) -> T:
        """
        Flush an already tracked entity.

        No implicit merge or ownership mutation is introduced here; this
        preserves the existing domain-service transaction semantics.
        """
        self.db.flush()
        return entity

    def delete(self, id: Any) -> bool:
        """Delete an entity by ID only when it is visible to this tenant."""
        entity = self.get_by_id(id)

        if entity is None:
            return False

        self.db.delete(entity)
        self.db.flush()
        return True

    def count(self) -> int:
        """Count all entities visible within this tenant."""
        return self._base_query().count()