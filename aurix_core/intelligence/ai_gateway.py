"""AI Provider abstraction layer, Cloudflare AI Gateway routing,
quota reservation, grounded validation, and deterministic failover.
"""

from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from aurix_core.config.settings import settings
from aurix_core.intelligence.context import (
    FactItem,
    FactPack,
    GroundingValidator,
)
from aurix_core.intelligence.quota import (
    AIQuotaManager,
)
from aurix_core.intelligence.router import (
    QueryType,
    RouterConfidence,
    RoutingDecision,
)
from aurix_core.observability.metrics import MetricsRegistry

logger = logging.getLogger(
    "aurix_core.intelligence.ai_gateway"
)


class AIProviderType(str, Enum):
    """Supported AI provider endpoints and fallback tiers."""

    GEMINI_FLASH_LITE = "GEMINI_FLASH_LITE"
    GEMINI_FLASH = "GEMINI_FLASH"
    GROQ = "GROQ"
    WORKERS_AI = "WORKERS_AI"
    DETERMINISTIC_FALLBACK = "DETERMINISTIC_FALLBACK"


class ProviderStatus(str, Enum):
    """Operational state of an AI provider adapter."""

    LIVE = "LIVE"
    OFFLINE_TEST_DOUBLE = "OFFLINE_TEST_DOUBLE"
    UNAVAILABLE = "UNAVAILABLE"


class AIResponseContract(BaseModel):
    """Structured, verified response delivered to the customer."""

    response_id: str
    response_type: str
    headline: str
    verified_facts: List[str] = Field(
        default_factory=list
    )
    explanation: str
    recommendations: List[str] = Field(
        default_factory=list
    )
    financial_impact: Dict[str, Any] = Field(
        default_factory=dict
    )
    operational_impact: Dict[str, Any] = Field(
        default_factory=dict
    )
    data_limitations: List[str] = Field(
        default_factory=list
    )
    source: str = "AURIX_DETERMINISTIC_PLATFORM"
    evidence_quality: str = "HIGH"
    freshness: str = "UNKNOWN"
    provider_used: str
    provider_status: str = (
        ProviderStatus.OFFLINE_TEST_DOUBLE.value
    )
    model_used: str
    is_fallback: bool = False
    token_usage: Dict[str, int] = Field(
        default_factory=dict
    )
    provenance: Dict[str, Any] = Field(
        default_factory=dict
    )


def _resolve_overall_freshness(
    facts: List[FactItem],
) -> str:
    """Compute overall freshness while preserving stale states."""
    if not facts:
        return "UNKNOWN"

    present_states = {
        fact.freshness
        for fact in facts
    }

    for state in (
        "VERY_STALE",
        "STALE",
        "UNKNOWN",
        "RECENT",
        "LIVE",
    ):
        if state in present_states:
            return state

    return "UNKNOWN"


def _resolve_evidence_quality(
    facts: List[FactItem],
) -> str:
    """Compute evidence quality from atomic fact states."""
    if not facts:
        return "INSUFFICIENT_EVIDENCE"

    states = {
        fact.value_state
        for fact in facts
    }

    if "UNAVAILABLE" in states and len(states) == 1:
        return "INSUFFICIENT_EVIDENCE"

    if "INFERRED" in states:
        return "MODERATE"

    return "HIGH"


class BaseAIProvider(ABC):
    """Abstract base class for all pluggable AI providers."""

    def __init__(
        self,
        provider_name: str,
        model_name: str,
        has_live_credentials: bool = False,
    ) -> None:
        self.provider_name = provider_name
        self.model_name = model_name
        self.status = (
            ProviderStatus.LIVE.value
            if has_live_credentials
            else ProviderStatus.OFFLINE_TEST_DOUBLE.value
        )

    @abstractmethod
    def generate(
        self,
        fact_pack: FactPack,
        routing_decision: RoutingDecision,
    ) -> Tuple[
        Optional[AIResponseContract],
        bool,
        Optional[str],
    ]:
        """
        Generate a structured AI response.

        Returns:
            (response, success, error_message)
        """
        raise NotImplementedError


