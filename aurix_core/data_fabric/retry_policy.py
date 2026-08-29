"""
AURIX Enterprise Data Fabric — Retry & Failure Handling Engine
Phase 19 Core Implementation.
Distinguishes retryable vs permanent errors and computes bounded exponential backoff.
"""

from __future__ import annotations

import random
from typing import Optional
from pydantic import BaseModel


class RetryDecision(BaseModel):
    """Decision model detailing retry behavior."""
    should_retry: bool
    delay_seconds: float
    error_classification: str
    is_permanent: bool
    reason: str


class RetryPolicyEngine:
    """Calculates backoff and classifies connector failure modes."""

    MAX_RETRIES = 5
    INITIAL_DELAY = 1.0
    BACKOFF_FACTOR = 2.0
    MAX_DELAY = 60.0

    @classmethod
    def classify_error(cls, exc: Exception) -> str:
        """Classify exceptions into authoritative failure domains."""
        msg = str(exc).lower()
        if "auth" in msg or "401" in msg or "403" in msg or "forbidden" in msg or "credential" in msg:
            return "AUTHENTICATION_FAILURE"
        if "429" in msg or "rate limit" in msg or "too many requests" in msg:
            return "RATE_LIMITED"
        if "timeout" in msg or "connection refused" in msg or "502" in msg or "503" in msg or "504" in msg:
            return "TRANSIENT_NETWORK_ERROR"
        if "schema" in msg or "drift" in msg or "column" in msg:
            return "SCHEMA_ERROR"
        if "duplicate" in msg or "unique constraint" in msg:
            return "DUPLICATE_KEY_ERROR"
        if "validation" in msg or "valueerror" in msg:
            return "VALIDATION_FAILURE"

        return "UNKNOWN_ERROR"

    @classmethod
    def evaluate(cls, exc: Exception, attempt: int) -> RetryDecision:
        """Evaluate if an exception is retryable and compute backoff delay."""
        error_class = cls.classify_error(exc)

        # Permanent Non-Retryable Errors
        if error_class in ("AUTHENTICATION_FAILURE", "VALIDATION_FAILURE", "SCHEMA_ERROR"):
            return RetryDecision(
                should_retry=False,
                delay_seconds=0.0,
                error_classification=error_class,
                is_permanent=True,
                reason=f"Non-retryable failure: {error_class}",
            )

        # Max retries exceeded
        if attempt >= cls.MAX_RETRIES:
            return RetryDecision(
                should_retry=False,
                delay_seconds=0.0,
                error_classification=error_class,
                is_permanent=False,
                reason=f"Max retry limit ({cls.MAX_RETRIES}) reached",
            )

        # Compute Bounded Exponential Backoff + Jitter
        delay = min(cls.MAX_DELAY, cls.INITIAL_DELAY * (cls.BACKOFF_FACTOR ** attempt))
        jitter = random.uniform(0.1, 0.5) * delay
        final_delay = round(delay + jitter, 2)

        return RetryDecision(
            should_retry=True,
            delay_seconds=final_delay,
            error_classification=error_class,
            is_permanent=False,
            reason=f"Transient failure ({error_class}). Retrying in {final_delay}s (attempt {attempt + 1}/{cls.MAX_RETRIES})",
        )
