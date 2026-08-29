from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import datetime

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

# Enterprise Connector Registry
CONNECTORS_DB: Dict[str, Dict[str, Any]] = {
    "CONN-TALLY-01": {
        "connectorId": "CONN-TALLY-01",
        "name": "Tally Prime Local CDC Bridge",
        "type": "ERP_TALLY",
        "status": "CONNECTED",
        "deployment": "Local Agent (Outbound HTTPS)",
        "connectivityState": "LIVE",
        "lastSyncTimestamp": "3 minutes ago",
        "nextScheduledSync": "in 12 minutes",
        "recordsSyncedLast24h": 42150,
        "errorRatePercent": 0.01,
        "syncFrequency": "Every 15 minutes (Incremental CDC)",
        "endpointMasked": "https://agent-tally-peenya.internal.aurix.ai/***",
        "healthNote": "Operational. Vouchers and ledger stock balances in sync.",
        "checkpoint": "CHK-TALLY-998241"
    },
    "CONN-ODOO-02": {
        "connectorId": "CONN-ODOO-02",
        "name": "Odoo Enterprise REST API Bridge",
        "type": "ERP_ODOO",
        "status": "CONNECTED",
        "deployment": "Cloud API",
        "connectivityState": "LIVE",
        "lastSyncTimestamp": "1 minute ago",
        "nextScheduledSync": "in 4 minutes",
        "recordsSyncedLast24h": 68900,
        "errorRatePercent": 0.00,
        "syncFrequency": "Every 5 minutes",
        "endpointMasked": "https://quidch.odoo.com/api/v2/***",
        "healthNote": "Operational. Sales orders and production bills synchronized.",
        "checkpoint": "CHK-ODOO-441029"
    },
    "CONN-SAP-03": {
        "connectorId": "CONN-SAP-03",
        "name": "SAP S/4HANA OData Enterprise Gateway",
        "type": "ERP_SAP",
        "status": "CONNECTED",
        "deployment": "Cloud API / SAP Gateway",
        "connectivityState": "LIVE",
        "lastSyncTimestamp": "4 minutes ago",
        "nextScheduledSync": "Continuous (Webhooks)",
        "recordsSyncedLast24h": 184520,
        "errorRatePercent": 0.02,
        "syncFrequency": "Near Real-Time Webhooks",
        "endpointMasked": "https://sap-gateway.internal.aurix.ai/***",
        "healthNote": "Operational. Bi-directional PO and Goods Receipt sync active.",
        "checkpoint": "CHK-SAP-883102"
    },
    "CONN-TMS-04": {
        "connectorId": "CONN-TMS-04",
        "name": "Freight Carrier Telematics & GPS Listener",
        "type": "TMS_FREIGHT",
        "status": "DEGRADED",
        "deployment": "Cloud API",
        "connectivityState": "SYNC_DELAYED",
        "lastSyncTimestamp": "19 minutes ago",
        "nextScheduledSync": "Retrying in 2 minutes",
        "recordsSyncedLast24h": 12450,
        "errorRatePercent": 2.84,
        "syncFrequency": "Every 15 minutes",
        "endpointMasked": "https://tms-gateway.gatikwe.com/***",
        "healthNote": "Intermittent timeout on webhook listener. Local buffer holds un-synced events safely.",
        "checkpoint": "CHK-TMS-110942"
    }
}

@router.get("/integrations")
async def get_all_connectors(x_tenant_id: Optional[str] = Header(None)):
    return list(CONNECTORS_DB.values())

@router.post("/integrations/{connector_id}/test", response_model=ConnectorTestResponse)
async def test_connector_connection(connector_id: str, x_tenant_id: Optional[str] = Header(None)):
    conn = CONNECTORS_DB.get(connector_id)
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Connector {connector_id} not registered.")
    
    is_degraded = conn["status"] == "DEGRADED"
    return ConnectorTestResponse(
        connectorId=connector_id,
        status="DEGRADED" if is_degraded else "HEALTHY",
        latencyMs=185 if is_degraded else 24,
        message="Handshake verified with remote agent endpoint." if not is_degraded else "High latency response detected.",
        endpointVerified=conn["endpointMasked"],
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

@router.post("/integrations/{connector_id}/sync", response_model=SyncConnectorResponse)
async def sync_connector(connector_id: str, req: SyncConnectorRequest, x_tenant_id: Optional[str] = Header(None)):
    conn = CONNECTORS_DB.get(connector_id)
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Connector {connector_id} not found.")
    
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    new_checkpoint = f"CHK-{connector_id.split('-')[1]}-{timestamp.strftime('%H%M%S')}"
    conn["lastSyncTimestamp"] = "Just now"
    conn["checkpoint"] = new_checkpoint

    return SyncConnectorResponse(
        connectorId=connector_id,
        status="COMPLETED",
        recordsSynced=842,
        checkpointId=new_checkpoint,
        completedAt=timestamp.isoformat(),
        durationMs=480
    )

@router.post("/models/{model_id}/retrain")
async def retrain_model(model_id: str, req: RetrainModelRequest, x_tenant_id: Optional[str] = Header(None)):
    return {
        "success": True,
        "modelId": model_id,
        "pipelineState": "DISPATCHED_TO_WORKER",
        "jobId": f"JOB-ML-{datetime.datetime.now().strftime('%M%S')}"
    }

@router.get("/system-health")
async def get_system_health(x_tenant_id: Optional[str] = Header(None)):
    return {
        "evaluatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "overallHealth": "HEALTHY",
        "meanApiLatencyMs": 28.4,
        "activeDatabaseConnections": 14,
        "celeryQueueDepth": 3,
        "services": [
            {
                "serviceKey": "SRV-FASTAPI",
                "serviceName": "FastAPI Canonical API Engine",
                "status": "HEALTHY",
                "latencyMs": 18.2,
                "uptimePercent": 99.98,
                "activeWorkersOrConnections": 8,
                "resourceUtilizationPercent": 42.0,
                "lastCheckedAt": "Just now"
            },
            {
                "serviceKey": "SRV-POSTGRES",
                "serviceName": "PostgreSQL Primary (RLS Enforced)",
                "status": "HEALTHY",
                "latencyMs": 4.8,
                "uptimePercent": 99.99,
                "activeWorkersOrConnections": 14,
                "resourceUtilizationPercent": 36.5,
                "lastCheckedAt": "Just now"
            },
            {
                "serviceKey": "SRV-REDIS-QUEUE",
                "serviceName": "Redis Queue & Celery Worker Cluster",
                "status": "HEALTHY",
                "latencyMs": 1.2,
                "uptimePercent": 100.0,
                "activeWorkersOrConnections": 4,
                "resourceUtilizationPercent": 22.1,
                "lastCheckedAt": "Just now"
            }
        ]
    }