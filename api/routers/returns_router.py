from fastapi import APIRouter, Header
from typing import Optional, List, Dict
import datetime

router = APIRouter(prefix="/returns", tags=["Reverse Logistics"])

@router.get("/summary")
async def get_returns_summary(x_tenant_id: Optional[str] = Header(None)):
    return {
        "evaluatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "summary": {
            "totalReturnsCount": 4,
            "totalReturnedUnits": 48,
            "aggregateRefundINR": 31200.0,
            "netLossINR": 11400.0,
            "portfolioReturnRatePercent": 3.2,
            "topReturnReason": "SIZE_FIT",
            "dispositionMetrics": [
                {
                    "disposition": "RESTOCK",
                    "unitsCount": 32,
                    "percentageOfTotal": 66.7,
                    "totalRefundINR": 20800.0,
                    "salvageRecoveryINR": 20800.0
                },
                {
                    "disposition": "REWORK",
                    "unitsCount": 10,
                    "percentageOfTotal": 20.8,
                    "totalRefundINR": 6500.0,
                    "salvageRecoveryINR": 4200.0
                },
                {
                    "disposition": "SCRAP",
                    "unitsCount": 6,
                    "percentageOfTotal": 12.5,
                    "totalRefundINR": 3900.0,
                    "salvageRecoveryINR": 0.0
                }
            ]
        },
        "returns": [
            {
                "rmaNumber": "RMA-2025-041",
                "orderId": "ORD-2025-9812",
                "skuId": "SKU-004",
                "skuName": "103 Black-XXL (Hoodie)",
                "customerName": "Rohit Verma (Myntra Customer)",
                "returnReason": "SIZE_FIT",
                "disposition": "RESTOCK",
                "returnQty": 1,
                "refundAmountINR": 900.0,
                "salvageValueINR": 900.0,
                "netFinancialLossINR": 0.0,
                "requestedDate": "2025-02-12",
                "inspectedDate": "2025-02-14",
                "inspectionNotes": "Pristine packaging, brand tags attached. Returned to prime A-grade stock bin."
            },
            {
                "rmaNumber": "RMA-2025-042",
                "orderId": "ORD-2025-9794",
                "skuId": "SKU-001",
                "skuName": "101 Beige-L (T-Shirt)",
                "customerName": "Ananya Sharma (D2C)",
                "returnReason": "FABRIC_DEFECT",
                "disposition": "REWORK",
                "returnQty": 12,
                "refundAmountINR": 5040.0,
                "salvageValueINR": 3600.0,
                "netFinancialLossINR": 1440.0,
                "requestedDate": "2025-02-10",
                "inspectedDate": "2025-02-13",
                "inspectionNotes": "Loose overlock seam on collar rib. Dispatched to Peenya plant rework line for restitching."
            }
        ]
    }