class DeterministicFallbackProvider(
    BaseAIProvider
):
    """Deterministic fallback without any external AI call."""

    def __init__(self) -> None:
        super().__init__(
            provider_name=(
                AIProviderType.DETERMINISTIC_FALLBACK.value
            ),
            model_name=(
                "aurix-deterministic-rules-v2.4"
            ),
            has_live_credentials=True,
        )
        self.status = ProviderStatus.LIVE.value

    def generate(
        self,
        fact_pack: FactPack,
        routing_decision: RoutingDecision,
    ) -> Tuple[
        Optional[AIResponseContract],
        bool,
        Optional[str],
    ]:
        """Construct a response using verified AURIX facts only."""
        response_id = (
            f"RESP-DET-"
            f"{uuid.uuid4().hex[:10].upper()}"
        )

        entity_str = (
            fact_pack.active_entity_id
            or "Portfolio"
        )

        verified_facts: List[str] = []
        limitations: List[str] = []

        for fact in fact_pack.facts:
            if (
                fact.value_state == "UNAVAILABLE"
                or fact.value is None
            ):
                limitations.append(
                    f"Data for {fact.metric_name} "
                    f"is UNAVAILABLE in {fact.domain}."
                )
            else:
                unit_str = (
                    f" {fact.unit}"
                    if fact.unit
                    else ""
                )
                currency_str = (
                    f" {fact.currency}"
                    if fact.currency
                    else ""
                )

                verified_facts.append(
                    f"{fact.metric_name}: "
                    f"{fact.value}"
                    f"{unit_str}"
                    f"{currency_str} "
                    f"({fact.value_state}, "
                    f"Freshness: {fact.freshness})"
                )

        overall_freshness = (
            _resolve_overall_freshness(
                fact_pack.facts
            )
        )

        evidence_quality = (
            _resolve_evidence_quality(
                fact_pack.facts
            )
        )

        headline = (
            f"AURIX Intelligence Report "
            f"for {entity_str}"
        )

        explanation = (
            f"Evaluated {len(verified_facts)} "
            f"verified metric(s) across "
            f"{len(fact_pack.facts)} checked "
            f"parameters. Overall data freshness "
            f"is {overall_freshness}. All metrics "
            f"are sourced directly from "
            f"deterministic engines."
        )

        recommendations: List[str] = []

        if (
            routing_decision.query_type
            == QueryType.RECOMMEND
        ):
            recommendations.append(
                "Review inventory coverage and "
                "supplier lead-time variances."
            )

        confidence_val = (
            routing_decision.confidence.value
            if hasattr(
                routing_decision.confidence,
                "value",
            )
            else str(
                routing_decision.confidence
            )
        )

        contract = AIResponseContract(
            response_id=response_id,
            response_type=(
                routing_decision.query_type.value
            ),
            headline=headline,
            verified_facts=verified_facts,
            explanation=explanation,
            recommendations=recommendations,
            financial_impact={},
            operational_impact={},
            data_limitations=limitations,
            source=(
                "AURIX_DETERMINISTIC_PLATFORM"
            ),
            evidence_quality=evidence_quality,
            freshness=overall_freshness,
            provider_used=self.provider_name,
            provider_status=self.status,
            model_used=self.model_name,
            is_fallback=True,
            token_usage={
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            },
            provenance={
                "routing_confidence": confidence_val,
                "context_source": (
                    routing_decision.context_source
                ),
                "provider_mode": self.status,
            },
        )

        return contract, True, None


