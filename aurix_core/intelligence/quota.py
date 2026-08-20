"""Tenant-scoped AI quota, persistent usage, atomic reservation, and pricing."""

from __future__ import annotations

import logging
import math
import threading
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, cast

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from aurix_core.config.settings import settings
from aurix_core.database.models.quota import (
    AIQuotaReservation,
    AIUsageLedger,
    AIUsagePolicy,
)

logger = logging.getLogger("aurix_core.intelligence.quota")


# ============================================================
# Provider / Model Pricing
# ============================================================


class AIProviderPricing(BaseModel):
    """Provider/model-specific AI pricing configuration."""

    provider: str
    model: str
    input_price_per_1m: float
    output_price_per_1m: float
    status: str = Field(
        default="LIVE",
        description=(
            "Provider state: LIVE, OFFLINE_TEST_DOUBLE, or UNAVAILABLE."
        ),
    )


AI_PRICING_REGISTRY: Dict[str, AIProviderPricing] = {
    "GEMINI_FLASH_LITE": AIProviderPricing(
        provider="GEMINI_FLASH_LITE",
        model="gemini-2.5-flash-lite",
        input_price_per_1m=0.075,
        output_price_per_1m=0.30,
        status="LIVE",
    ),
    "GEMINI_FLASH": AIProviderPricing(
        provider="GEMINI_FLASH",
        model="gemini-2.5-flash",
        input_price_per_1m=0.15,
        output_price_per_1m=0.60,
        status="LIVE",
    ),
    "CLOUDFLARE": AIProviderPricing(
        provider="CLOUDFLARE",
        model="llama-3-8b",
        input_price_per_1m=0.10,
        output_price_per_1m=0.10,
        status="LIVE",
    ),
    "OFFLINE_TEST_DOUBLE": AIProviderPricing(
        provider="OFFLINE_TEST_DOUBLE",
        model="test-double-model",
        input_price_per_1m=0.0,
        output_price_per_1m=0.0,
        status="OFFLINE_TEST_DOUBLE",
    ),
}


# ============================================================
# Contracts
# ============================================================


class TenantAIQuotaPolicyContract(BaseModel):
    """Tenant-specific AI budget and usage policy."""

    tenant_id: str

    monthly_spend_limit_usd: float = Field(
        default=500.0,
        description="Monthly AI spend ceiling in USD.",
    )

    daily_spend_limit_usd: float = Field(
        default=50.0,
        description="Daily AI spend ceiling in USD.",
    )

    monthly_token_limit: int = Field(
        default=10_000_000,
        description="Monthly AI token ceiling.",
    )

    daily_token_limit: int = Field(
        default=1_000_000,
        description="Daily AI token ceiling.",
    )

    monthly_request_limit: int = Field(
        default=5000,
        description="Monthly AI request ceiling.",
    )

    daily_request_limit: int = Field(
        default=500,
        description="Daily AI request ceiling.",
    )

    warning_threshold_pct: float = Field(
        default=80.0,
        description="Warning threshold as percentage of monthly budget.",
    )

    is_active: bool = Field(
        default=True,
        description="Whether AI quota enforcement is active.",
    )


# Preserve existing test/import contract.
TenantAIQuotaPolicy = TenantAIQuotaPolicyContract


class TenantAIUsageRecord(BaseModel):
    """Application-level representation of a settled AI usage record."""

    record_id: str = Field(
        default_factory=lambda: (
            f"AI-USE-{uuid.uuid4().hex[:10].upper()}"
        ),
    )

    tenant_id: str

    timestamp: str = Field(
        default_factory=lambda: (
            datetime.now(timezone.utc).isoformat()
        ),
    )

    date: str
    month: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    is_fallback: bool = False
    reservation_id: Optional[str] = None


class QuotaCheckResult(BaseModel):
    """Result of a tenant quota evaluation."""

    allowed: bool

    is_warning: bool = False

    rejection_reason: Optional[str] = None

    warning_message: Optional[str] = None

    current_daily_spend_usd: float = 0.0
    current_monthly_spend_usd: float = 0.0

    current_daily_tokens: int = 0
    current_monthly_tokens: int = 0

    current_daily_requests: int = 0
    current_monthly_requests: int = 0

    reserved_spend_usd: float = 0.0
    reserved_tokens: int = 0
    reserved_requests: int = 0


class QuotaReservationResult(BaseModel):
    """Result returned when an AI budget reservation is created."""

    allowed: bool

    reservation_id: Optional[str] = None

    is_warning: bool = False

    rejection_reason: Optional[str] = None

    warning_message: Optional[str] = None

    estimated_cost_usd: float = 0.0
    estimated_tokens: int = 0
    estimated_requests: int = 0


# ============================================================
# AI Quota Manager
# ============================================================


