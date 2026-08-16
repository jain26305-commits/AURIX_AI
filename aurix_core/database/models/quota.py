"""SQLAlchemy persistent ORM models for tenant-scoped AI quota policies,
usage ledgers, and atomic AI budget reservations.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
)

from aurix_core.database.engine import Base


class AIUsagePolicy(Base):
    """Persistent storage model for tenant-specific AI spend and usage limits."""

    __tablename__ = "ai_usage_policies"

    tenant_id = Column(
        String(64),
        primary_key=True,
        index=True,
        nullable=False,
    )

    monthly_spend_limit_usd = Column(
        Float,
        nullable=False,
        default=500.0,
    )
    daily_spend_limit_usd = Column(
        Float,
        nullable=False,
        default=50.0,
    )

    monthly_token_limit = Column(
        Integer,
        nullable=False,
        default=10_000_000,
    )
    daily_token_limit = Column(
        Integer,
        nullable=False,
        default=1_000_000,
    )

    monthly_request_limit = Column(
        Integer,
        nullable=False,
        default=5_000,
    )
    daily_request_limit = Column(
        Integer,
        nullable=False,
        default=500,
    )

    warning_threshold_pct = Column(
        Float,
        nullable=False,
        default=80.0,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    # ------------------------------------------------------------
    # Atomic quota reservation state
    # ------------------------------------------------------------
    #
    # These represent usage that has been RESERVED for in-flight
    # requests but has not yet been settled into AIUsageLedger.
    #
    # They are deliberately stored on the tenant policy row so
    # SELECT ... FOR UPDATE can serialize concurrent reservations.
    #
    reserved_spend_usd = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    reserved_token_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    reserved_request_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class AIUsageLedger(Base):
    """Persistent immutable ledger of completed AI provider interactions."""

    __tablename__ = "ai_usage_ledgers"

    record_id = Column(
        String(64),
        primary_key=True,
        nullable=False,
    )

    tenant_id = Column(
        String(64),
        index=True,
        nullable=False,
    )

    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    date_str = Column(
        String(10),
        index=True,
        nullable=False,
    )  # YYYY-MM-DD

    month_str = Column(
        String(7),
        index=True,
        nullable=False,
    )  # YYYY-MM

    provider = Column(
        String(64),
        nullable=False,
    )

    model = Column(
        String(128),
        nullable=False,
    )

    input_tokens = Column(
        Integer,
        nullable=False,
        default=0,
    )

    output_tokens = Column(
        Integer,
        nullable=False,
        default=0,
    )

    estimated_cost_usd = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    is_fallback = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Links completed usage back to the reservation that authorised it.
    reservation_id = Column(
        String(64),
        nullable=True,
        index=True,
    )

    # Optional lifecycle/provenance information.
    status = Column(
        String(32),
        nullable=False,
        default="SETTLED",
    )

    __table_args__ = (
        Index(
            "ix_ai_ledger_tenant_date",
            "tenant_id",
            "date_str",
        ),
        Index(
            "ix_ai_ledger_tenant_month",
            "tenant_id",
            "month_str",
        ),
        Index(
            "ix_ai_ledger_tenant_reservation",
            "tenant_id",
            "reservation_id",
        ),
    )


class AIQuotaReservation(Base):
    """
    Persistent reservation for an in-flight AI request.

    A reservation is created BEFORE the external AI provider is called.
    The tenant policy row is locked during reservation creation so
    concurrent requests cannot oversubscribe the configured budget.

    Lifecycle:

        RESERVED
            ↓
        SETTLED

    or:

        RESERVED
            ↓
        RELEASED

    or, if recovery/expiry is required:

        RESERVED
            ↓
        EXPIRED
    """

    __tablename__ = "ai_quota_reservations"

    reservation_id = Column(
        String(64),
        primary_key=True,
        nullable=False,
    )

    tenant_id = Column(
        String(64),
        index=True,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    settled_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    status = Column(
        String(32),
        nullable=False,
        default="RESERVED",
    )

    provider = Column(
        String(64),
        nullable=False,
    )

    model = Column(
        String(128),
        nullable=False,
    )

    # ------------------------------------------------------------
    # Estimated usage reserved BEFORE provider execution
    # ------------------------------------------------------------

    estimated_input_tokens = Column(
        Integer,
        nullable=False,
        default=0,
    )

    estimated_output_tokens = Column(
        Integer,
        nullable=False,
        default=0,
    )

    estimated_token_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    estimated_cost_usd = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    estimated_request_count = Column(
        Integer,
        nullable=False,
        default=1,
    )

    # ------------------------------------------------------------
    # Actual usage settled AFTER provider execution
    # ------------------------------------------------------------

    actual_input_tokens = Column(
        Integer,
        nullable=True,
    )

    actual_output_tokens = Column(
        Integer,
        nullable=True,
    )

    actual_token_count = Column(
        Integer,
        nullable=True,
    )

    actual_cost_usd = Column(
        Float,
        nullable=True,
    )

    actual_request_count = Column(
        Integer,
        nullable=True,
    )

    # Links the final settled reservation to the usage ledger.
    ledger_record_id = Column(
        String(64),
        nullable=True,
        index=True,
    )

    # Failure/recovery provenance.
    release_reason = Column(
        String(255),
        nullable=True,
    )

    error_message = Column(
        String(2000),
        nullable=True,
    )

    __table_args__ = (
        Index(
            "ix_ai_reservation_tenant_status",
            "tenant_id",
            "status",
        ),
        Index(
            "ix_ai_reservation_tenant_created",
            "tenant_id",
            "created_at",
        ),
        Index(
            "ix_ai_reservation_tenant_expires",
            "tenant_id",
            "expires_at",
        ),
        Index(
            "ix_ai_reservation_tenant_ledger",
            "tenant_id",
            "ledger_record_id",
        ),
    )