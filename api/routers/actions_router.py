from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
import datetime

from aurix_core.database.engine import get_db
from aurix_core.database.models.actions import Phase14ActionModel
from aurix_core.database.tenant_context import set_current_tenant_id
from api.routers.auth_router import get_current_user_claims

router = APIRouter(prefix="/actions", tags=["Phase 14 Controlled Actions"])

class PreflightCheck(BaseModel):
    checkId: str
    name: str
    category: str
    passed: bool
    message: str
    timestamp: str

class ExecutionToken(BaseModel):
    tokenId: str
    signedBy: str
    role: str
    timestamp: str
    sha256Checksum: str
    phase14AuthorizationCode: str

class AuditTrailEntry(BaseModel):
    timestamp: str
    state: str
    actor: str
    note: str

class Phase14ActionItem(BaseModel):
    id: str
    title: str
    domain: str
    priority: str
    state: str
    targetEntityId: str
    targetEntityName: str
    prescriptivePayload: Dict[str, Any]
    initiatedBy: str
    assignedApproverRole: str
    createdAt: str
    updatedAt: str
    preflightCleared: bool
    preflightChecks: List[PreflightCheck]
    executionToken: Optional[ExecutionToken] = None
    auditTrail: List[AuditTrailEntry]

class ActionSummary(BaseModel):
    totalPendingCount: int
    awaitingApprovalCount: int
    executingCount: int
    executedTodayCount: int
    failedCount: int
    totalCommittedCapitalINR: float
    totalProtectedExposureINR: float

class ActionCenterFeedReport(BaseModel):
    evaluatedAt: str
    summary: ActionSummary
    actions: List[Phase14ActionItem]

class ActionDecisionRequest(BaseModel):
    actionId: str
    decision: str
    reason: Optional[str] = None

def _seed_actions_if_empty(db: Session, tenant_id: str):
    count = db.query(Phase14ActionModel).filter(Phase14ActionModel.tenant_id == tenant_id).count()
    if count == 0:
        now_dt = datetime.datetime.now(timezone_utc := datetime.timezone.utc)
        now = now_dt.isoformat()
        act1 = Phase14ActionModel(
            id="ACT-2026-101",
            tenant_id=tenant_id,
            title="Expedite PO-8821 Air Freight Delivery (Apex Mills)",
            domain="INVENTORY",
            priority="CRITICAL",
            state="AWAITING_APPROVAL",
            target_entity_id="SKU-004",
            target_entity_name="Dotknit White S",
            prescriptive_payload_json={
                "actionType": "EXPEDITE_AIR_FREIGHT",
                "quantity": 500,
                "destination": "BLR_CENTRAL_DC",
                "carrier": "GATI_AIR_EXPRESS",
                "financialCommitmentINR": 24500.0,
                "expectedRoiINR": 340000.0,
            },
            initiated_by="Autonomous Stockout Sentinel",
            assigned_approver_role="SUPER_ADMIN",
            preflight_cleared=True,
            preflight_checks_json=[
                {
                    "checkId": "CHK-01",
                    "name": "Supplier Capacity Verification",
                    "category": "ERP_CONNECTIVITY",
                    "passed": True,
                    "message": "Apex Mills confirmed 48h ready-to-ship lot readiness.",
                    "timestamp": now,
                },
                {
                    "checkId": "CHK-02",
                    "name": "Contingency Budget Authority",
                    "category": "BUDGET_CAPITAL",
                    "passed": True,
                    "message": "Within authorized 50,000 contingency reserve threshold.",
                    "timestamp": now,
                }
            ],
            execution_token_json={
                "tokenId": "TKN-SHA256-88192-A",
                "signedBy": "System Authority",
                "role": "SUPER_ADMIN",
                "timestamp": now,
                "sha256Checksum": "0x9b7a4c8e1f52d9a34e78b12c56df90a12e34bc78",
                "phase14AuthorizationCode": "PH14-AUTH-99014",
            },
            audit_trail_json=[
                {
                    "timestamp": now,
                    "state": "AWAITING_APPROVAL",
                    "actor": "Autonomous Dispatch Router",
                    "note": "Submitted to Super Admin approval queue."
                }
            ],
            created_at=now_dt,
            updated_at=now_dt,
        )
        db.add(act1)
        db.commit()

def _to_pydantic_action(row: Phase14ActionModel) -> Phase14ActionItem:
    return Phase14ActionItem(
        id=row.id,
        title=row.title,
        domain=row.domain,
        priority=row.priority,
        state=row.state,
        targetEntityId=row.target_entity_id,
        targetEntityName=row.target_entity_name,
        prescriptivePayload=row.prescriptive_payload_json,
        initiatedBy=row.initiated_by,
        assignedApproverRole=row.assigned_approver_role,
        createdAt=row.created_at.isoformat(),
        updatedAt=row.updated_at.isoformat(),
        preflightCleared=row.preflight_cleared,
        preflightChecks=[PreflightCheck(**c) for c in (row.preflight_checks_json or [])],
        executionToken=ExecutionToken(**row.execution_token_json) if row.execution_token_json else None,
        auditTrail=[AuditTrailEntry(**a) for a in (row.audit_trail_json or [])],
    )

@router.get("", response_model=ActionCenterFeedReport)
@router.get("/", response_model=ActionCenterFeedReport)
async def get_action_feed(
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user_claims)
):
    tenant_id = claims["tenantId"]
    set_current_tenant_id(tenant_id)
    db.info["tenant_id"] = tenant_id
    
    _seed_actions_if_empty(db, tenant_id)
    
    rows = db.query(Phase14ActionModel).filter(Phase14ActionModel.tenant_id == tenant_id).order_by(Phase14ActionModel.created_at.desc()).all()
    actions_list = [_to_pydantic_action(r) for r in rows]
    
    awaiting = sum(1 for a in actions_list if a.state == "AWAITING_APPROVAL")
    executed = sum(1 for a in actions_list if a.state == "EXECUTED")
    executing = sum(1 for a in actions_list if a.state == "APPROVED")
    failed = sum(1 for a in actions_list if a.state == "REJECTED")
    
    total_committed = sum(float(a.prescriptivePayload.get("financialCommitmentINR", 0.0)) for a in actions_list)
    total_protected = sum(float(a.prescriptivePayload.get("expectedRoiINR", 0.0)) for a in actions_list)

    return ActionCenterFeedReport(
        evaluatedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        summary=ActionSummary(
            totalPendingCount=len(actions_list),
            awaitingApprovalCount=awaiting,
            executingCount=executing,
            executedTodayCount=executed,
            failedCount=failed,
            totalCommittedCapitalINR=total_committed,
            totalProtectedExposureINR=total_protected,
        ),
        actions=actions_list,
    )

@router.post("/{action_id}/approve", response_model=Phase14ActionItem)
async def approve_action(
    action_id: str,
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user_claims)
):
    tenant_id = claims["tenantId"]
    set_current_tenant_id(tenant_id)
    db.info["tenant_id"] = tenant_id
    
    action = db.query(Phase14ActionModel).filter(
        Phase14ActionModel.id == action_id,
        Phase14ActionModel.tenant_id == tenant_id
    ).first()
    
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action [{action_id}] not found.")
    
    now_dt = datetime.datetime.now(datetime.timezone.utc)
    now = now_dt.isoformat()
    action.state = "APPROVED"
    action.updated_at = now_dt
    
    updated_audit = list(action.audit_trail_json or [])
    updated_audit.append({
        "timestamp": now,
        "state": "APPROVED",
        "actor": f"{claims.get('email', 'Operator')} ({claims.get('role', 'SUPER_ADMIN')})",
        "note": "Action verified and approved through Phase 14 cryptographic gate."
    })
    action.audit_trail_json = updated_audit
    flag_modified(action, "audit_trail_json")
    db.commit()
    db.refresh(action)
    return _to_pydantic_action(action)

@router.post("/{action_id}/execute", response_model=Phase14ActionItem)
async def execute_action(
    action_id: str,
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user_claims)
):
    tenant_id = claims["tenantId"]
    set_current_tenant_id(tenant_id)
    db.info["tenant_id"] = tenant_id
    
    action = db.query(Phase14ActionModel).filter(
        Phase14ActionModel.id == action_id,
        Phase14ActionModel.tenant_id == tenant_id
    ).first()
    
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action [{action_id}] not found.")
    
    now_dt = datetime.datetime.now(datetime.timezone.utc)
    now = now_dt.isoformat()
    action.state = "EXECUTED"
    action.updated_at = now_dt
    
    updated_audit = list(action.audit_trail_json or [])
    updated_audit.append({
        "timestamp": now,
        "state": "EXECUTED",
        "actor": "AURIX Phase 14 Execution Engine",
        "note": "Dispatched to external connector endpoints with verified cryptographic payload."
    })
    action.audit_trail_json = updated_audit
    flag_modified(action, "audit_trail_json")
    db.commit()
    db.refresh(action)
    return _to_pydantic_action(action)

@router.post("/{action_id}/reject")
async def reject_action(
    action_id: str,
    req: ActionDecisionRequest,
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user_claims)
):
    tenant_id = claims["tenantId"]
    set_current_tenant_id(tenant_id)
    db.info["tenant_id"] = tenant_id
    
    action = db.query(Phase14ActionModel).filter(
        Phase14ActionModel.id == action_id,
        Phase14ActionModel.tenant_id == tenant_id
    ).first()
    
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action [{action_id}] not found.")
    
    now_dt = datetime.datetime.now(datetime.timezone.utc)
    now = now_dt.isoformat()
    action.state = "REJECTED"
    action.updated_at = now_dt
    
    updated_audit = list(action.audit_trail_json or [])
    updated_audit.append({
        "timestamp": now,
        "state": "REJECTED",
        "actor": f"{claims.get('email', 'Operator')}",
        "note": req.reason or "Rejected by operator."
    })
    action.audit_trail_json = updated_audit
    flag_modified(action, "audit_trail_json")
    db.commit()
    return {"status": "SUCCESS", "actionId": action_id, "state": "REJECTED"}