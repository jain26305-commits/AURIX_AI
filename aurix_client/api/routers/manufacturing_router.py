from fastapi import APIRouter, HTTPException, Header
from typing import Optional

router = APIRouter(prefix="/manufacturing", tags=["Manufacturing & BOM"])

@router.get("/bom/{sku_id}")
async def get_bom(sku_id: str, x_tenant_id: Optional[str] = Header(None)):
    return {
        "parentSkuId": sku_id,
        "parentSkuName": f"Material {sku_id}",
        "category": "Apparel",
        "version": "BOM-v2.4",
        "yieldRatePercent": 97.2,
        "totalBomCostINR": 198.5,
        "components": []
    }