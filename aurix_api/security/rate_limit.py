"""In-memory token-bucket rate limiter interface and FastAPI throttling dependencies for Phase 10."""

import math
import time
from typing import Callable, Dict, Optional, Tuple
from fastapi import Depends, HTTPException, status

from aurix_api.schemas.auth import TenantContext
from aurix_api.security.auth import get_current_tenant_context
from aurix_core.config.settings import settings


class TokenBucket:
    """Mathematical token-bucket rate limiter for continuous replenishment."""

    def __init__(self, capacity: float, refill_rate_per_second: float) -> None:
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate_per_second)
        self.tokens = float(capacity)
        self.last_refill_time = time.monotonic()

    def consume(self, tokens_to_consume: float = 1.0) -> Tuple[bool, float]:
        """
        Attempts to consume tokens from the bucket.
        Returns: (is_allowed: bool, retry_after_seconds: float)
        """
        now = time.monotonic()
        elapsed = max(0.0, now - self.last_refill_time)
        self.last_refill_time = now

        # Replenish tokens based on elapsed time
        self.tokens = min(self.capacity, self.tokens + (elapsed * self.refill_rate))

        if self.tokens >= tokens_to_consume:
            self.tokens -= tokens_to_consume
            return True, 0.0

        # Calculate wait time until required tokens are available
        deficit = tokens_to_consume - self.tokens
        retry_after = deficit / self.refill_rate if self.refill_rate > 0 else 60.0
        return False, math.ceil(retry_after)


class InMemoryRateLimiter:
    """Manages rate-limiting token buckets isolated by tenant and capability domain."""

    def __init__(self) -> None:
        self._buckets: Dict[str, TokenBucket] = {}

    def get_or_create_bucket(
        self,
        key: str,
        requests_per_minute: int,
    ) -> TokenBucket:
        """Retrieves or instantiates a token bucket with configured per-minute limits."""
        if key not in self._buckets:
            refill_rate = requests_per_minute / 60.0
            self._buckets[key] = TokenBucket(
                capacity=float(requests_per_minute),
                refill_rate_per_second=refill_rate,
            )
        return self._buckets[key]

    def check_rate_limit(
        self,
        tenant_id: str,
        category: str,
        requests_per_minute: int,
    ) -> Tuple[bool, float]:
        """Evaluates rate limit for a specific tenant and operational category."""
        key = f"{tenant_id}:{category}"
        bucket = self.get_or_create_bucket(key, requests_per_minute)
        return bucket.consume(1.0)


# Global singleton in-memory rate limiter instance
rate_limiter = InMemoryRateLimiter()


class RateLimitDependency:
    """FastAPI callable dependency checking tenant rate limits on route invocation."""

    def __init__(
        self,
        category: str,
        requests_per_minute: Optional[int] = None,
    ) -> None:
        self.category = category
        self.requests_per_minute = requests_per_minute

    def __call__(
        self,
        tenant_context: TenantContext = Depends(get_current_tenant_context),
    ) -> TenantContext:
        """Enforces rate limit against active tenant context, raising 429 on exhaustion."""
        limit = self.requests_per_minute or (
            settings.rate_limit_ai_requests_per_minute
            if self.category == "ai"
            else settings.rate_limit_requests_per_minute
        )

        allowed, retry_after = rate_limiter.check_rate_limit(
            tenant_id=tenant_context.tenant_id,
            category=self.category,
            requests_per_minute=limit,
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Rate limit exceeded for tenant '{tenant_context.tenant_id}'. "
                    f"Maximum {limit} requests allowed per minute for category '{self.category}'."
                ),
                headers={"Retry-After": str(int(retry_after))},
            )

        return tenant_context


def rate_limit_standard() -> Callable[[TenantContext], TenantContext]:
    """Dependency helper enforcing standard platform endpoint rate limits."""
    return RateLimitDependency(category="standard")


def rate_limit_ai() -> Callable[[TenantContext], TenantContext]:
    """Dependency helper enforcing strict AI Copilot query rate limits."""
    return RateLimitDependency(category="ai")