"""Phase 16 deterministic planning, execution, and collaboration contracts.

Phase 16 consolidates procurement, returns, MRP/capacity, ATP/CTP,
scenario analysis, impact handling, and governed orchestration without
reimplementing Phase 1-15 domain mathematics.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class MutationMetadata(BaseModel):
    """Optional external identity/idempotency metadata for write operations."""

    idempotency_key: Optional[str] = Field(default=None, min_length=1, max_length=255)
    source_system: str = Field(default="AURIX", min_length=1, max_length=64)
    external_record_id: Optional[str] = Field(default=None, min_length=1, max_length=255)


class PurchaseOrderLineInput(BaseModel):
    sku_id: str = Field(min_length=1)
    quantity: float = Field(gt=0)
    unit_price: Optional[float] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default=None, min_length=3, max_length=16)


class PurchaseOrderCreateRequest(MutationMetadata):
    supplier_id: str = Field(min_length=1)
    required_date: Optional[datetime] = None
    lines: List[PurchaseOrderLineInput] = Field(min_length=1)
    source_request_id: Optional[str] = Field(default=None, max_length=128)


class PurchaseOrderRevisionRequest(MutationMetadata):
    purchase_order_id: str = Field(min_length=1)
    reason: str = Field(min_length=1, max_length=500)
    lines: List[PurchaseOrderLineInput] = Field(min_length=1)


class SupplierAcknowledgementRequest(MutationMetadata):
    purchase_order_id: str = Field(min_length=1)
    acknowledgement_status: str = Field(
        pattern=r"^(ACKNOWLEDGED|PARTIAL|REJECTED)$"
    )
    committed_date: Optional[datetime] = None
    committed_quantity: Optional[float] = Field(default=None, ge=0)
    alternative_date: Optional[datetime] = None
    reason: Optional[str] = Field(default=None, max_length=500)
    supplier_reference: Optional[str] = Field(default=None, max_length=128)


class AdvanceShipmentNoticeLineInput(BaseModel):
    purchase_order_line_id: str = Field(min_length=1)
    shipped_quantity: float = Field(gt=0)


class AdvanceShipmentNoticeRequest(MutationMetadata):
    purchase_order_id: str = Field(min_length=1)
    expected_arrival_date: Optional[datetime] = None
    carrier: Optional[str] = Field(default=None, max_length=128)
    tracking_number: Optional[str] = Field(default=None, max_length=128)
    lines: List[AdvanceShipmentNoticeLineInput] = Field(min_length=1)


class GoodsReceiptLineInput(BaseModel):
    purchase_order_line_id: str = Field(min_length=1)
    received_quantity: float = Field(ge=0)
    accepted_quantity: float = Field(ge=0)
    rejected_quantity: float = Field(ge=0)

    @field_validator("accepted_quantity", "rejected_quantity")
    @classmethod
    def non_negative(cls, value: float) -> float:
        return value


class GoodsReceiptCreateRequest(MutationMetadata):
    purchase_order_id: str = Field(min_length=1)
    lines: List[GoodsReceiptLineInput] = Field(min_length=1)


class FinancialDocumentLineInput(BaseModel):
    purchase_order_line_id: str = Field(min_length=1)
    quantity: float = Field(gt=0)
    unit_price: Optional[float] = Field(default=None, ge=0)
    tax_amount: float = Field(default=0.0, ge=0)
    freight_amount: float = Field(default=0.0, ge=0)


class FinancialDocumentRequest(MutationMetadata):
    purchase_order_id: str = Field(min_length=1)
    document_type: str = Field(pattern=r"^(INVOICE|CREDIT_NOTE|DEBIT_NOTE)$")
    document_number: str = Field(min_length=1, max_length=128)
    amount: float = Field(ge=0)
    currency: str = Field(min_length=3, max_length=16)
    matched_receipt_id: Optional[str] = None
    reference_document_id: Optional[str] = None
    lines: List[FinancialDocumentLineInput] = Field(default_factory=list)


class ReturnCreateRequest(MutationMetadata):
    source_order_id: Optional[str] = None
    sku_id: str = Field(min_length=1)
    quantity: float = Field(gt=0)
    reason: str = Field(min_length=1, max_length=255)


class ReturnDispositionRequest(BaseModel):
    disposition: str = Field(
        pattern=r"^(RESTOCK|REPAIR|REFURBISH|REPLACE|SUPPLIER_RETURN|SCRAP)$"
    )
    recovery_value: Optional[float] = Field(default=None, ge=0)


class BOMLineInput(BaseModel):
    component_sku_id: str = Field(min_length=1)
    quantity_per: float = Field(gt=0)
    scrap_pct: float = Field(default=0, ge=0, lt=100)


class BOMCreateRequest(MutationMetadata):
    parent_sku_id: str = Field(min_length=1)
    version: str = Field(min_length=1, max_length=64)
    effective_from: datetime
    lines: List[BOMLineInput] = Field(min_length=1)


class MRPRequirement(BaseModel):
    sku_id: str = Field(min_length=1)
    gross_requirement: float = Field(gt=0)
    due_date: Optional[datetime] = None
    location_id: Optional[str] = None


class MRPRequest(MutationMetadata):
    requirements: List[MRPRequirement] = Field(min_length=1)


class CapacityResourceInput(BaseModel):
    resource_id: str = Field(min_length=1)
    available_hours: float = Field(ge=0)
    required_hours: float = Field(ge=0)


class CapacityCheckRequest(MutationMetadata):
    resources: List[CapacityResourceInput] = Field(min_length=1)


class SalesOrderLineInput(BaseModel):
    sku_id: str = Field(min_length=1)
    quantity: float = Field(gt=0)
    location_id: Optional[str] = None


class SalesOrderCreateRequest(MutationMetadata):
    customer_id: str = Field(min_length=1)
    requested_date: Optional[datetime] = None
    lines: List[SalesOrderLineInput] = Field(min_length=1)


class ATPRequest(BaseModel):
    sku_id: str = Field(min_length=1)
    requested_quantity: float = Field(gt=0)
    location_id: Optional[str] = None


class CTPRequest(ATPRequest):
    """Constrained-to-promise request.

    A CTP calculation is conservative: production lead time and capacity are
    required inputs when ATP is insufficient, and the engine refuses to
    fabricate feasibility without a BOM or explicit constraint data.
    """

    requested_date: Optional[datetime] = None
    production_lead_time_days: Optional[int] = Field(default=None, ge=0)
    capacity_resources: List[CapacityResourceInput] = Field(default_factory=list)


class ScenarioRequest(BaseModel):
    scenario_type: str = Field(min_length=1, max_length=64)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ScenarioComparisonRequest(BaseModel):
    scenarios: List[ScenarioRequest] = Field(min_length=2, max_length=20)


class Phase16Result(BaseModel):
    success: bool
    status: str
    data: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