class AIQuotaManager:
    """
    Coordinates tenant-scoped AI quotas.

    Production persistence:
        AIUsagePolicy
        AIQuotaReservation
        AIUsageLedger

    In-memory storage remains only for backwards-compatible unit tests
    and non-database execution paths. The production API path should
    always provide a database session.
    """

    _lock = threading.RLock()

    _POLICIES: Dict[str, TenantAIQuotaPolicyContract] = {}

    _USAGE_LEDGER: Dict[
        str,
        List[TenantAIUsageRecord],
    ] = {}

    _DEFAULT_RESERVATION_TTL_SECONDS = 300

    # ========================================================
    # Pricing
    # ========================================================

    @classmethod
    def _get_pricing(
        cls,
        provider: str,
        model: str,
    ) -> AIProviderPricing:
        """
        Resolve exact provider/model pricing.

        No fabricated pricing is permitted.
        """
        provider_key = provider.strip().upper()

        pricing = AI_PRICING_REGISTRY.get(provider_key)

        if pricing is None:
            raise ValueError(
                "AI pricing unavailable for provider "
                f"'{provider}'."
            )

        if pricing.status == "UNAVAILABLE":
            raise ValueError(
                "AI provider is unavailable for accounting: "
                f"{provider}."
            )

        if pricing.model != model:
            raise ValueError(
                "Configured model mismatch for provider "
                f"'{provider}': expected '{pricing.model}', "
                f"received '{model}'."
            )

        return pricing

    @classmethod
    def calculate_cost(
        cls,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """
        Calculate estimated provider cost.

        Unknown pricing is a controlled error, never a fabricated price.
        """
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError(
                "Token counts cannot be negative."
            )

        pricing = cls._get_pricing(
            provider,
            model,
        )

        cost = (
            (input_tokens / 1_000_000)
            * pricing.input_price_per_1m
        ) + (
            (output_tokens / 1_000_000)
            * pricing.output_price_per_1m
        )

        if not math.isfinite(cost) or cost < 0:
            raise ValueError(
                "Calculated AI cost is invalid."
            )

        return round(cost, 6)

    # ========================================================
    # Policy helpers
    # ========================================================

    @classmethod
    def _default_policy(
        cls,
        tenant_id: str,
    ) -> TenantAIQuotaPolicyContract:
        """Construct the configured default tenant policy."""
        return TenantAIQuotaPolicyContract(
            tenant_id=tenant_id,
            monthly_spend_limit_usd=(
                settings.ai_monthly_spend_limit_usd
            ),
            daily_spend_limit_usd=(
                settings.ai_daily_spend_limit_usd
            ),
            monthly_token_limit=(
                settings.ai_monthly_token_limit
            ),
            daily_token_limit=(
                settings.ai_daily_token_limit
            ),
            monthly_request_limit=(
                settings.ai_monthly_request_limit
            ),
            daily_request_limit=(
                settings.ai_daily_request_limit
            ),
            warning_threshold_pct=(
                settings.ai_quota_warning_pct
            ),
            is_active=True,
        )

    @classmethod
    def _policy_to_contract(
        cls,
        db_policy: AIUsagePolicy,
    ) -> TenantAIQuotaPolicyContract:
        """Convert ORM policy into the application contract."""
        return TenantAIQuotaPolicyContract(
            tenant_id=str(db_policy.tenant_id),
            monthly_spend_limit_usd=float(
                db_policy.monthly_spend_limit_usd
            ),
            daily_spend_limit_usd=float(
                db_policy.daily_spend_limit_usd
            ),
            monthly_token_limit=int(
                db_policy.monthly_token_limit
            ),
            daily_token_limit=int(
                db_policy.daily_token_limit
            ),
            monthly_request_limit=int(
                db_policy.monthly_request_limit
            ),
            daily_request_limit=int(
                db_policy.daily_request_limit
            ),
            warning_threshold_pct=float(
                db_policy.warning_threshold_pct
            ),
            is_active=bool(db_policy.is_active),
        )

    @classmethod
    def get_or_create_policy(
        cls,
        tenant_id: str,
        db: Optional[Session] = None,
    ) -> TenantAIQuotaPolicyContract:
        """
        Retrieve or create the tenant quota policy.

        When a DB session is supplied, the database is authoritative.
        The method flushes new policy state but does not commit the
        caller's broader transaction.
        """
        if db is not None:
            db_policy = (
                db.query(AIUsagePolicy)
                .filter(
                    AIUsagePolicy.tenant_id
                    == tenant_id,
                )
                .first()
            )

            if db_policy is None:
                defaults = cls._default_policy(
                    tenant_id
                )

                db_policy = AIUsagePolicy(
                    tenant_id=tenant_id,
                    monthly_spend_limit_usd=(
                        defaults.monthly_spend_limit_usd
                    ),
                    daily_spend_limit_usd=(
                        defaults.daily_spend_limit_usd
                    ),
                    monthly_token_limit=(
                        defaults.monthly_token_limit
                    ),
                    daily_token_limit=(
                        defaults.daily_token_limit
                    ),
                    monthly_request_limit=(
                        defaults.monthly_request_limit
                    ),
                    daily_request_limit=(
                        defaults.daily_request_limit
                    ),
                    warning_threshold_pct=(
                        defaults.warning_threshold_pct
                    ),
                    is_active=True,
                )

                db.add(db_policy)
                db.flush()

            return cls._policy_to_contract(
                db_policy
            )

        with cls._lock:
            if tenant_id not in cls._POLICIES:
                cls._POLICIES[tenant_id] = (
                    cls._default_policy(tenant_id)
                )

            return cls._POLICIES[
                tenant_id
            ].model_copy()

    @classmethod
    def set_policy(
        cls,
        policy: TenantAIQuotaPolicyContract,
        db: Optional[Session] = None,
    ) -> TenantAIQuotaPolicyContract:
        """
        Create/update a tenant quota policy.

        DB transactions remain owned by the caller.
        """
        if (
            policy.monthly_spend_limit_usd < 0
            or policy.daily_spend_limit_usd < 0
            or policy.monthly_token_limit < 0
            or policy.daily_token_limit < 0
            or policy.monthly_request_limit < 0
            or policy.daily_request_limit < 0
            or policy.warning_threshold_pct < 0
            or policy.warning_threshold_pct > 100
        ):
            raise ValueError(
                "Invalid AI quota policy values."
            )

        if db is not None:
            db_policy = (
                db.query(AIUsagePolicy)
                .filter(
                    AIUsagePolicy.tenant_id
                    == policy.tenant_id,
                )
                .first()
            )

            if db_policy is None:
                db_policy = AIUsagePolicy(
                    tenant_id=policy.tenant_id,
                )
                db.add(db_policy)

            db_policy.monthly_spend_limit_usd = cast(
                Any,
                policy.monthly_spend_limit_usd,
            )
            db_policy.daily_spend_limit_usd = cast(
                Any,
                policy.daily_spend_limit_usd,
            )
            db_policy.monthly_token_limit = cast(
                Any,
                policy.monthly_token_limit,
            )
            db_policy.daily_token_limit = cast(
                Any,
                policy.daily_token_limit,
            )
            db_policy.monthly_request_limit = cast(
                Any,
                policy.monthly_request_limit,
            )
            db_policy.daily_request_limit = cast(
                Any,
                policy.daily_request_limit,
            )
            db_policy.warning_threshold_pct = cast(
                Any,
                policy.warning_threshold_pct,
            )
            db_policy.is_active = cast(
                Any,
                policy.is_active,
            )

            db.flush()

            return policy.model_copy()

        with cls._lock:
            cls._POLICIES[
                policy.tenant_id
            ] = policy.model_copy()

            return cls._POLICIES[
                policy.tenant_id
            ].model_copy()

    # ========================================================
    # Usage calculations
    # ========================================================

    @classmethod
    def _db_usage_totals(
        cls,
        db: Session,
        tenant_id: str,
        current_date: str,
        current_month: str,
    ) -> Tuple[
        float,
        float,
        int,
        int,
        int,
        int,
    ]:
        """Calculate committed usage totals from the persistent ledger."""
        records = (
            db.query(AIUsageLedger)
            .filter(
                AIUsageLedger.tenant_id
                == tenant_id,
            )
            .all()
        )

        daily = [
            record
            for record in records
            if record.date_str == current_date
        ]

        monthly = [
            record
            for record in records
            if record.month_str == current_month
        ]

        daily_spend = sum(
            float(record.estimated_cost_usd)
            for record in daily
        )

        monthly_spend = sum(
            float(record.estimated_cost_usd)
            for record in monthly
        )

        daily_tokens = sum(
            int(record.input_tokens)
            + int(record.output_tokens)
            for record in daily
        )

        monthly_tokens = sum(
            int(record.input_tokens)
            + int(record.output_tokens)
            for record in monthly
        )

        daily_requests = len(daily)
        monthly_requests = len(monthly)

        return (
            daily_spend,
            monthly_spend,
            daily_tokens,
            monthly_tokens,
            daily_requests,
            monthly_requests,
        )

    @classmethod
    def _db_active_reservations(
        cls,
        db: Session,
        tenant_id: str,
    ) -> List[AIQuotaReservation]:
        """Return active non-settled reservations for one tenant."""
        return (
            db.query(AIQuotaReservation)
            .filter(
                AIQuotaReservation.tenant_id
                == tenant_id,
                AIQuotaReservation.status
                == "RESERVED",
            )
            .all()
        )

    @classmethod
    def _reservation_totals(
        cls,
        reservations: List[AIQuotaReservation],
    ) -> Tuple[float, int, int]:
        """Aggregate active reservation exposure."""
        reserved_spend = sum(
            float(
                reservation.estimated_cost_usd
            )
            for reservation in reservations
        )

        reserved_tokens = sum(
            int(
                reservation.estimated_token_count
            )
            for reservation in reservations
        )

        reserved_requests = sum(
            int(
                reservation.estimated_request_count
            )
            for reservation in reservations
        )

        return (
            reserved_spend,
            reserved_tokens,
            reserved_requests,
        )

    # ========================================================
    # Read-only quota check
    # ========================================================

    @classmethod
    def check_quota(
        cls,
        tenant_id: str,
        estimated_tokens: int = 1000,
        estimated_cost_usd: float = 0.001,
        db: Optional[Session] = None,
    ) -> QuotaCheckResult:
        """
        Evaluate whether an estimated request fits within tenant limits.

        This method is intentionally read/evaluation oriented.

        For a real provider call, use reserve_quota() immediately before
        dispatch so the budget is actually reserved.
        """
        if estimated_tokens < 0:
            raise ValueError(
                "estimated_tokens cannot be negative."
            )

        if (
            not math.isfinite(
                estimated_cost_usd
            )
            or estimated_cost_usd < 0
        ):
            raise ValueError(
                "estimated_cost_usd must be finite and non-negative."
            )

        now = datetime.now(timezone.utc)

        current_date = now.strftime(
            "%Y-%m-%d"
        )

        current_month = now.strftime(
            "%Y-%m"
        )

        if db is not None:
            policy_row = (
                db.query(AIUsagePolicy)
                .filter(
                    AIUsagePolicy.tenant_id
                    == tenant_id,
                )
                .first()
            )

            if policy_row is None:
                policy = cls.get_or_create_policy(
                    tenant_id,
                    db=db,
                )
                db.flush()
                policy_row = (
                    db.query(AIUsagePolicy)
                    .filter(
                        AIUsagePolicy.tenant_id
                        == tenant_id,
                    )
                    .first()
                )

            if policy_row is None:
                return QuotaCheckResult(
                    allowed=False,
                    rejection_reason=(
                        "AI quota policy unavailable."
                    ),
                )

            policy = cls._policy_to_contract(
                policy_row
            )

            if not policy.is_active:
                return QuotaCheckResult(
                    allowed=True,
                )

            (
                daily_spend,
                monthly_spend,
                daily_tokens,
                monthly_tokens,
                daily_requests,
                monthly_requests,
            ) = cls._db_usage_totals(
                db,
                tenant_id,
                current_date,
                current_month,
            )

            reservations = (
                cls._db_active_reservations(
                    db,
                    tenant_id,
                )
            )

            (
                reserved_spend,
                reserved_tokens,
                reserved_requests,
            ) = cls._reservation_totals(
                reservations
            )

        else:
            policy = cls.get_or_create_policy(
                tenant_id,
                db=None,
            )

            if not policy.is_active:
                return QuotaCheckResult(
                    allowed=True,
                )

            with cls._lock:
                records = cls._USAGE_LEDGER.get(
                    tenant_id,
                    [],
                )

                daily_records = [
                    record
                    for record in records
                    if record.date == current_date
                ]

                monthly_records = [
                    record
                    for record in records
                    if record.month == current_month
                ]

                daily_spend = sum(
                    record.estimated_cost_usd
                    for record in daily_records
                )

                monthly_spend = sum(
                    record.estimated_cost_usd
                    for record in monthly_records
                )

                daily_tokens = sum(
                    record.input_tokens
                    + record.output_tokens
                    for record in daily_records
                )

                monthly_tokens = sum(
                    record.input_tokens
                    + record.output_tokens
                    for record in monthly_records
                )

                daily_requests = len(
                    daily_records
                )
                monthly_requests = len(
                    monthly_records
                )

                reserved_spend = 0.0
                reserved_tokens = 0
                reserved_requests = 0

        projected_daily_spend = (
            daily_spend
            + reserved_spend
            + estimated_cost_usd
        )

        projected_monthly_spend = (
            monthly_spend
            + reserved_spend
            + estimated_cost_usd
        )

        projected_daily_tokens = (
            daily_tokens
            + reserved_tokens
            + estimated_tokens
        )

        projected_monthly_tokens = (
            monthly_tokens
            + reserved_tokens
            + estimated_tokens
        )

        projected_daily_requests = (
            daily_requests
            + reserved_requests
            + 1
        )

        projected_monthly_requests = (
            monthly_requests
            + reserved_requests
            + 1
        )

        if (
            projected_daily_spend
            > policy.daily_spend_limit_usd
        ):
            return QuotaCheckResult(
                allowed=False,
                rejection_reason=(
                    "Daily spend limit exceeded."
                ),
                current_daily_spend_usd=daily_spend,
                current_monthly_spend_usd=monthly_spend,
                current_daily_tokens=daily_tokens,
                current_monthly_tokens=monthly_tokens,
                current_daily_requests=daily_requests,
                current_monthly_requests=monthly_requests,
                reserved_spend_usd=reserved_spend,
                reserved_tokens=reserved_tokens,
                reserved_requests=reserved_requests,
            )

        if (
            projected_monthly_spend
            > policy.monthly_spend_limit_usd
        ):
            return QuotaCheckResult(
                allowed=False,
                rejection_reason=(
                    "Monthly spend limit exceeded."
                ),
                current_daily_spend_usd=daily_spend,
                current_monthly_spend_usd=monthly_spend,
                current_daily_tokens=daily_tokens,
                current_monthly_tokens=monthly_tokens,
                current_daily_requests=daily_requests,
                current_monthly_requests=monthly_requests,
                reserved_spend_usd=reserved_spend,
                reserved_tokens=reserved_tokens,
                reserved_requests=reserved_requests,
            )

        if (
            projected_daily_tokens
            > policy.daily_token_limit
        ):
            return QuotaCheckResult(
                allowed=False,
                rejection_reason=(
                    "Daily token limit exceeded."
                ),
                current_daily_spend_usd=daily_spend,
                current_monthly_spend_usd=monthly_spend,
                current_daily_tokens=daily_tokens,
                current_monthly_tokens=monthly_tokens,
                current_daily_requests=daily_requests,
                current_monthly_requests=monthly_requests,
                reserved_spend_usd=reserved_spend,
                reserved_tokens=reserved_tokens,
                reserved_requests=reserved_requests,
            )

        if (
            projected_monthly_tokens
            > policy.monthly_token_limit
        ):
            return QuotaCheckResult(
                allowed=False,
                rejection_reason=(
                    "Monthly token limit exceeded."
                ),
                current_daily_spend_usd=daily_spend,
                current_monthly_spend_usd=monthly_spend,
                current_daily_tokens=daily_tokens,
                current_monthly_tokens=monthly_tokens,
                current_daily_requests=daily_requests,
                current_monthly_requests=monthly_requests,
                reserved_spend_usd=reserved_spend,
                reserved_tokens=reserved_tokens,
                reserved_requests=reserved_requests,
            )

        if (
            projected_daily_requests
            > policy.daily_request_limit
        ):
            return QuotaCheckResult(
                allowed=False,
                rejection_reason=(
                    "Daily request limit exceeded."
                ),
                current_daily_spend_usd=daily_spend,
                current_monthly_spend_usd=monthly_spend,
                current_daily_tokens=daily_tokens,
                current_monthly_tokens=monthly_tokens,
                current_daily_requests=daily_requests,
                current_monthly_requests=monthly_requests,
                reserved_spend_usd=reserved_spend,
                reserved_tokens=reserved_tokens,
                reserved_requests=reserved_requests,
            )

        if (
            projected_monthly_requests
            > policy.monthly_request_limit
        ):
            return QuotaCheckResult(
                allowed=False,
                rejection_reason=(
                    "Monthly request limit exceeded."
                ),
                current_daily_spend_usd=daily_spend,
                current_monthly_spend_usd=monthly_spend,
                current_daily_tokens=daily_tokens,
                current_monthly_tokens=monthly_tokens,
                current_daily_requests=daily_requests,
                current_monthly_requests=monthly_requests,
                reserved_spend_usd=reserved_spend,
                reserved_tokens=reserved_tokens,
                reserved_requests=reserved_requests,
            )

        spend_ratio = (
            (
                projected_monthly_spend
                / max(
                    policy.monthly_spend_limit_usd,
                    0.000001,
                )
            )
            * 100.0
        )

        is_warning = (
            spend_ratio
            >= policy.warning_threshold_pct
        )

        warning_message: Optional[str] = None

        if is_warning:
            warning_message = (
                "Warning: Tenant AI consumption has "
                f"reached {spend_ratio:.1f}% of monthly budget."
            )

        return QuotaCheckResult(
            allowed=True,
            is_warning=is_warning,
            warning_message=warning_message,
            current_daily_spend_usd=round(
                daily_spend,
                6,
            ),
            current_monthly_spend_usd=round(
                monthly_spend,
                6,
            ),
            current_daily_tokens=daily_tokens,
            current_monthly_tokens=monthly_tokens,
            current_daily_requests=daily_requests,
            current_monthly_requests=monthly_requests,
            reserved_spend_usd=round(
                reserved_spend,
                6,
            ),
            reserved_tokens=reserved_tokens,
            reserved_requests=reserved_requests,
        )

    # ========================================================
    # Atomic reservation
    # ========================================================

    @classmethod
    def reserve_quota(
        cls,
        tenant_id: str,
        provider: str,
        model: str,
        estimated_input_tokens: int,
        estimated_output_tokens: int,
        estimated_cost_usd: Optional[float] = None,
        db: Optional[Session] = None,
        ttl_seconds: int = _DEFAULT_RESERVATION_TTL_SECONDS,
    ) -> QuotaReservationResult:
        """
        Reserve AI budget before an external provider call.

        Database-backed execution:
            - locks the tenant policy row with SELECT FOR UPDATE
            - evaluates committed usage + active reservations
            - creates a durable reservation
            - increments reservation exposure on the policy row
            - flushes but does not commit the caller's broader transaction

        The caller must ensure the reservation transaction is committed
        before performing a potentially long-running external provider call.
        """
        if db is None:
            raise ValueError(
                "Persistent AI quota reservation requires a database session."
            )

        if (
            estimated_input_tokens < 0
            or estimated_output_tokens < 0
        ):
            raise ValueError(
                "Estimated token counts cannot be negative."
            )

        estimated_tokens = (
            estimated_input_tokens
            + estimated_output_tokens
        )

        cost = (
            cls.calculate_cost(
                provider,
                model,
                estimated_input_tokens,
                estimated_output_tokens,
            )
            if estimated_cost_usd is None
            else estimated_cost_usd
        )

        if not math.isfinite(cost) or cost < 0:
            raise ValueError(
                "Estimated AI cost must be finite and non-negative."
            )

        if ttl_seconds <= 0:
            raise ValueError(
                "Reservation TTL must be positive."
            )

        now = datetime.now(timezone.utc)

        expires_at = (
            now
            + timedelta(
                seconds=ttl_seconds
            )
        )

        current_date = now.strftime(
            "%Y-%m-%d"
        )

        current_month = now.strftime(
            "%Y-%m"
        )

        # Ensure row exists before locking.
        cls.get_or_create_policy(
            tenant_id,
            db=db,
        )

        policy_row = (
            db.query(AIUsagePolicy)
            .filter(
                AIUsagePolicy.tenant_id
                == tenant_id,
            )
            .with_for_update()
            .one()
        )

        policy = cls._policy_to_contract(
            policy_row
        )

        if not policy.is_active:
            return QuotaReservationResult(
                allowed=True,
                reservation_id=None,
                estimated_cost_usd=cost,
                estimated_tokens=estimated_tokens,
            )

        (
            daily_spend,
            monthly_spend,
            daily_tokens,
            monthly_tokens,
            daily_requests,
            monthly_requests,
        ) = cls._db_usage_totals(
            db,
            tenant_id,
            current_date,
            current_month,
        )

        active_reservations = (
            cls._db_active_reservations(
                db,
                tenant_id,
            )
        )

        (
            reserved_spend,
            reserved_tokens,
            reserved_requests,
        ) = cls._reservation_totals(
            active_reservations
        )

        projected_daily_spend = (
            daily_spend
            + reserved_spend
            + cost
        )

        projected_monthly_spend = (
            monthly_spend
            + reserved_spend
            + cost
        )

        projected_daily_tokens = (
            daily_tokens
            + reserved_tokens
            + estimated_tokens
        )

        projected_monthly_tokens = (
            monthly_tokens
            + reserved_tokens
            + estimated_tokens
        )

        projected_daily_requests = (
            daily_requests
            + reserved_requests
            + 1
        )

        projected_monthly_requests = (
            monthly_requests
            + reserved_requests
            + 1
        )

        rejection_reason: Optional[str] = None

        if (
            projected_daily_spend
            > policy.daily_spend_limit_usd
        ):
            rejection_reason = (
                "Daily spend limit exceeded."
            )
        elif (
            projected_monthly_spend
            > policy.monthly_spend_limit_usd
        ):
            rejection_reason = (
                "Monthly spend limit exceeded."
            )
        elif (
            projected_daily_tokens
            > policy.daily_token_limit
        ):
            rejection_reason = (
                "Daily token limit exceeded."
            )
        elif (
            projected_monthly_tokens
            > policy.monthly_token_limit
        ):
            rejection_reason = (
                "Monthly token limit exceeded."
            )
        elif (
            projected_daily_requests
            > policy.daily_request_limit
        ):
            rejection_reason = (
                "Daily request limit exceeded."
            )
        elif (
            projected_monthly_requests
            > policy.monthly_request_limit
        ):
            rejection_reason = (
                "Monthly request limit exceeded."
            )

        if rejection_reason is not None:
            db.rollback()
            return QuotaReservationResult(
                allowed=False,
                rejection_reason=rejection_reason,
                estimated_cost_usd=cost,
                estimated_tokens=estimated_tokens,
            )

        spend_ratio = (
            (
                projected_monthly_spend
                / max(
                    policy.monthly_spend_limit_usd,
                    0.000001,
                )
            )
            * 100.0
        )

        is_warning = (
            spend_ratio
            >= policy.warning_threshold_pct
        )

        warning_message: Optional[str] = None

        if is_warning:
            warning_message = (
                "Warning: Tenant AI consumption has "
                f"reached {spend_ratio:.1f}% of monthly budget."
            )

        reservation_id = (
            f"AI-RES-{uuid.uuid4().hex[:12].upper()}"
        )

        reservation = AIQuotaReservation(
            reservation_id=reservation_id,
            tenant_id=tenant_id,
            created_at=now,
            expires_at=expires_at,
            status="RESERVED",
            provider=provider,
            model=model,
            estimated_input_tokens=(
                estimated_input_tokens
            ),
            estimated_output_tokens=(
                estimated_output_tokens
            ),
            estimated_token_count=estimated_tokens,
            estimated_cost_usd=cost,
            estimated_request_count=1,
        )

        db.add(reservation)

        policy_row.reserved_spend_usd = cast(
            Any,
            float(
                policy_row.reserved_spend_usd
            )
            + cost,
        )

        policy_row.reserved_token_count = cast(
            Any,
            int(
                policy_row.reserved_token_count
            )
            + estimated_tokens,
        )

        policy_row.reserved_request_count = cast(
            Any,
            int(
                policy_row.reserved_request_count
            )
            + 1,
        )

        db.flush()

        return QuotaReservationResult(
            allowed=True,
            reservation_id=reservation_id,
            is_warning=is_warning,
            warning_message=warning_message,
            estimated_cost_usd=cost,
            estimated_tokens=estimated_tokens,
            estimated_requests=1,
        )

    # ========================================================
    # Reservation settlement
    # ========================================================

    @classmethod
    def settle_reservation(
        cls,
        reservation_id: str,
        input_tokens: int,
        output_tokens: int,
        estimated_cost_usd: Optional[float] = None,
        is_fallback: bool = False,
        db: Optional[Session] = None,
    ) -> TenantAIUsageRecord:
        """
        Settle a previously reserved AI request.

        The reservation is locked and its reserved exposure is removed.
        Actual usage is persisted into AIUsageLedger.
        """
        if db is None:
            raise ValueError(
                "Reservation settlement requires a database session."
            )

        if input_tokens < 0 or output_tokens < 0:
            raise ValueError(
                "Actual token counts cannot be negative."
            )

        reservation = (
            db.query(AIQuotaReservation)
            .filter(
                AIQuotaReservation.reservation_id
                == reservation_id,
            )
            .with_for_update()
            .one_or_none()
        )

        if reservation is None:
            raise ValueError(
                f"AI reservation '{reservation_id}' was not found."
            )

        if reservation.status == "SETTLED":
            existing = (
                db.query(AIUsageLedger)
                .filter(
                    AIUsageLedger.tenant_id
                    == reservation.tenant_id,
                    AIUsageLedger.reservation_id
                    == reservation_id,
                )
                .first()
            )

            if existing is not None:
                return TenantAIUsageRecord(
                    record_id=str(
                        existing.record_id
                    ),
                    tenant_id=str(
                        existing.tenant_id
                    ),
                    date=str(
                        existing.date_str
                    ),
                    month=str(
                        existing.month_str
                    ),
                    provider=str(
                        existing.provider
                    ),
                    model=str(
                        existing.model
                    ),
                    input_tokens=int(
                        existing.input_tokens
                    ),
                    output_tokens=int(
                        existing.output_tokens
                    ),
                    estimated_cost_usd=float(
                        existing.estimated_cost_usd
                    ),
                    is_fallback=bool(
                        existing.is_fallback
                    ),
                    reservation_id=str(
                        reservation_id
                    ),
                )

            raise ValueError(
                "Reservation is marked SETTLED but its usage ledger "
                "entry is missing."
            )

        if reservation.status != "RESERVED":
            raise ValueError(
                "Reservation cannot be settled from status "
                f"'{reservation.status}'."
            )

        actual_cost = (
            cls.calculate_cost(
                str(reservation.provider),
                str(reservation.model),
                input_tokens,
                output_tokens,
            )
            if estimated_cost_usd is None
            else estimated_cost_usd
        )

        if (
            not math.isfinite(
                actual_cost
            )
            or actual_cost < 0
        ):
            raise ValueError(
                "Actual AI cost must be finite and non-negative."
            )

        policy_row = (
            db.query(AIUsagePolicy)
            .filter(
                AIUsagePolicy.tenant_id
                == reservation.tenant_id,
            )
            .with_for_update()
            .one()
        )

        now = datetime.now(timezone.utc)

        record_id = (
            f"AI-USE-{uuid.uuid4().hex[:10].upper()}"
        )

        ledger_entry = AIUsageLedger(
            record_id=record_id,
            tenant_id=str(
                reservation.tenant_id
            ),
            timestamp=now,
            date_str=now.strftime("%Y-%m-%d"),
            month_str=now.strftime("%Y-%m"),
            provider=str(
                reservation.provider
            ),
            model=str(
                reservation.model
            ),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=actual_cost,
            is_fallback=is_fallback,
            reservation_id=reservation_id,
            status="SETTLED",
        )

        db.add(ledger_entry)

        policy_row.reserved_spend_usd = cast(
            Any,
            max(
                0.0,
                float(
                    policy_row.reserved_spend_usd
                )
                - float(
                    reservation.estimated_cost_usd
                ),
            ),
        )

        policy_row.reserved_token_count = cast(
            Any,
            max(
                0,
                int(
                    policy_row.reserved_token_count
                )
                - int(
                    reservation.estimated_token_count
                ),
            ),
        )

        policy_row.reserved_request_count = cast(
            Any,
            max(
                0,
                int(
                    policy_row.reserved_request_count
                )
                - int(
                    reservation.estimated_request_count
                ),
            ),
        )

        reservation.status = cast(
            Any,
            "SETTLED",
        )

        reservation.settled_at = cast(
            Any,
            now,
        )

        reservation.actual_input_tokens = cast(
            Any,
            input_tokens,
        )

        reservation.actual_output_tokens = cast(
            Any,
            output_tokens,
        )

        reservation.actual_token_count = cast(
            Any,
            input_tokens + output_tokens,
        )

        reservation.actual_cost_usd = cast(
            Any,
            actual_cost,
        )

        reservation.actual_request_count = cast(
            Any,
            1,
        )

        reservation.ledger_record_id = cast(
            Any,
            record_id,
        )

        db.flush()

        logger.info(
            "Settled AI reservation [%s] for tenant [%s]: $%.6f",
            reservation_id,
            reservation.tenant_id,
            actual_cost,
        )

        return TenantAIUsageRecord(
            record_id=record_id,
            tenant_id=str(
                reservation.tenant_id
            ),
            timestamp=now.isoformat(),
            date=now.strftime("%Y-%m-%d"),
            month=now.strftime("%Y-%m"),
            provider=str(
                reservation.provider
            ),
            model=str(
                reservation.model
            ),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=actual_cost,
            is_fallback=is_fallback,
            reservation_id=reservation_id,
        )

    # ========================================================
    # Reservation release
    # ========================================================

    @classmethod
    def release_reservation(
        cls,
        reservation_id: str,
        reason: str,
        db: Optional[Session] = None,
    ) -> None:
        """Release an unused AI reservation safely."""
        if db is None:
            raise ValueError(
                "Reservation release requires a database session."
            )

        reservation = (
            db.query(AIQuotaReservation)
            .filter(
                AIQuotaReservation.reservation_id
                == reservation_id,
            )
            .with_for_update()
            .one_or_none()
        )

        if reservation is None:
            raise ValueError(
                f"AI reservation '{reservation_id}' was not found."
            )

        if reservation.status != "RESERVED":
            return

        policy_row = (
            db.query(AIUsagePolicy)
            .filter(
                AIUsagePolicy.tenant_id
                == reservation.tenant_id,
            )
            .with_for_update()
            .one()
        )

        policy_row.reserved_spend_usd = cast(
            Any,
            max(
                0.0,
                float(
                    policy_row.reserved_spend_usd
                )
                - float(
                    reservation.estimated_cost_usd
                ),
            ),
        )

        policy_row.reserved_token_count = cast(
            Any,
            max(
                0,
                int(
                    policy_row.reserved_token_count
                )
                - int(
                    reservation.estimated_token_count
                ),
            ),
        )

        policy_row.reserved_request_count = cast(
            Any,
            max(
                0,
                int(
                    policy_row.reserved_request_count
                )
                - int(
                    reservation.estimated_request_count
                ),
            ),
        )

        reservation.status = cast(
            Any,
            "RELEASED",
        )

        reservation.settled_at = cast(
            Any,
            datetime.now(timezone.utc),
        )

        reservation.release_reason = cast(
            Any,
            reason,
        )

        db.flush()

        logger.info(
            "Released AI reservation [%s] for tenant [%s]: %s",
            reservation_id,
            reservation.tenant_id,
            reason,
        )

    # ========================================================
    # Expired reservation cleanup
    # ========================================================

    @classmethod
    def expire_reservations(
        cls,
        db: Optional[Session] = None,
        now: Optional[datetime] = None,
    ) -> int:
        """
        Release expired RESERVED records.

        This is intentionally deterministic and tenant-scoped.
        """
        if db is None:
            raise ValueError(
                "Reservation expiry requires a database session."
            )

        current_time = (
            now
            if now is not None
            else datetime.now(timezone.utc)
        )

        reservations = (
            db.query(AIQuotaReservation)
            .filter(
                AIQuotaReservation.status
                == "RESERVED",
                AIQuotaReservation.expires_at
                <= current_time,
            )
            .with_for_update()
            .all()
        )

        expired_count = 0

        for reservation in reservations:
            cls.release_reservation(
                reservation_id=str(
                    reservation.reservation_id
                ),
                reason="RESERVATION_EXPIRED",
                db=db,
            )
            reservation.status = cast(
                Any,
                "EXPIRED",
            )
            expired_count += 1

        db.flush()

        return expired_count

    # ========================================================
    # Backwards-compatible direct usage recording
    # ========================================================

    @classmethod
    def record_usage(
        cls,
        tenant_id: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        estimated_cost_usd: Optional[float] = None,
        is_fallback: bool = False,
        db: Optional[Session] = None,
        reservation_id: Optional[str] = None,
    ) -> TenantAIUsageRecord:
        """
        Record completed AI usage.

        Production provider calls should use:
            reserve_quota()
            provider call
            settle_reservation()

        This direct method remains for compatibility with existing
        unit tests and already-implemented code paths.
        """
        if reservation_id is not None:
            return cls.settle_reservation(
                reservation_id=reservation_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost_usd=estimated_cost_usd,
                is_fallback=is_fallback,
                db=db,
            )

        now = datetime.now(timezone.utc)

        cost = (
            cls.calculate_cost(
                provider,
                model,
                input_tokens,
                output_tokens,
            )
            if estimated_cost_usd is None
            else estimated_cost_usd
        )

        if not math.isfinite(cost) or cost < 0:
            raise ValueError(
                "AI cost must be finite and non-negative."
            )

        record_id = (
            f"AI-USE-{uuid.uuid4().hex[:10].upper()}"
        )

        if db is not None:
            ledger_entry = AIUsageLedger(
                record_id=record_id,
                tenant_id=tenant_id,
                timestamp=now,
                date_str=now.strftime("%Y-%m-%d"),
                month_str=now.strftime("%Y-%m"),
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost_usd=cost,
                is_fallback=is_fallback,
                reservation_id=None,
                status="SETTLED",
            )

            db.add(ledger_entry)
            db.flush()

            logger.info(
                "Recorded persistent AI usage for tenant [%s]: $%.6f",
                tenant_id,
                cost,
            )

            return TenantAIUsageRecord(
                record_id=record_id,
                tenant_id=tenant_id,
                timestamp=now.isoformat(),
                date=now.strftime("%Y-%m-%d"),
                month=now.strftime("%Y-%m"),
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost_usd=cost,
                is_fallback=is_fallback,
            )

        record = TenantAIUsageRecord(
            record_id=record_id,
            tenant_id=tenant_id,
            date=now.strftime("%Y-%m-%d"),
            month=now.strftime("%Y-%m"),
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=cost,
            is_fallback=is_fallback,
        )

        with cls._lock:
            cls._USAGE_LEDGER.setdefault(
                tenant_id,
                [],
            ).append(record)

        return record

    # ========================================================
    # Usage summary
    # ========================================================

    @classmethod
    def get_tenant_usage_summary(
        cls,
        tenant_id: str,
        target_date: Optional[str] = None,
        target_month: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Return tenant usage, limits, reservations, and remaining budget."""
        now = datetime.now(timezone.utc)

        filter_date = (
            target_date
            or now.strftime("%Y-%m-%d")
        )

        filter_month = (
            target_month
            or now.strftime("%Y-%m")
        )

        policy = cls.get_or_create_policy(
            tenant_id,
            db=db,
        )

        if db is not None:
            (
                daily_spend,
                monthly_spend,
                daily_tokens,
                monthly_tokens,
                daily_requests,
                monthly_requests,
            ) = cls._db_usage_totals(
                db,
                tenant_id,
                filter_date,
                filter_month,
            )

            reservations = (
                cls._db_active_reservations(
                    db,
                    tenant_id,
                )
            )

            (
                reserved_spend,
                reserved_tokens,
                reserved_requests,
            ) = cls._reservation_totals(
                reservations
            )

        else:
            with cls._lock:
                records = cls._USAGE_LEDGER.get(
                    tenant_id,
                    [],
                )

                daily_records = [
                    record
                    for record in records
                    if record.date == filter_date
                ]

                monthly_records = [
                    record
                    for record in records
                    if record.month == filter_month
                ]

                daily_spend = sum(
                    record.estimated_cost_usd
                    for record in daily_records
                )

                monthly_spend = sum(
                    record.estimated_cost_usd
                    for record in monthly_records
                )

                daily_tokens = sum(
                    record.input_tokens
                    + record.output_tokens
                    for record in daily_records
                )

                monthly_tokens = sum(
                    record.input_tokens
                    + record.output_tokens
                    for record in monthly_records
                )

                daily_requests = len(
                    daily_records
                )

                monthly_requests = len(
                    monthly_records
                )

                reserved_spend = 0.0
                reserved_tokens = 0
                reserved_requests = 0

        return {
            "tenant_id": tenant_id,
            "period_date": filter_date,
            "period_month": filter_month,
            "daily_spend_usd": round(
                daily_spend,
                6,
            ),
            "monthly_spend_usd": round(
                monthly_spend,
                6,
            ),
            "monthly_spend_limit_usd": (
                policy.monthly_spend_limit_usd
            ),
            "daily_spend_limit_usd": (
                policy.daily_spend_limit_usd
            ),
            "daily_tokens": daily_tokens,
            "monthly_tokens": monthly_tokens,
            "daily_token_limit": (
                policy.daily_token_limit
            ),
            "monthly_token_limit": (
                policy.monthly_token_limit
            ),
            "daily_requests": daily_requests,
            "monthly_requests": monthly_requests,
            "daily_request_limit": (
                policy.daily_request_limit
            ),
            "monthly_request_limit": (
                policy.monthly_request_limit
            ),
            "reserved_spend_usd": round(
                reserved_spend,
                6,
            ),
            "reserved_tokens": reserved_tokens,
            "reserved_requests": reserved_requests,
            "remaining_monthly_spend_usd": max(
                0.0,
                policy.monthly_spend_limit_usd
                - monthly_spend
                - reserved_spend,
            ),
            "remaining_daily_spend_usd": max(
                0.0,
                policy.daily_spend_limit_usd
                - daily_spend
                - reserved_spend,
            ),
            "remaining_monthly_tokens": max(
                0,
                policy.monthly_token_limit
                - monthly_tokens
                - reserved_tokens,
            ),
            "remaining_daily_tokens": max(
                0,
                policy.daily_token_limit
                - daily_tokens
                - reserved_tokens,
            ),
            "remaining_monthly_requests": max(
                0,
                policy.monthly_request_limit
                - monthly_requests
                - reserved_requests,
            ),
            "remaining_daily_requests": max(
                0,
                policy.daily_request_limit
                - daily_requests
                - reserved_requests,
            ),
            "fallback_requests": (
                sum(
                    1
                    for record in monthly_records
                    if record.is_fallback
                )
                if db is None
                else sum(
                    1
                    for record in (
                        db.query(
                            AIUsageLedger
                        )
                        .filter(
                            AIUsageLedger.tenant_id
                            == tenant_id,
                            AIUsageLedger.month_str
                            == filter_month,
                        )
                        .all()
                    )
                    if bool(record.is_fallback)
                )
            ),
            "policy": policy.model_dump(),
        }

    # ========================================================
    # Test / maintenance reset
    # ========================================================

    @classmethod
    def reset_usage_ledger(
        cls,
        tenant_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> None:
        """
        Clear usage/reservations for maintenance and test isolation.

        Production operational paths should not use this method.
        """
        if db is not None:
            ledger_query = db.query(
                AIUsageLedger
            )

            reservation_query = db.query(
                AIQuotaReservation
            )

            policy_query = db.query(
                AIUsagePolicy
            )

            if tenant_id is not None:
                ledger_query = ledger_query.filter(
                    AIUsageLedger.tenant_id
                    == tenant_id
                )

                reservation_query = (
                    reservation_query.filter(
                        AIQuotaReservation.tenant_id
                        == tenant_id
                    )
                )

                policy_query = policy_query.filter(
                    AIUsagePolicy.tenant_id
                    == tenant_id
                )

            ledger_query.delete(
                synchronize_session=False
            )

            reservation_query.delete(
                synchronize_session=False
            )

            policies = policy_query.all()

            for policy in policies:
                policy.reserved_spend_usd = cast(
                    Any,
                    0.0,
                )
                policy.reserved_token_count = cast(
                    Any,
                    0,
                )
                policy.reserved_request_count = cast(
                    Any,
                    0,
                )

            db.flush()
            return

        with cls._lock:
            if tenant_id is not None:
                cls._USAGE_LEDGER.pop(
                    tenant_id,
                    None
                )
            else:
                cls._USAGE_LEDGER.clear()

    # ========================================================
    # Convenience helpers
    # ========================================================

    @classmethod
    def get_pricing(
        cls,
        provider: str,
        model: str,
    ) -> AIProviderPricing:
        """Expose validated provider/model pricing to other services."""
        return cls._get_pricing(
            provider,
            model,
        )

    @classmethod
    def is_provider_live(
        cls,
        provider: str,
        model: str,
    ) -> bool:
        """Return whether provider pricing/configuration is marked LIVE."""
        pricing = cls._get_pricing(
            provider,
            model,
        )

        return pricing.status == "LIVE"