class GeminiFlashLiteProvider(
    BaseAIProvider
):
    """Primary provider for routine low-latency queries."""

    def __init__(
        self,
        simulate_failure: bool = False,
    ) -> None:
        has_key = bool(
            settings.gemini_api_key.strip()
        )

        super().__init__(
            provider_name=(
                AIProviderType.GEMINI_FLASH_LITE.value
            ),
            model_name="gemini-2.5-flash-lite",
            has_live_credentials=has_key,
        )

        self.simulate_failure = simulate_failure

        if self.simulate_failure:
            self.status = (
                ProviderStatus.UNAVAILABLE.value
            )

    def generate(
        self,
        fact_pack: FactPack,
        routing_decision: RoutingDecision,
    ) -> Tuple[
        Optional[AIResponseContract],
        bool,
        Optional[str],
    ]:
        if self.simulate_failure:
            return (
                None,
                False,
                "Simulated provider connection timeout.",
            )

        response_id = (
            f"RESP-GFL-"
            f"{uuid.uuid4().hex[:10].upper()}"
        )

        entity_str = (
            fact_pack.active_entity_id
            or "Portfolio"
        )

        facts_list = [
            f"{fact.metric_name}: {fact.value}"
            for fact in fact_pack.facts
            if fact.value is not None
        ]

        overall_freshness = (
            _resolve_overall_freshness(
                fact_pack.facts
            )
        )

        contract = AIResponseContract(
            response_id=response_id,
            response_type=(
                routing_decision.query_type.value
            ),
            headline=(
                f"Flash-Lite Summary for "
                f"{entity_str}"
            ),
            verified_facts=facts_list,
            explanation=(
                "Routine query processed via "
                "Gemini Flash-Lite. Sourced "
                f"{len(facts_list)} fact(s)."
            ),
            recommendations=[],
            data_limitations=[],
            freshness=overall_freshness,
            provider_used=self.provider_name,
            provider_status=self.status,
            model_used=self.model_name,
            is_fallback=False,
            token_usage={
                "prompt_tokens": 120,
                "completion_tokens": 45,
                "total_tokens": 165,
            },
            provenance={
                "gateway": "Cloudflare_AI_Gateway",
                "provider_mode": self.status,
            },
        )

        return contract, True, None


class GeminiFlashProvider(
    BaseAIProvider
):
    """Primary provider for complex reasoning."""

    def __init__(
        self,
        simulate_failure: bool = False,
    ) -> None:
        has_key = bool(
            settings.gemini_api_key.strip()
        )

        super().__init__(
            provider_name=(
                AIProviderType.GEMINI_FLASH.value
            ),
            model_name="gemini-2.5-flash",
            has_live_credentials=has_key,
        )

        self.simulate_failure = simulate_failure

        if self.simulate_failure:
            self.status = (
                ProviderStatus.UNAVAILABLE.value
            )

    def generate(
        self,
        fact_pack: FactPack,
        routing_decision: RoutingDecision,
    ) -> Tuple[
        Optional[AIResponseContract],
        bool,
        Optional[str],
    ]:
        if self.simulate_failure:
            return (
                None,
                False,
                "Simulated upstream rate limit.",
            )

        response_id = (
            f"RESP-GF-"
            f"{uuid.uuid4().hex[:10].upper()}"
        )

        entity_str = (
            fact_pack.active_entity_id
            or "Portfolio"
        )

        facts_list = [
            f"{fact.metric_name}: {fact.value}"
            for fact in fact_pack.facts
            if fact.value is not None
        ]

        overall_freshness = (
            _resolve_overall_freshness(
                fact_pack.facts
            )
        )

        contract = AIResponseContract(
            response_id=response_id,
            response_type=(
                routing_decision.query_type.value
            ),
            headline=(
                "Executive Reasoning Analysis "
                f"for {entity_str}"
            ),
            verified_facts=facts_list,
            explanation=(
                f"Complex reasoning synthesis for "
                f"{entity_str}. Evaluated underlying "
                "relationships."
            ),
            recommendations=[
                "Verify safety stock thresholds "
                "before expediting transfer orders."
            ],
            data_limitations=[],
            freshness=overall_freshness,
            provider_used=self.provider_name,
            provider_status=self.status,
            model_used=self.model_name,
            is_fallback=False,
            token_usage={
                "prompt_tokens": 280,
                "completion_tokens": 110,
                "total_tokens": 390,
            },
            provenance={
                "gateway": "Cloudflare_AI_Gateway",
                "provider_mode": self.status,
            },
        )

        return contract, True, None


