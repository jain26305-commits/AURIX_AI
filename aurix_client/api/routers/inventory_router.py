from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import math
import datetime

router = APIRouter(prefix="/inventory", tags=["Inventory Optimization"])

class RecalculatePolicyRequest(BaseModel):
    skuId: str = Field(..., description="Target SKU identifier")
    serviceLevelTargetPercent: float = Field(..., ge=50.0, le=99.9, description="Target cycle service level (50% - 99.9%)")

class RecalculatePolicyResponse(BaseModel):
    skuId: str
    serviceLevelTargetPercent: float
    computedSafetyStockUnits: int
    computedReorderPointUnits: int
    leadTimeDemandUnits: int
    zScoreUsed: float
    stockoutProbabilityPercent: float
    recommendationAction: str

class InventoryMetricSummary(BaseModel):
    totalSkusMonitored: int
    totalOnHandUnits: int
    totalCommittedUnits: int
    meanDaysOfCover: float
    criticalStockoutRiskCount: int
    holdingCostDragAnnualINR: float

@router.post("/recalculate-policy", response_model=RecalculatePolicyResponse)
async def recalculate_policy(req: RecalculatePolicyRequest, x_tenant_id: Optional[str] = Header(None)):
    sl = req.serviceLevelTargetPercent

    # Inverse CDF approximation for standard normal distribution Z-score
    if sl >= 99.0:
        z = 2.33
    elif sl >= 98.0:
        z = 2.05
    elif sl >= 95.0:
        z = 1.65
    elif sl >= 90.0:
        z = 1.28
    elif sl >= 85.0:
        z = 1.04
    else:
        z = 0.84

    daily_demand = 5.14
    lead_time_days = 28
    sigma_demand = 1.2

    ltd = round(daily_demand * lead_time_days)
    ss = round(z * sigma_demand * math.sqrt(lead_time_days) * 5.2)
    rop = ltd + ss

    action = (
        "Elevated buffer policy active. Trigger expedited replenishment if on-hand dips below ROP."
        if sl >= 98.0
        else "Steady-state replenishment policy operating within baseline safety boundaries."
    )

    return RecalculatePolicyResponse(
        skuId=req.skuId,
        serviceLevelTargetPercent=sl,
        computedSafetyStockUnits=ss,
        computedReorderPointUnits=rop,
        leadTimeDemandUnits=ltd,
        zScoreUsed=z,
        stockoutProbabilityPercent=round(100.0 - sl, 1),
        recommendationAction=action
    )

@router.get("/metrics", response_model=InventoryMetricSummary)
async def get_inventory_metrics(x_tenant_id: Optional[str] = Header(None)):
    return InventoryMetricSummary(
        totalSkusMonitored=248,
        totalOnHandUnits=14850,
        totalCommittedUnits=3420,
        meanDaysOfCover=18.4,
        criticalStockoutRiskCount=3,
        holdingCostDragAnnualINR=428500.0
    )

@router.get("/tournament")
async def get_forecasting_tournament(x_tenant_id: Optional[str] = Header(None)):
    return {
        "evaluatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "tournamentLeaderboard": [
            {
                "modelId": "MDL-XGB-01",
                "modelName": "XGBoost Multi-Horizon Regressor",
                "algorithmFamily": "XGBOOST",
                "wapePercent": 8.2,
                "rmse": 14.8,
                "isChampion": True,
                "status": "PRODUCTION_CHAMPION"
            },
            {
                "modelId": "MDL-SARIMA-02",
                "modelName": "SARIMA (2,1,2)(1,1,1)7 Seasonal",
                "algorithmFamily": "SARIMA",
                "wapePercent": 11.4,
                "rmse": 18.2,
                "isChampion": False,
                "status": "BENCHMARK_CHALLENGER"
            },
            {
                "modelId": "MDL-PROPHET-03",
                "modelName": "Additive Trend & Holiday Prophet",
                "algorithmFamily": "PROPHET",
                "wapePercent": 13.1,
                "rmse": 21.0,
                "isChampion": False,
                "status": "BENCHMARK_CHALLENGER"
            }
        ]
    }