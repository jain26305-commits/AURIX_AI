"""Phase 16 procurement, planning, fulfillment, reverse-logistics, and control-tower APIs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from aurix_api.routers.intelligence import get_db
from aurix_api.schemas.auth import Permission, TenantContext
from aurix_api.schemas.base import ApiResponse, ResponseMetadata, ResponseStatus
from aurix_api.security.rbac import require_permission
from aurix_core.phase16.agent_contracts import ControlTowerQuery
from aurix_core.phase16.agent_orchestrator import Phase16Supervisor
from aurix_core.phase16.contracts import (
    AdvanceShipmentNoticeRequest,
    ATPRequest,
    BOMCreateRequest,
    CapacityCheckRequest,
    CTPRequest,
    FinancialDocumentRequest,
    GoodsReceiptCreateRequest,
    MRPRequest,
    PurchaseOrderCreateRequest,
    PurchaseOrderRevisionRequest,
    ReturnCreateRequest,
    ReturnDispositionRequest,
    SalesOrderCreateRequest,
    ScenarioComparisonRequest,
    ScenarioRequest,
    SupplierAcknowledgementRequest,
)
from aurix_core.phase16.services import (
    CapacityService,
    FulfillmentService,
    ManufacturingService,
    ProcurementService,
    ReturnsService,
    ScenarioService,
)

router = APIRouter(prefix="/api/v1/phase16", tags=["Phase 16"])


def _response(result: object, tenant_id: str) -> ApiResponse[dict[str, Any]]:
    payload = result.model_dump() if hasattr(result, "model_dump") else {"data": result}
    return ApiResponse(
        status=ResponseStatus.SUCCESS if payload.get("success") else ResponseStatus.FAILED,
        data=payload,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.post("/procurement/purchase-orders", response_model=ApiResponse[dict[str, Any]])
def create_purchase_order(
    payload: PurchaseOrderCreateRequest,
    context: TenantContext = Depends(require_permission(Permission.WRITE_DATA)),
    db: Session = Depends(get_db),
) -> ApiResponse[dict[str, Any]]:
    return _response(ProcurementService.create_purchase_order(db, context.tenant_id, payload), context.tenant_id)


@router.post("/procurement/purchase-orders/revise", response_model=ApiResponse[dict[str, Any]])
def revise_purchase_order(
    payload: PurchaseOrderRevisionRequest,
    context: TenantContext = Depends(require_permission(Permission.WRITE_DATA)),
    db: Session = Depends(get_db),
) -> ApiResponse[dict[str, Any]]:
    return _response(ProcurementService.revise_purchase_order(db, context.tenant_id, payload), context.tenant_id)


@router.post("/procurement/purchase-orders/{purchase_order_id}/transition", response_model=ApiResponse[dict[str, Any]])
def transition_purchase_order(
    purchase_order_id: str,
    target_status: str,
    reason: str | None = None,
    committed_date: str | None = None,
    context: TenantContext = Depends(require_permission(Permission.WRITE_DATA)),
    db: Session = Depends(get_db),
) -> ApiResponse[dict[str, Any]]:
    from datetime import datetime

    parsed_date = datetime.fromisoformat(committed_date) if committed_date else None
    result = ProcurementService.transition_purchase_order(
        db, context.tenant_id, purchase_order_id, target_status, reason, parsed_date
    )
    return _response(result, context.tenant_id)


@router.post("/procurement/purchase-orders/acknowledgement", response_model=ApiResponse[dict[str, Any]])
def acknowledge_purchase_order(
    payload: SupplierAcknowledgementRequest,
    context: TenantContext = Depends(require_permission(Permission.WRITE_DATA)),
    db: Session = Depends(get_db),
) -> ApiResponse[dict[str, Any]]:
    return _response(ProcurementService.acknowledge_purchase_order(db, context.tenant_id, payload), context.tenant_id)


@router.post("/procurement/asn", response_model=ApiResponse[dict[str, Any]])
def create_asn(
    payload: AdvanceShipmentNoticeRequest,
    context: TenantContext = Depends(require_permission(Permission.WRITE_DATA)),
    db: Session = Depends(get_db),
) -> ApiResponse[dict[str, Any]]:
    return _response(ProcurementService.create_asn(db, context.tenant_id, payload), context.tenant_id)


@router.post("/procurement/goods-receipts", response_model=ApiResponse[dict[str, Any]])
def receive_goods(
    payload: GoodsReceiptCreateRequest,
    context: TenantContext = Depends(require_permission(Permission.WRITE_DATA)),
    db: Session = Depends(get_db),
) -> ApiResponse[dict[str, Any]]:
    return _response(ProcurementService.receive_goods(db, context.tenant_id, payload), context.tenant_id)


@router.post("/procurement/financial-documents", response_model=ApiResponse[dict[str, Any]])
def add_financial_document(
    payload: FinancialDocumentRequest,
    context: TenantContext = Depends(require_permission(Permission.WRITE_DATA)),
    db: Session = Depends(get_db),
) -> ApiResponse[dict[str, Any]]:
    return _response(ProcurementService.add_financial_document(db, context.tenant_id, payload), context.tenant_id)


@router.post("/returns", response_model=ApiResponse[dict[str, Any]])
def create_return(
    payload: ReturnCreateRequest,
    context: TenantContext = Depends(require_permission(Permission.WRITE_DATA)),
    db: Session = Depends(get_db),
) -> ApiResponse[dict[str, Any]]:
    return _response(ReturnsService.create_return(db, context.tenant_id, payload), context.tenant_id)


@router.post("/returns/{return_id}/disposition", response_model=ApiResponse[dict[str, Any]])
def dispose_return(
    return_id: str,
    payload: ReturnDispositionRequest,
    context: TenantContext = Depends(require_permission(Permission.WRITE_DATA)),
    db: Session = Depends(get_db),
) -> ApiResponse[dict[str, Any]]:
    return _response(ReturnsService.dispose_return(db, context.tenant_id, return_id, payload), context.tenant_id)


@router.post("/manufacturing/boms", response_model=ApiResponse[dict[str, Any]])
def create_bom(
    payload: BOMCreateRequest,
    context: TenantContext = Depends(require_permission(Permission.WRITE_DATA)),
    db: Session = Depends(get_db),
) -> ApiResponse[dict[str, Any]]:
    return _response(ManufacturingService.create_bom(db, context.tenant_id, payload), context.tenant_id)


@router.post("/manufacturing/mrp", response_model=ApiResponse[dict[str, Any]])
def run_mrp(
    payload: MRPRequest,
    context: TenantContext = Depends(require_permission(Permission.RUN_ANALYSIS)),
    db: Session = Depends(get_db),
) -> ApiResponse[dict[str, Any]]:
    return _response(ManufacturingService.run_mrp(db, context.tenant_id, payload), context.tenant_id)


@router.post("/manufacturing/capacity/check", response_model=ApiResponse[dict[str, Any]])
def check_capacity(
    payload: CapacityCheckRequest,
    context: TenantContext = Depends(require_permission(Permission.RUN_ANALYSIS)),
    db: Session = Depends(get_db),
) -> ApiResponse[dict[str, Any]]:
    return _response(CapacityService.check(db, context.tenant_id, payload), context.tenant_id)


@router.post("/fulfillment/orders", response_model=ApiResponse[dict[str, Any]])
def create_sales_order(
    payload: SalesOrderCreateRequest,
    context: TenantContext = Depends(require_permission(Permission.WRITE_DATA)),
    db: Session = Depends(get_db),
) -> ApiResponse[dict[str, Any]]:
    return _response(FulfillmentService.create_order(db, context.tenant_id, payload), context.tenant_id)


@router.post("/fulfillment/atp", response_model=ApiResponse[dict[str, Any]])
def calculate_atp(
    payload: ATPRequest,
    context: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    db: Session = Depends(get_db),
) -> ApiResponse[dict[str, Any]]:
    return _response(FulfillmentService.calculate_atp(db, context.tenant_id, payload), context.tenant_id)


@router.post("/fulfillment/ctp", response_model=ApiResponse[dict[str, Any]])
def calculate_ctp(
    payload: CTPRequest,
    context: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    db: Session = Depends(get_db),
) -> ApiResponse[dict[str, Any]]:
    return _response(FulfillmentService.calculate_ctp(db, context.tenant_id, payload), context.tenant_id)


@router.post("/fulfillment/lines/{sales_order_line_id}/reserve", response_model=ApiResponse[dict[str, Any]])
def reserve_inventory(
    sales_order_line_id: str,
    quantity: float = Query(gt=0),
    idempotency_key: str | None = None,
    context: TenantContext = Depends(require_permission(Permission.WRITE_DATA)),
    db: Session = Depends(get_db),
) -> ApiResponse[dict[str, Any]]:
    return _response(
        FulfillmentService.reserve(
            db, context.tenant_id, sales_order_line_id, quantity, idempotency_key
        ),
        context.tenant_id,
    )


@router.post("/scenarios", response_model=ApiResponse[dict[str, Any]])
def run_scenario(
    payload: ScenarioRequest,
    context: TenantContext = Depends(require_permission(Permission.RUN_ANALYSIS)),
    db: Session = Depends(get_db),
) -> ApiResponse[dict[str, Any]]:
    return _response(ScenarioService.run(db, context.tenant_id, payload), context.tenant_id)


@router.post("/scenarios/compare", response_model=ApiResponse[dict[str, Any]])
def compare_scenarios(
    payload: ScenarioComparisonRequest,
    context: TenantContext = Depends(require_permission(Permission.RUN_ANALYSIS)),
    db: Session = Depends(get_db),
) -> ApiResponse[dict[str, Any]]:
    return _response(ScenarioService.compare(db, context.tenant_id, payload), context.tenant_id)


@router.post("/control-tower/query", response_model=ApiResponse[dict[str, Any]])
def control_tower_query(
    payload: ControlTowerQuery,
    context: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    db: Session = Depends(get_db),
) -> ApiResponse[dict[str, Any]]:
    """Run deterministic-first Phase 16 supervisor orchestration."""
    result = Phase16Supervisor.run(db, context.tenant_id, payload)
    return _response(result, context.tenant_id)


@router.post("/control-tower/impacts/supplier-delay", response_model=ApiResponse[dict[str, Any]])
def supplier_delay_impact(
    supplier_id: str,
    delay_days: int = Query(gt=0),
    create_case: bool = False,
    context: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    db: Session = Depends(get_db),
) -> ApiResponse[dict[str, Any]]:
    result = Phase16Supervisor.supplier_delay_case(
        db=db,
        tenant_id=context.tenant_id,
        supplier_id=supplier_id,
        delay_days=delay_days,
        create=create_case,
    )
    from aurix_core.phase16.contracts import Phase16Result

    return _response(
        Phase16Result(
            success=True,
            status="IMPACT_COMPUTED",
            data=result,
            warnings=result.get("limitations", []),
        ),
        context.tenant_id,
    )