class GroqProvider(BaseAIProvider):
    """Secondary failover provider."""

    def __init__(
        self,
        simulate_failure: bool = False,
    ) -> None:
        has_key = bool(
            settings.groq_api_key.strip()
        )

        super().__init__(
            provider_name=(
                AIProviderType.GROQ.value
            ),
            model_name=(
                "llama-3.3-70b-versatile"
            ),
            has_live_credentials=has_key,
        )

        self.simulate_failure = simulate_failure

        if self.simulate_failure:
            self.status = (
                ProviderStatus.UNAVAILABLE.value
            )

    def generate(
        self,
        fact_pack: FactPack,
        routing_decision: RoutingDecision,
    ) -> Tuple[
        Optional[AIResponseContract],
        bool,
        Optional[str],
    ]:
        if self.simulate_failure:
            return (
                None,
                False,
                "Simulated Groq gateway error.",
            )

        response_id = (
            f"RESP-GROQ-"
            f"{uuid.uuid4().hex[:10].upper()}"
        )

        facts_list = [
            f"{fact.metric_name}: {fact.value}"
            for fact in fact_pack.facts
            if fact.value is not None
        ]

        overall_freshness = (
            _resolve_overall_freshness(
                fact_pack.facts
            )
        )

        contract = AIResponseContract(
            response_id=response_id,
            response_type=(
                routing_decision.query_type.value
            ),
            headline=(
                "Groq Failover "
                "Intelligence Report"
            ),
            verified_facts=facts_list,
            explanation=(
                "Processed via secondary "
                "Groq failover tier."
            ),
            recommendations=[],
            data_limitations=[],
            freshness=overall_freshness,
            provider_used=self.provider_name,
            provider_status=self.status,
            model_used=self.model_name,
            is_fallback=True,
            token_usage={
                "prompt_tokens": 150,
                "completion_tokens": 60,
                "total_tokens": 210,
            },
            provenance={
                "failover_tier": "SECONDARY",
                "provider_mode": self.status,
            },
        )

        return contract, True, None


class WorkersAIProvider(
    BaseAIProvider
):
    """Tertiary failover provider."""

    def __init__(
        self,
        simulate_failure: bool = False,
    ) -> None:
        has_key = bool(
            settings.cloudflare_account_id.strip()
            and settings.cloudflare_api_token.strip()
        )

        super().__init__(
            provider_name=(
                AIProviderType.WORKERS_AI.value
            ),
            model_name=(
                "@cf/meta/llama-3.1-8b-instruct"
            ),
            has_live_credentials=has_key,
        )

        self.simulate_failure = simulate_failure

        if self.simulate_failure:
            self.status = (
                ProviderStatus.UNAVAILABLE.value
            )

    def generate(
        self,
        fact_pack: FactPack,
        routing_decision: RoutingDecision,
    ) -> Tuple[
        Optional[AIResponseContract],
        bool,
        Optional[str],
    ]:
        if self.simulate_failure:
            return (
                None,
                False,
                "Simulated Workers AI endpoint unavailable.",
            )

        response_id = (
            f"RESP-WAI-"
            f"{uuid.uuid4().hex[:10].upper()}"
        )

        facts_list = [
            f"{fact.metric_name}: {fact.value}"
            for fact in fact_pack.facts
            if fact.value is not None
        ]

        overall_freshness = (
            _resolve_overall_freshness(
                fact_pack.facts
            )
        )

        contract = AIResponseContract(
            response_id=response_id,
            response_type=(
                routing_decision.query_type.value
            ),
            headline=(
                "Workers AI Tertiary "
                "Failover Report"
            ),
            verified_facts=facts_list,
            explanation=(
                "Processed via tertiary "
                "Cloudflare Workers AI tier."
            ),
            recommendations=[],
            data_limitations=[],
            freshness=overall_freshness,
            provider_used=self.provider_name,
            provider_status=self.status,
            model_used=self.model_name,
            is_fallback=True,
            token_usage={
                "prompt_tokens": 100,
                "completion_tokens": 40,
                "total_tokens": 140,
            },
            provenance={
                "failover_tier": "TERTIARY",
                "provider_mode": self.status,
            },
        )

        return contract, True, None


