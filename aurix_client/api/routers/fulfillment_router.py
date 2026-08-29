from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import datetime

router = APIRouter(prefix="/fulfillment", tags=["Outbound Fulfillment"])

class AtpCheckRequest(BaseModel):
    skuId: str
    requestedUnits: int
    targetDate: str

@router.post("/atp-check")
async def check_atp(req: AtpCheckRequest, x_tenant_id: Optional[str] = Header(None)):
    is_hoodie = req.skuId == "SKU-004"
    on_hand = 42 if is_hoodie else 327
    allocated = 42 if is_hoodie else 250
    unallocated = max(0, on_hand - allocated)
    can_fulfill = unallocated >= req.requestedUnits
    
    return {
        "skuId": req.skuId,
        "skuName": "103 Black-XXL (Hoodie)" if is_hoodie else "101 Beige-L (T-Shirt)",
        "requestedUnits": req.requestedUnits,
        "availableToPromiseUnits": unallocated,
        "capableToPromiseUnits": unallocated + (150 if is_hoodie else 250),
        "onHandStockUnits": on_hand,
        "allocatedStockUnits": allocated,
        "plannedReceiptsUnits": 150 if is_hoodie else 250,
        "canFulfillImmediately": can_fulfill,
        "promisedDeliveryDate": req.targetDate if can_fulfill else (datetime.date.today() + datetime.timedelta(days=18 if is_hoodie else 7)).isoformat(),
        "leadTimeDaysRequired": 1 if can_fulfill else (18 if is_hoodie else 7),
        "constrainingFactor": (
            "Inbound PO-2025-084 transit delay (+2.5d) and high allocated customer reservations."
            if not can_fulfill and is_hoodie
            else None
        )
    }