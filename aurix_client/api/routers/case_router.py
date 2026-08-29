from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional, Any
import datetime

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

@router.post("/{case_id}/transition")
async def transition_case_stage(case_id: str, req: TransitionStageRequest, x_tenant_id: Optional[str] = Header(None)):
    return {"success": True, "caseId": case_id, "stage": req.stage}

@router.post("/create")
async def create_case(req: CreateCaseRequest, x_tenant_id: Optional[str] = Header(None)):
    return {
        "id": f"CASE-2026-{datetime.datetime.now().strftime('%M%S')}",
        "title": req.title,
        "domain": req.domain,
        "priority": req.priority,
        "stage": "OPEN",
        "owner": "Supply Chain Desk",
        "targetEntityId": req.targetEntityId,
        "targetEntityName": req.targetEntityName,
        "summary": req.summary,
        "rootCauseAttribution": "Under automated intake analysis.",
        "exposureINR": req.exposureINR,
        "serviceImpactPercent": 95.0,
        "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "updatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "provenanceLineage": [
            {
                "stepIndex": 1,
                "stage": "OPEN",
                "title": "Case Manually Provisioned",
                "actorOrSystem": "Operator Dispatch",
                "timestamp": "Just now",
                "summary": "Case initiated via AURIX Workspace."
            }
        ]
    }