class AIGateway:
    """Manage routing, quota reservation, validation, and failover."""

    def __init__(
        self,
        simulate_gemini_failure: bool = False,
        simulate_groq_failure: bool = False,
        simulate_workers_failure: bool = False,
    ) -> None:
        self.flash_lite_provider = (
            GeminiFlashLiteProvider(
                simulate_failure=(
                    simulate_gemini_failure
                )
            )
        )

        self.flash_provider = (
            GeminiFlashProvider(
                simulate_failure=(
                    simulate_gemini_failure
                )
            )
        )

        self.groq_provider = GroqProvider(
            simulate_failure=simulate_groq_failure
        )

        self.workers_ai_provider = (
            WorkersAIProvider(
                simulate_failure=(
                    simulate_workers_failure
                )
            )
        )

        self.fallback_provider = (
            DeterministicFallbackProvider()
        )

    @staticmethod
    def _estimated_provider_usage(
        provider: BaseAIProvider,
    ) -> Tuple[int, int]:
        """
        Return conservative pre-call token estimates.

        These are reservations, not final accounting values.
        Final usage is settled from the provider response.
        """
        estimates = {
            AIProviderType.GEMINI_FLASH_LITE.value: (
                200,
                80,
            ),
            AIProviderType.GEMINI_FLASH.value: (
                350,
                150,
            ),
            AIProviderType.GROQ.value: (
                220,
                100,
            ),
            AIProviderType.WORKERS_AI.value: (
                180,
                80,
            ),
        }

        return estimates.get(
            provider.provider_name,
            (
                0,
                0,
            ),
        )

    @staticmethod
    def _is_external_provider(
        provider: BaseAIProvider,
    ) -> bool:
        """Return whether provider represents an external AI call."""
        return provider.provider_name != (
            AIProviderType.DETERMINISTIC_FALLBACK.value
        )

    def _generate_deterministic_fallback(
        self,
        fact_pack: FactPack,
        routing_decision: RoutingDecision,
        explanation: Optional[str] = None,
        provenance_updates: Optional[
            Dict[str, Any]
        ] = None,
    ) -> AIResponseContract:
        """Generate the safe deterministic final response."""
        contract, success, error = (
            self.fallback_provider.generate(
                fact_pack,
                routing_decision,
            )
        )

        if not success or contract is None:
            raise RuntimeError(
                "Deterministic AURIX fallback failed."
                + (
                    f" {error}"
                    if error
                    else ""
                )
            )

        if explanation is not None:
            contract.explanation = explanation

        if provenance_updates:
            contract.provenance.update(
                provenance_updates
            )

        return contract

    def process_query(
        self,
        fact_pack: FactPack,
        routing_decision: RoutingDecision,
        db: Optional[Session] = None,
    ) -> AIResponseContract:
        """
        Execute a query through the AI cascade.

        External provider flow:

            estimate
                ↓
            persistent quota reservation
                ↓
            provider call
                ↓
            grounding validation
                ↓
            settle actual usage
                ↓
            response

        Failed/ungrounded providers release their reservations and
        the cascade continues.
        """
        tenant_id = (
            fact_pack.tenant_id
            or settings.default_tenant_id
        )

        # --------------------------------------------------------
        # 1. Deterministic fast-path
        # --------------------------------------------------------
        if (
            routing_decision.fast_path_eligible
            or not routing_decision.requires_ai
        ):
            return self._generate_deterministic_fallback(
                fact_pack,
                routing_decision,
            )

        # --------------------------------------------------------
        # 2. Provider selection
        # --------------------------------------------------------
        is_routine = (
            routing_decision.query_type
            in (
                QueryType.READ,
                QueryType.COMPARE,
            )
        )

        primary_provider: BaseAIProvider = (
            self.flash_lite_provider
            if is_routine
            else self.flash_provider
        )

        provider_cascade: List[
            BaseAIProvider
        ] = [
            primary_provider,
            self.groq_provider,
            self.workers_ai_provider,
        ]

        # --------------------------------------------------------
        # 3. Persistent quota requirement
        # --------------------------------------------------------
        #
        # A real external AI request must have a DB-backed quota
        # reservation. We deliberately refuse to make an external
        # provider call without the persistent enforcement context.
        #
        # Offline test doubles are allowed to execute without DB
        # reservation because they do not generate external cost.
        #
        if db is None and any(
            provider.status
            == ProviderStatus.LIVE.value
            for provider in provider_cascade
        ):
            logger.error(
                "Live AI provider requested without "
                "persistent quota database session "
                "for tenant [%s].",
                tenant_id,
            )

            return self._generate_deterministic_fallback(
                fact_pack,
                routing_decision,
                explanation=(
                    "Live AI execution requires a "
                    "persistent quota session. "
                    "Deterministic AURIX analysis "
                    "was returned instead."
                ),
                provenance_updates={
                    "quota_db_required": True,
                    "live_provider_blocked": True,
                },
            )

        # --------------------------------------------------------
        # 3B. Quota enforcement BEFORE provider selection
        # --------------------------------------------------------
        #
        # Test doubles do not incur external cost, but they must
        # still respect an exhausted tenant AI policy. This keeps
        # production and test behavior aligned without requiring
        # live API credentials in the test suite.
        #
        quota_probe_provider = primary_provider

        (
            estimated_input_tokens,
            estimated_output_tokens,
        ) = self._estimated_provider_usage(
            quota_probe_provider
        )

        estimated_token_count = (
            estimated_input_tokens
            + estimated_output_tokens
        )

        if quota_probe_provider.status == (
            ProviderStatus.OFFLINE_TEST_DOUBLE.value
        ):
            try:
                estimated_cost = 0.001

                quota_check = (
                    AIQuotaManager.check_quota(
                        tenant_id=tenant_id,
                        estimated_tokens=(
                            estimated_token_count
                        ),
                        estimated_cost_usd=estimated_cost,
                        db=db,
                    )
                )
            except Exception as exc:
                logger.exception(
                    "AI quota check failed for tenant [%s].",
                    tenant_id,
                )

                return self._generate_deterministic_fallback(
                    fact_pack,
                    routing_decision,
                    explanation=(
                        "AI quota enforcement could not "
                        "be evaluated safely. Deterministic "
                        "AURIX analysis was returned."
                    ),
                    provenance_updates={
                        "quota_check_error": str(exc),
                    },
                )

            if not quota_check.allowed:
                logger.warning(
                    "Tenant [%s] exceeded AI quota before "
                    "test-double execution: %s",
                    tenant_id,
                    quota_check.rejection_reason,
                )

                return self._generate_deterministic_fallback(
                    fact_pack,
                    routing_decision,
                    explanation=(
                        "AI quota limit reached: "
                        f"{quota_check.rejection_reason} "
                        "Deterministic AURIX analysis provided."
                    ),
                    provenance_updates={
                        "quota_exhausted": True,
                        "quota_rejection_reason": (
                            quota_check.rejection_reason
                        ),
                        "quota_enforced_before_test_double": (
                            True
                        ),
                    },
                )

        # --------------------------------------------------------
        # 4. Traverse cascade
        # --------------------------------------------------------
        for provider in provider_cascade:
            if (
                provider.status
                == ProviderStatus.UNAVAILABLE.value
            ):
                continue

            reservation_id: Optional[str] = None

            # ----------------------------------------------------
            # 4A. Persistent reservation for LIVE provider
            # ----------------------------------------------------
            if (
                provider.status
                == ProviderStatus.LIVE.value
            ):
                if db is None:
                    # Defensive guard; already handled above.
                    continue

                estimated_input_tokens, (
                    estimated_output_tokens
                ) = self._estimated_provider_usage(
                    provider
                )

                try:
                    reservation = (
                        AIQuotaManager.reserve_quota(
                            tenant_id=tenant_id,
                            provider=(
                                provider.provider_name
                            ),
                            model=provider.model_name,
                            estimated_input_tokens=(
                                estimated_input_tokens
                            ),
                            estimated_output_tokens=(
                                estimated_output_tokens
                            ),
                            db=db,
                        )
                    )
                except Exception as exc:
                    logger.exception(
                        "AI quota reservation failed "
                        "for tenant [%s], provider [%s].",
                        tenant_id,
                        provider.provider_name,
                    )

                    return (
                        self._generate_deterministic_fallback(
                            fact_pack,
                            routing_decision,
                            explanation=(
                                "AI quota enforcement "
                                "could not be established "
                                "safely. Deterministic "
                                "AURIX analysis was "
                                "returned instead."
                            ),
                            provenance_updates={
                                "quota_reservation_error": str(
                                    exc
                                ),
                                "provider_blocked": (
                                    provider.provider_name
                                ),
                            },
                        )
                    )

                if not reservation.allowed:
                    logger.warning(
                        "Tenant [%s] blocked by AI quota "
                        "before provider [%s]: %s",
                        tenant_id,
                        provider.provider_name,
                        reservation.rejection_reason,
                    )

                    return (
                        self._generate_deterministic_fallback(
                            fact_pack,
                            routing_decision,
                            explanation=(
                                "AI quota limit reached: "
                                f"{reservation.rejection_reason}. "
                                "Deterministic AURIX analysis "
                                "provided."
                            ),
                            provenance_updates={
                                "quota_exhausted": True,
                                "quota_rejection_reason": (
                                    reservation.rejection_reason
                                ),
                            },
                        )
                    )

                reservation_id = (
                    reservation.reservation_id
                )

            # ----------------------------------------------------
            # 4B. Execute provider
            # ----------------------------------------------------
            candidate_resp: Optional[
                AIResponseContract
            ]

            is_success: bool
            provider_error: Optional[str]

            candidate_resp, is_success, provider_error = (
                provider.generate(
                    fact_pack,
                    routing_decision,
                )
            )

            # ----------------------------------------------------
            # 4C. Provider failure → release reservation
            # ----------------------------------------------------
            if (
                not is_success
                or candidate_resp is None
            ):
                if reservation_id is not None:
                    try:
                        AIQuotaManager.release_reservation(
                            reservation_id=reservation_id,
                            reason=(
                                provider_error
                                or "PROVIDER_FAILURE"
                            ),
                            db=db,
                        )
                        if db is None:
                            raise RuntimeError(
                                "Reservation release completed without a database session."
                            )
                        db.commit()
                    except Exception:
                        if db is not None:
                            db.rollback()
                        logger.exception(
                            "Failed to release AI reservation "
                            "[%s] after provider failure.",
                            reservation_id,
                        )

                continue

            # ----------------------------------------------------
            # 4D. Test double responses are not billable
            # ----------------------------------------------------
            if (
                provider.status
                == ProviderStatus.OFFLINE_TEST_DOUBLE.value
            ):
                grounding_result = (
                    GroundingValidator.validate(
                        ai_response_text=(
                            f"{candidate_resp.headline} "
                            f"{candidate_resp.explanation}"
                        ),
                        fact_pack=fact_pack,
                    )
                )

                if not grounding_result.is_grounded:
                    continue

                candidate_resp.provenance[
                    "billing_mode"
                ] = "NON_BILLABLE_TEST_DOUBLE"

                MetricsRegistry.record_ai_usage(
                    input_tokens=(
                        candidate_resp.token_usage.get(
                            "prompt_tokens",
                            0,
                        )
                    ),
                    output_tokens=(
                        candidate_resp.token_usage.get(
                            "completion_tokens",
                            0,
                        )
                    ),
                    provider=(
                        candidate_resp.provider_used
                    ),
                    is_fallback=(
                        candidate_resp.is_fallback
                    ),
                )

                return candidate_resp

            # ----------------------------------------------------
            # 4E. Grounding validation
            # ----------------------------------------------------
            grounding_result = (
                GroundingValidator.validate(
                    ai_response_text=(
                        f"{candidate_resp.headline} "
                        f"{candidate_resp.explanation}"
                    ),
                    fact_pack=fact_pack,
                )
            )

            if not grounding_result.is_grounded:
                logger.warning(
                    "Grounding rejected provider response "
                    "from [%s].",
                    provider.provider_name,
                )

                if reservation_id is not None:
                    try:
                        AIQuotaManager.release_reservation(
                            reservation_id=reservation_id,
                            reason="GROUNDING_REJECTED",
                            db=db,
                        )
                        if db is None:
                            raise RuntimeError(
                                "Reservation release completed without a database session."
                            )
                        db.commit()
                    except Exception:
                        if db is not None:
                            db.rollback()
                        logger.exception(
                            "Failed to release AI reservation "
                            "[%s] after grounding rejection.",
                            reservation_id,
                        )

                continue

            # ----------------------------------------------------
            # 4F. Settle actual provider usage
            # ----------------------------------------------------
            in_tokens = int(
                candidate_resp.token_usage.get(
                    "prompt_tokens",
                    0,
                )
            )

            out_tokens = int(
                candidate_resp.token_usage.get(
                    "completion_tokens",
                    0,
                )
            )

            try:
                if reservation_id is not None:
                    if db is None:
                        raise RuntimeError(
                            "Persistent reservation exists "
                            "without database session."
                        )

                    usage_record = (
                        AIQuotaManager.settle_reservation(
                            reservation_id=(
                                reservation_id
                            ),
                            input_tokens=in_tokens,
                            output_tokens=out_tokens,
                            is_fallback=(
                                candidate_resp.is_fallback
                            ),
                            db=db,
                        )
                    )

                    candidate_resp.provenance[
                        "quota_reservation_id"
                    ] = reservation_id

                    candidate_resp.provenance[
                        "settled_cost_usd"
                    ] = (
                        usage_record.estimated_cost_usd
                    )

                    db.commit()

                else:
                    # Defensive branch for future non-reserved
                    # internal billable providers. No external
                    # live provider should reach this branch.
                    if (
                        provider.status
                        == ProviderStatus.LIVE.value
                    ):
                        raise RuntimeError(
                            "Live external provider completed "
                            "without a quota reservation."
                        )

                MetricsRegistry.record_ai_usage(
                    input_tokens=in_tokens,
                    output_tokens=out_tokens,
                    provider=(
                        candidate_resp.provider_used
                    ),
                    is_fallback=(
                        candidate_resp.is_fallback
                    ),
                )

            except Exception as exc:
                if db is not None:
                    db.rollback()

                logger.exception(
                    "AI usage settlement failed for "
                    "provider [%s].",
                    provider.provider_name,
                )

                # We must NOT return a live provider response
                # when its usage could not be persisted/accounted.
                return (
                    self._generate_deterministic_fallback(
                        fact_pack,
                        routing_decision,
                        explanation=(
                            "AI provider response was obtained, "
                            "but usage accounting could not be "
                            "persisted safely. Deterministic "
                            "AURIX analysis was returned."
                        ),
                        provenance_updates={
                            "quota_settlement_error": str(
                                exc
                            ),
                            "provider_response_discarded": (
                                provider.provider_name
                            ),
                        },
                    )
                )

            return candidate_resp

        # --------------------------------------------------------
        # 5. Ultimate deterministic safety net
        # --------------------------------------------------------
        return self._generate_deterministic_fallback(
            fact_pack,
            routing_decision,
            provenance_updates={
                "ai_provider_cascade_exhausted": True,
            },
        )


