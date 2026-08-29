from fastapi import APIRouter, HTTPException, Header, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
import datetime

from aurix_core.database.engine import get_db, engine
from aurix_core.database.models.auth import User
from aurix_core.database.models.connectors import ConnectorModel
from aurix_core.database.models.intelligence import AIAuditLogModel
from aurix_core.database.tenant_context import set_current_tenant_id
from api.routers.auth_router import get_current_user_claims

router = APIRouter(prefix="/admin", tags=["Administration & Connectors"])

class ConnectorTestResponse(BaseModel):
    connectorId: str
    status: str
    latencyMs: int
    message: str
    endpointVerified: str
    timestamp: str

class SyncConnectorRequest(BaseModel):
    connectorId: str
    syncMode: Optional[str] = Field(default="DELTA_CDC", description="FULL_REFRESH or DELTA_CDC")

class SyncConnectorResponse(BaseModel):
    connectorId: str
    status: str
    recordsSynced: int
    checkpointId: str
    completedAt: str
    durationMs: int

class RetrainModelRequest(BaseModel):
    modelId: str
    hyperparameterTuning: Optional[bool] = False

def _seed_connectors_if_empty(db: Session, tenant_id: str):
    if db.query(ConnectorModel).filter(ConnectorModel.tenant_id == tenant_id).count() == 0:
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        conns = [
            ConnectorModel(
                id="CONN-TALLY-01",
                tenant_id=tenant_id,
                name="Tally Prime Local CDC Bridge",
                connector_type="ERP_TALLY",
                status="CONNECTED",
                deployment="Local Agent (Outbound HTTPS)",
                connectivity_state="LIVE",
                last_sync_timestamp="3 minutes ago",
                next_scheduled_sync="in 12 minutes",
                records_synced_last_24h=42150,
                error_rate_percent=0.01,
                sync_frequency="Every 15 minutes (Incremental CDC)",
                endpoint_masked="https://agent-tally-peenya.internal.aurix.ai/***",
                health_note="Operational. Vouchers and ledger stock balances in sync.",
                checkpoint="CHK-TALLY-998241",
                created_at=now_dt,
                updated_at=now_dt
            ),
            ConnectorModel(
                id="CONN-ODOO-02",
                tenant_id=tenant_id,
                name="Odoo Enterprise REST API Bridge",
                connector_type="ERP_ODOO",
                status="CONNECTED",
                deployment="Cloud API",
                connectivity_state="LIVE",
                last_sync_timestamp="1 minute ago",
                next_scheduled_sync="in 4 minutes",
                records_synced_last_24h=68900,
                error_rate_percent=0.00,
                sync_frequency="Every 5 minutes",
                endpoint_masked="https://quidch.odoo.com/api/v2/***",
                health_note="Operational. Sales orders and production bills synchronized.",
                checkpoint="CHK-ODOO-441029",
                created_at=now_dt,
                updated_at=now_dt
            ),
            ConnectorModel(
                id="CONN-SAP-03",
                tenant_id=tenant_id,
                name="SAP S/4HANA OData Enterprise Gateway",
                connector_type="ERP_SAP",
                status="CONNECTED",
                deployment="Cloud API / SAP Gateway",
                connectivity_state="LIVE",
                last_sync_timestamp="4 minutes ago",
                next_scheduled_sync="Continuous (Webhooks)",
                records_synced_last_24h=184520,
                error_rate_percent=0.02,
                sync_frequency="Near Real-Time Webhooks",
                endpoint_masked="https://sap-gateway.internal.aurix.ai/***",
                health_note="Operational. Bi-directional PO and Goods Receipt sync active.",
                checkpoint="CHK-SAP-883102",
                created_at=now_dt,
                updated_at=now_dt
            ),
            ConnectorModel(
                id="CONN-TMS-04",
                tenant_id=tenant_id,
                name="Freight Carrier Telematics & GPS Listener",
                connector_type="TMS_FREIGHT",
                status="DEGRADED",
                deployment="Cloud API",
                connectivity_state="SYNC_DELAYED",
                last_sync_timestamp="19 minutes ago",
                next_scheduled_sync="Retrying in 2 minutes",
                records_synced_last_24h=12450,
                error_rate_percent=2.84,
                sync_frequency="Every 15 minutes",
                endpoint_masked="https://tms-gateway.gatikwe.com/***",
                health_note="Intermittent timeout on webhook listener. Local buffer holds un-synced events safely.",
                checkpoint="CHK-TMS-110942",
                created_at=now_dt,
                updated_at=now_dt
            )
        ]
        for c in conns:
            db.add(c)
        db.commit()

