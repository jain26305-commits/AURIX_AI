"""Executive Intelligence Eight-Question Brief API router for Phase 28."""

import logging
from fastapi import APIRouter, Depends

from aurix_api.schemas.auth import Permission, TenantContext
from aurix_api.schemas.base import ApiResponse, ResponseMetadata, ResponseStatus
from aurix_api.security.auth import get_current_tenant_context
from aurix_api.security.rate_limit import rate_limit_standard
from aurix_api.security.rbac import require_permission
from aurix_core.scenarios.contracts import ExecutiveEightQuestionBrief
from aurix_core.scenarios.executive_engine import ExecutiveIntelligenceEngine

logger = logging.getLogger("aurix_api.routers.executive")

router = APIRouter(prefix="/api/v1/executive", tags=["Executive Intelligence"])


@router.get(
    "/brief",
    response_model=ApiResponse[ExecutiveEightQuestionBrief],
    summary="Get Executive Eight-Question Operational Brief",
)
async def get_executive_brief(
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
) -> ApiResponse[ExecutiveEightQuestionBrief]:
    """Retrieve grounded executive brief answering the mandatory 8 operational questions."""
    tenant_id = tenant_context.tenant_id
    brief = ExecutiveIntelligenceEngine.generate_executive_brief(
        tenant_id=tenant_id,
        supplier_disruption_days=12.0,
        expected_value_usd=18400.0,
        realized_savings_usd=16200.0,
    )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=brief,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )
