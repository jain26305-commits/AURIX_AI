from fastapi import APIRouter, HTTPException, Header, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import datetime

from aurix_core.database.engine import get_db
from aurix_core.phase16.models import Phase16CaseModel
from aurix_core.database.tenant_context import set_current_tenant_id
from api.routers.auth_router import get_current_user_claims

router = APIRouter(prefix="/cases", tags=["Case Management"])

class TransitionStageRequest(BaseModel):
    caseId: str
    stage: str

class CreateCaseRequest(BaseModel):
    title: str
    domain: str
    priority: str
    targetEntityId: str
    targetEntityName: str
    summary: str
    exposureINR: Optional[float] = 0.0

def _seed_cases_if_empty(db: Session, tenant_id: str):
    if db.query(Phase16CaseModel).filter(Phase16CaseModel.tenant_id == tenant_id).count() == 0:
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        c1 = Phase16CaseModel(
            id="CASE-2026-881",
            tenant_id=tenant_id,
            case_type="INVENTORY",
            severity="CRITICAL",
            status="IN_TRIAGE",
            title="Severe Stockout Breach Risk: Dotknit White S",
            owner="Bengaluru Planning Desk",
            priority="CRITICAL",
            impact_json={
                "targetEntityId": "SKU-004",
                "targetEntityName": "Dotknit White S",
                "summary": "Projected stockout within 4.2 days due to 35% regional demand surge and supplier Apex Mills fabric shipment delay.",
                "rootCauseAttribution": "Lead time expanded from 18 to 28 days (+55.6% drift) during spinning mill downtime.",
                "exposureINR": 340000.0,
                "serviceImpactPercent": 98.5,
            },
            resolution_json={
                "provenanceLineage": [
                    {
                        "stepIndex": 1,
                        "stage": "OPEN",
                        "title": "Breach Threshold Exceeded",
                        "actorOrSystem": "Inventory Engine Monitor",
                        "timestamp": "Yesterday 08:30 AM",
                        "summary": "Projected on-hand dropped below computed reorder point (144 units)."
                    },
                    {
                        "stepIndex": 2,
                        "stage": "IN_TRIAGE",
                        "title": "Assigned to Lead Planner",
                        "actorOrSystem": "Kaushik Jain (Super Admin)",
                        "timestamp": "Today 04:15 AM",
                        "summary": "Evaluation of air-freight expedite versus secondary mill substitution initiated."
                    }
                ]
            },
            created_at=now_dt,
            updated_at=now_dt,
        )
        db.add(c1)
        db.commit()

def _format_case_dict(c: Phase16CaseModel) -> dict:
    impact = c.impact_json or {}
    resolution = c.resolution_json or {}
    return {
        "id": c.id,
        "title": c.title,
        "domain": c.case_type,
        "priority": c.priority,
        "stage": c.status,
        "owner": c.owner or "Unassigned",
        "targetEntityId": impact.get("targetEntityId", ""),
        "targetEntityName": impact.get("targetEntityName", ""),
        "summary": impact.get("summary", ""),
        "rootCauseAttribution": impact.get("rootCauseAttribution", ""),
        "exposureINR": impact.get("exposureINR", 0.0),
        "serviceImpactPercent": impact.get("serviceImpactPercent", 100.0),
        "createdAt": c.created_at.isoformat(),
        "updatedAt": c.updated_at.isoformat(),
        "provenanceLineage": resolution.get("provenanceLineage", [])
    }

@router.get("")
@router.get("/")
async def list_cases(
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user_claims)
):
    tenant_id = claims["tenantId"]
    set_current_tenant_id(tenant_id)
    db.info["tenant_id"] = tenant_id
    
    _seed_cases_if_empty(db, tenant_id)
    cases = db.query(Phase16CaseModel).filter(Phase16CaseModel.tenant_id == tenant_id).all()
    return [_format_case_dict(c) for c in cases]

@router.get("/{case_id}")
async def get_case_by_id(
    case_id: str,
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user_claims)
):
    tenant_id = claims["tenantId"]
    set_current_tenant_id(tenant_id)
    db.info["tenant_id"] = tenant_id
    
    c = db.query(Phase16CaseModel).filter(
        Phase16CaseModel.id == case_id,
        Phase16CaseModel.tenant_id == tenant_id
    ).first()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found.")
    return _format_case_dict(c)

@router.post("/{case_id}/transition")
async def transition_case_stage(
    case_id: str,
    req: TransitionStageRequest,
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user_claims)
):
    tenant_id = claims["tenantId"]
    set_current_tenant_id(tenant_id)
    db.info["tenant_id"] = tenant_id
    
    c = db.query(Phase16CaseModel).filter(
        Phase16CaseModel.id == case_id,
        Phase16CaseModel.tenant_id == tenant_id
    ).first()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found.")
    
    now_dt = datetime.datetime.now(datetime.timezone.utc)
    c.status = req.stage
    c.updated_at = now_dt
    
    res = dict(c.resolution_json or {})
    lineage = list(res.get("provenanceLineage", []))
    lineage.append({
        "stepIndex": len(lineage) + 1,
        "stage": req.stage,
        "title": f"Stage Transitioned to {req.stage}",
        "actorOrSystem": f"{claims.get('email', 'Operator')}",
        "timestamp": "Just now",
        "summary": f"Workflow stage moved to {req.stage}."
    })
    res["provenanceLineage"] = lineage
    c.resolution_json = res
    db.commit()
    return {"success": True, "caseId": case_id, "stage": req.stage}

@router.post("/create")
async def create_case(
    req: CreateCaseRequest,
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user_claims)
):
    tenant_id = claims["tenantId"]
    set_current_tenant_id(tenant_id)
    db.info["tenant_id"] = tenant_id
    
    now_dt = datetime.datetime.now(datetime.timezone.utc)
    case_id = f"CASE-2026-{now_dt.strftime('%M%S')}"
    
    new_case = Phase16CaseModel(
        id=case_id,
        tenant_id=tenant_id,
        case_type=req.domain,
        severity=req.priority,
        status="OPEN",
        title=req.title,
        owner="Supply Chain Desk",
        priority=req.priority,
        impact_json={
            "targetEntityId": req.targetEntityId,
            "targetEntityName": req.targetEntityName,
            "summary": req.summary,
            "rootCauseAttribution": "Under automated intake analysis.",
            "exposureINR": req.exposureINR,
            "serviceImpactPercent": 95.0,
        },
        resolution_json={
            "provenanceLineage": [
                {
                    "stepIndex": 1,
                    "stage": "OPEN",
                    "title": "Case Provisioned",
                    "actorOrSystem": f"{claims.get('email', 'Operator')}",
                    "timestamp": "Just now",
                    "summary": "Case initiated via AURIX Workspace."
                }
            ]
        },
        created_at=now_dt,
        updated_at=now_dt,
    )
    db.add(new_case)
    db.commit()
    db.refresh(new_case)
    return _format_case_dict(new_case)