from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/procurement", tags=["Inbound Procurement"])

class CreatePoRequest(BaseModel):
    vendorId: Optional[str] = "VEND-001"
    vendorName: Optional[str] = "Apex Mills & Fabrics Pvt Ltd"
    promisedDeliveryDate: Optional[str] = None
    totalAmountINR: Optional[float] = 150000.0
    lineItems: Optional[List[dict]] = []

@router.post("/orders")
async def create_purchase_order(req: CreatePoRequest, x_tenant_id: Optional[str] = Header(None)):
    return {
        "poNumber": "PO-2025-998",
        "vendorId": req.vendorId,
        "vendorName": req.vendorName,
        "status": "DRAFT",
        "orderDate": "2025-02-14",
        "promisedDeliveryDate": req.promisedDeliveryDate or "2025-03-05",
        "totalAmountINR": req.totalAmountINR,
        "currency": "INR",
        "paymentTerms": "Net 45 Days",
        "lineItems": req.lineItems
    }