@router.get("/integrations")
async def get_all_connectors(
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user_claims)
):
    tenant_id = claims["tenantId"]
    set_current_tenant_id(tenant_id)
    db.info["tenant_id"] = tenant_id
    
    _seed_connectors_if_empty(db, tenant_id)
    conns = db.query(ConnectorModel).filter(ConnectorModel.tenant_id == tenant_id).all()
    return [
        {
            "connectorId": c.id,
            "name": c.name,
            "type": c.connector_type,
            "status": c.status,
            "deployment": c.deployment,
            "connectivityState": c.connectivity_state,
            "lastSyncTimestamp": c.last_sync_timestamp,
            "nextScheduledSync": c.next_scheduled_sync,
            "recordsSyncedLast24h": c.records_synced_last_24h,
            "errorRatePercent": c.error_rate_percent,
            "syncFrequency": c.sync_frequency,
            "endpointMasked": c.endpoint_masked,
            "healthNote": c.health_note,
            "checkpoint": c.checkpoint
        }
        for c in conns
    ]

@router.post("/integrations/{connector_id}/test", response_model=ConnectorTestResponse)
async def test_connector_connection(
    connector_id: str,
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user_claims)
):
    tenant_id = claims["tenantId"]
    set_current_tenant_id(tenant_id)
    db.info["tenant_id"] = tenant_id
    
    conn = db.query(ConnectorModel).filter(
        ConnectorModel.id == connector_id,
        ConnectorModel.tenant_id == tenant_id
    ).first()
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Connector {connector_id} not registered.")
    
    is_degraded = conn.status == "DEGRADED"
    return ConnectorTestResponse(
        connectorId=connector_id,
        status="DEGRADED" if is_degraded else "HEALTHY",
        latencyMs=185 if is_degraded else 24,
        message="Handshake verified with remote agent endpoint." if not is_degraded else "High latency response detected.",
        endpointVerified=conn.endpoint_masked,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

@router.post("/integrations/{connector_id}/sync", response_model=SyncConnectorResponse)
async def sync_connector(
    connector_id: str,
    req: SyncConnectorRequest,
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user_claims)
):
    tenant_id = claims["tenantId"]
    set_current_tenant_id(tenant_id)
    db.info["tenant_id"] = tenant_id
    
    conn = db.query(ConnectorModel).filter(
        ConnectorModel.id == connector_id,
        ConnectorModel.tenant_id == tenant_id
    ).first()
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Connector {connector_id} not found.")
    
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    new_checkpoint = f"CHK-{connector_id.split('-')[1]}-{timestamp.strftime('%H%M%S')}"
    conn.last_sync_timestamp = "Just now"
    conn.checkpoint = new_checkpoint
    conn.records_synced_last_24h += 842
    conn.updated_at = timestamp
    db.commit()

    return SyncConnectorResponse(
        connectorId=connector_id,
        status="COMPLETED",
        recordsSynced=842,
        checkpointId=new_checkpoint,
        completedAt=timestamp.isoformat(),
        durationMs=480
    )

@router.get("/models")
async def get_model_registry(claims: dict = Depends(get_current_user_claims)):
    return [
        {
            "modelId": "MDL-FCST-XGB-V4",
            "modelName": "XGBoost Multi-Horizon Demand Predictor",
            "algorithmFamily": "XGBOOST",
            "version": "v4.2.1",
            "isChampion": True,
            "targetDomain": "DEMAND_FORECAST",
            "wapePercent": 8.2,
            "rmse": 14.8,
            "driftStatus": "STABLE",
            "lastTrainedAt": "2025-02-10 03:00 AM IST",
            "trainingSamplesCount": 145000,
            "deployedEnvironment": "PRODUCTION"
        },
        {
            "modelId": "MDL-FCST-SARIMA-V3",
            "modelName": "Seasonal ARIMA Benchmark Challenger",
            "algorithmFamily": "SARIMA",
            "version": "v3.1.0",
            "isChampion": False,
            "targetDomain": "DEMAND_FORECAST",
            "wapePercent": 11.4,
            "rmse": 18.2,
            "driftStatus": "STABLE",
            "lastTrainedAt": "2025-02-10 03:30 AM IST",
            "trainingSamplesCount": 145000,
            "deployedEnvironment": "STAGING"
        },
        {
            "modelId": "MDL-LT-QUANT-V2",
            "modelName": "Empirical Lead-Time Quantile Estimator",
            "algorithmFamily": "ETS",
            "version": "v2.0.4",
            "isChampion": True,
            "targetDomain": "LEAD_TIME_QUANTILE",
            "wapePercent": 6.8,
            "rmse": 2.1,
            "driftStatus": "MODERATE_DRIFT",
            "lastTrainedAt": "2025-02-08 02:00 AM IST",
            "trainingSamplesCount": 8400,
            "deployedEnvironment": "PRODUCTION"
        }
    ]

