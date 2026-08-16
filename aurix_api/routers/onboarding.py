"""Automated data onboarding API router for Phase 11."""

import logging
from typing import Any, Dict, Generator, List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from aurix_api.schemas.base import ApiResponse, ResponseMetadata, ResponseStatus
from aurix_api.schemas.auth import Permission, TenantContext
from aurix_api.security.auth import get_current_tenant_context
from aurix_api.security.rbac import require_permission
from aurix_api.security.rate_limit import rate_limit_standard
from aurix_core.database.engine import SessionLocal
from aurix_core.onboarding.contracts import (
    ManualMappingResolutionRequest,
    OnboardingResult,
    OnboardingStatus,
)
from aurix_core.onboarding.service import OnboardingService

logger = logging.getLogger("aurix_api.routers.onboarding")

router = APIRouter(prefix="/api/v1/onboarding", tags=["Automated Data Onboarding"])


def get_db() -> Generator[Session, None, None]:
    """Database session dependency yielding a managed SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ResolveMappingPayload(BaseModel):
    """Payload to resolve mapping ambiguities with accompanying raw records."""
    raw_records: List[Dict[str, Any]] = Field(default_factory=list)
    resolution: ManualMappingResolutionRequest


@router.post(
    "/upload",
    response_model=ApiResponse[OnboardingResult],
    summary="Upload & Auto-Onboard Customer File",
    description="Uploads a CSV, XLSX, JSON, or Google Sheets tabular file for automated schema discovery and onboarding.",
)
async def upload_and_onboard_file(
    file: UploadFile = File(...),
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.WRITE_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
    db: Session = Depends(get_db),
) -> ApiResponse[OnboardingResult]:
    """Processes uploaded customer dataset through the automated onboarding pipeline."""
    tenant_id = tenant_context.tenant_id
    filename = file.filename or "unnamed_upload.csv"

    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file stream: {str(e)}",
        )

    result = OnboardingService.onboard_file(
        db=db,
        tenant_id=tenant_id,
        filename=filename,
        content=content,
    )

    api_status = ResponseStatus.SUCCESS
    if result.overall_status == OnboardingStatus.FAILED:
        api_status = ResponseStatus.FAILED
    elif result.overall_status in (OnboardingStatus.PARTIAL_SUCCESS, OnboardingStatus.USER_INPUT_REQUIRED):
        api_status = ResponseStatus.PARTIAL_SUCCESS

    return ApiResponse(
        status=api_status,
        data=result,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.post(
    "/records",
    response_model=ApiResponse[OnboardingResult],
    summary="Auto-Onboard Structured API Records",
    description="Submits an in-memory JSON array of records for automated schema discovery and onboarding.",
)
async def onboard_raw_records(
    records: List[Dict[str, Any]],
    source_name: str = "API_PAYLOAD",
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.WRITE_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
    db: Session = Depends(get_db),
) -> ApiResponse[OnboardingResult]:
    """Ingests raw in-memory record collections directly through the onboarding pipeline."""
    tenant_id = tenant_context.tenant_id

    result = OnboardingService.onboard_raw_records(
        db=db,
        tenant_id=tenant_id,
        records=records,
        source_name=source_name,
    )

    api_status = ResponseStatus.SUCCESS
    if result.overall_status == OnboardingStatus.FAILED:
        api_status = ResponseStatus.FAILED
    elif result.overall_status in (OnboardingStatus.PARTIAL_SUCCESS, OnboardingStatus.USER_INPUT_REQUIRED):
        api_status = ResponseStatus.PARTIAL_SUCCESS

    return ApiResponse(
        status=api_status,
        data=result,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.post(
    "/resolve-mapping",
    response_model=ApiResponse[OnboardingResult],
    summary="Resolve Ambiguous Column Mappings",
    description="Applies explicit column-to-canonical mappings to resolve datasets in USER_INPUT_REQUIRED state.",
)
async def resolve_mapping(
    payload: ResolveMappingPayload,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.WRITE_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
    db: Session = Depends(get_db),
) -> ApiResponse[OnboardingResult]:
    """Re-evaluates onboarding dataset using client-provided column mapping overrides."""
    tenant_id = tenant_context.tenant_id

    result = OnboardingService.resolve_manual_mapping(
        db=db,
        tenant_id=tenant_id,
        raw_records=payload.raw_records,
        request_data=payload.resolution,
    )

    api_status = ResponseStatus.SUCCESS if result.overall_status == OnboardingStatus.COMPLETED else ResponseStatus.PARTIAL_SUCCESS

    return ApiResponse(
        status=api_status,
        data=result,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )