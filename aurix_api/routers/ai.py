"""Grounded AI Copilot and Executive Question Answering API router."""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from aurix_api.routers.intelligence import get_db
from aurix_api.schemas.ai import AiQueryRequest, AiQueryResponse
from aurix_api.schemas.auth import Permission, TenantContext
from aurix_api.schemas.base import ApiResponse, ResponseMetadata, ResponseStatus
from aurix_api.security.auth import get_current_tenant_context
from aurix_api.security.rate_limit import rate_limit_ai
from aurix_api.security.rbac import require_permission

logger = logging.getLogger("aurix_api.routers.ai")

router = APIRouter(prefix="/api/v1/ai", tags=["AI Copilot"])


@router.post(
    "/query",
    response_model=ApiResponse[AiQueryResponse],
    summary="Query AURIX deterministic intelligence with grounded AI escalation",
)
async def query_copilot(
    payload: AiQueryRequest,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.USE_AI)),
    __: TenantContext = Depends(rate_limit_ai()),
    db: Session = Depends(get_db),
) -> ApiResponse[AiQueryResponse]:
    """Route the request through the canonical AURIX Query Router first."""
    tenant_id = tenant_context.tenant_id
    prompt_query = str(
        payload.query
        or payload.prompt
        or "Analyze inventory and demand posture."
    )

    try:
        from aurix_core.intelligence.service import IntelligenceService

        page_context = None
        if payload.page_context is not None:
            from aurix_core.intelligence.router import PageContext

            page_context = PageContext(**payload.page_context.model_dump())

        response_contract = IntelligenceService(
            db=db,
            tenant_id=tenant_id,
        ).ask_ai(
            query=prompt_query,
            conversation_id=payload.conversation_id,
            page_context=page_context,
            analytical_data=payload.analytical_data,
        )

        data = AiQueryResponse(
            response_id=response_contract.response_id,
            response_type=response_contract.response_type,
            headline=response_contract.headline,
            response=response_contract.explanation,
            summary=response_contract.explanation,
            narrative=response_contract.explanation,
            verified_facts=response_contract.verified_facts,
            explanation=response_contract.explanation,
            recommendations=response_contract.recommendations,
            citations=response_contract.verified_facts,
            financial_impact=response_contract.financial_impact,
            operational_impact=response_contract.operational_impact,
            data_limitations=response_contract.data_limitations,
            source=response_contract.source,
            evidence_quality=response_contract.evidence_quality,
            freshness=response_contract.freshness,
            provider_used=response_contract.provider_used,
            model_used=response_contract.model_used,
            answer_source=response_contract.answer_source,
            is_fallback=response_contract.is_fallback,
            confidence_score=0.95,
            token_usage=response_contract.token_usage,
            suggested_actions=[],
            provenance=response_contract.provenance,
        )

        return ApiResponse(
            status=ResponseStatus.SUCCESS,
            data=data,
            meta=ResponseMetadata(tenant_id=tenant_id),
        )
    except Exception as exc:
        logger.exception(
            "Canonical AURIX query failed for tenant [%s].",
            tenant_id,
        )
        raise exc