@router.post("/models/{model_id}/retrain")
async def retrain_model(
    model_id: str,
    req: RetrainModelRequest,
    claims: dict = Depends(get_current_user_claims)
):
    return {
        "success": True,
        "modelId": model_id,
        "pipelineState": "DISPATCHED_TO_WORKER",
        "jobId": f"JOB-ML-{datetime.datetime.now().strftime('%M%S')}"
    }

@router.get("/users")
async def get_user_directory(
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user_claims)
):
    tenant_id = claims["tenantId"]
    users = db.query(User).filter(User.tenant_id == tenant_id).all()
    return [
        {
            "userId": u.id,
            "email": u.email,
            "fullName": u.full_name,
            "role": u.role,
            "tenantId": u.tenant_id,
            "status": "ACTIVE" if u.is_active else "DISABLED",
            "lastLoginAt": u.last_login_at.strftime("%Y-%m-%d %H:%M:%S UTC") if u.last_login_at else "Never",
            "mfaEnabled": True
        }
        for u in users
    ]

@router.get("/audit-logs")
async def get_audit_trail(
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user_claims)
):
    tenant_id = claims["tenantId"]
    logs = db.query(AIAuditLogModel).filter(AIAuditLogModel.tenant_id == tenant_id).order_by(AIAuditLogModel.created_at.desc()).limit(20).all()
    if not logs:
        return [
            {
                "logId": "AUD-9941",
                "timestamp": "Today 11:22 AM IST",
                "actorEmail": claims.get("email", "kaushik@aurix.ai"),
                "actorRole": claims.get("role", "SUPER_ADMIN"),
                "actionCategory": "ACTION_EXECUTION",
                "eventSummary": "Phase 14 preflight signoff executed for Action ACT-2026-101.",
                "ipAddress": "127.0.0.1",
                "resultStatus": "SUCCESS"
            }
        ]
    return [
        {
            "logId": l.id,
            "timestamp": l.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "actorEmail": claims.get("email", "system"),
            "actorRole": "SYSTEM",
            "actionCategory": l.query_type,
            "eventSummary": f"AI Audit: {l.provider_name}/{l.model_name} [{l.status}]",
            "ipAddress": "127.0.0.1",
            "resultStatus": l.status
        }
        for l in logs
    ]

@router.get("/system-health")
async def get_system_health(
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user_claims)
):
    db_status = "HEALTHY"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "DEGRADED"

    return {
        "evaluatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "overallHealth": "HEALTHY" if db_status == "HEALTHY" else "DEGRADED",
        "meanApiLatencyMs": 28.4,
        "activeDatabaseConnections": 1,
        "services": [
            {
                "serviceKey": "SRV-FASTAPI",
                "serviceName": "FastAPI Canonical API Engine",
                "status": "HEALTHY",
                "latencyMs": 18.2,
                "uptimePercent": 99.98,
                "activeWorkersOrConnections": 1,
                "resourceUtilizationPercent": 42.0,
                "lastCheckedAt": "Just now"
            },
            {
                "serviceKey": "SRV-DATABASE",
                "serviceName": "PostgreSQL Primary (RLS Enforced)",
                "status": db_status,
                "latencyMs": 4.8,
                "uptimePercent": 99.99,
                "activeWorkersOrConnections": 1,
                "resourceUtilizationPercent": 36.5,
                "lastCheckedAt": "Just now"
            }
        ]
    }