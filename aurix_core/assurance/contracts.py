"""
AURIX Continuous Assurance Engine — Contracts & Schemas
Phase 20 Core Implementation.
Defines schemas for audit findings, leakage classification, and matching states.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AssuranceDomain(str, Enum):
    """Audit and assurance problem domains."""
    THREE_WAY_MATCH = "THREE_WAY_MATCH"
    DOUBLE_PAYMENT = "DOUBLE_PAYMENT"
    UNBILLED_SHIPMENT = "UNBILLED_SHIPMENT"
    PHANTOM_INVENTORY = "PHANTOM_INVENTORY"
    PRICE_VARIANCE = "PRICE_VARIANCE"
    CONTRACT_COMPLIANCE = "CONTRACT_COMPLIANCE"
    VENDOR_SLA = "VENDOR_SLA"


class LeakageSeverity(str, Enum):
    """Financial risk severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FindingStatus(str, Enum):
    """Lifecycle status of an assurance finding."""
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    ACTION_PROPOSED = "ACTION_PROPOSED"
    REMEDIATED = "REMEDIATED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    SUPPRESSED = "SUPPRESSED"


class MatchStatus(str, Enum):
    """Three-way match outcome states."""
    PERFECT_MATCH = "PERFECT_MATCH"
    TOLERANCE_MATCH = "TOLERANCE_MATCH"
    PRICE_MISMATCH = "PRICE_MISMATCH"
    QUANTITY_MISMATCH = "QUANTITY_MISMATCH"
    UNMATCHED_INVOICE = "UNMATCHED_INVOICE"
    UNMATCHED_RECEIPT = "UNMATCHED_RECEIPT"


class AssuranceFinding(BaseModel):
    """Authoritative ledger defect, leakage record, or assurance exception."""
    model_config = ConfigDict(extra="allow")

    finding_id: str = Field(default_factory=lambda: f"FND-{uuid.uuid4().hex[:10].upper()}")
    tenant_id: str
    domain: AssuranceDomain
    severity: LeakageSeverity
    status: FindingStatus = FindingStatus.OPEN
    title: str
    description: str
    financial_exposure: float = 0.0
    currency: str = "USD"
    entity_type: str
    entity_id: str
    evidence_data: Dict[str, Any] = Field(default_factory=dict)
    recommended_action: Optional[str] = None
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ThreeWayMatchResult(BaseModel):
    """Result of an automated 3-way matching assertion."""
    match_id: str = Field(default_factory=lambda: f"MTH-{uuid.uuid4().hex[:10].upper()}")
    tenant_id: str
    po_id: str
    receipt_id: Optional[str] = None
    invoice_id: str
    match_status: MatchStatus
    po_amount: float
    receipt_qty: float
    invoice_amount: float
    invoice_qty: float
    price_variance: float = 0.0
    qty_variance: float = 0.0
    is_approved: bool = False
    leakage_amount: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)


class AssuranceRunSummary(BaseModel):
    """Consolidated summary of a continuous assurance sweep."""
    run_id: str = Field(default_factory=lambda: f"ASR-{uuid.uuid4().hex[:10].upper()}")
    tenant_id: str
    total_findings: int = 0
    total_financial_leakage: float = 0.0
    critical_findings_count: int = 0
    high_findings_count: int = 0
    domain_breakdown: Dict[str, int] = Field(default_factory=dict)
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