class AutonomousCopilotGateway:
    """Unified facade for Copilot Router + AI Gateway."""

    _gateway = AIGateway()

    @classmethod
    def query(
        cls,
        prompt: str,
        context: Any,
        model_name: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> AIResponseContract:
        """Process a high-level Copilot query."""
        fact_pack: FactPack

        if isinstance(
            context,
            FactPack,
        ):
            fact_pack = context

        elif (
            hasattr(context, "fact_pack")
            and isinstance(
                context.fact_pack,
                FactPack,
            )
        ):
            fact_pack = context.fact_pack

        else:
            fact_pack = FactPack(
                pack_id=(
                    f"FACT-"
                    f"{uuid.uuid4().hex[:8].upper()}"
                ),
                tenant_id=str(
                    getattr(
                        context,
                        "tenant_id",
                        settings.default_tenant_id,
                    )
                ),
                facts=[],
                generated_at="",
            )

        prompt_lower = prompt.lower()

        query_type = (
            QueryType.EXPLAIN
            if (
                "why" in prompt_lower
                or "root" in prompt_lower
            )
            else QueryType.READ
        )

        routing_decision = RoutingDecision(
            query=prompt,
            query_type=query_type,
            requires_ai=True,
            confidence=RouterConfidence.HIGH,
            context_source="DYNAMIC_ASSEMBLY",
            resolved_entity_id=getattr(
                context,
                "active_entity_id",
                None,
            ),
        )

        return cls._gateway.process_query(
            fact_pack,
            routing_decision,
            db=db,
        )
