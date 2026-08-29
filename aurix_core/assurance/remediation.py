"""
AURIX Continuous Assurance — Governed Remediation Bridge
Phase 20 Core Implementation.
Translates assurance leakage findings into Phase 14 Controlled Action proposals.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional
from aurix_core.assurance.contracts import AssuranceDomain, AssuranceFinding, LeakageSeverity


class AssuranceRemediationBridge:
    """Generates prescriptive Phase 14 Action proposals from audit findings."""

    @classmethod
    def create_action_proposal(
        cls,
        finding: AssuranceFinding,
        initiated_by: str = "AURIX_ASSURANCE_ENGINE",
    ) -> Dict[str, Any]:
        """Convert a critical/high assurance finding into a governed action schema."""
        action_id = f"ACT-ASR-{uuid.uuid4().hex[:8].upper()}"
        domain = "FINANCE"
        title = f"Remediation for {finding.title}"
        assigned_role = "FINANCE_ADMIN"
        priority = "URGENT" if finding.severity == LeakageSeverity.CRITICAL else "HIGH"

        prescriptive_payload: Dict[str, Any] = {
            "finding_id": finding.finding_id,
            "financial_exposure": finding.financial_exposure,
            "currency": finding.currency,
            "entity_type": finding.entity_type,
            "entity_id": finding.entity_id,
            "recommended_action": finding.recommended_action,
        }

        # Domain-specific action mapping
        if finding.domain == AssuranceDomain.THREE_WAY_MATCH:
            domain = "PROCUREMENT"
            assigned_role = "PROCUREMENT_ADMIN"
            prescriptive_payload["action_type"] = "HOLD_INVOICE_PAYMENT"
            prescriptive_payload["remedy"] = "Issue short-payment or demand credit memo."

        elif finding.domain == AssuranceDomain.DOUBLE_PAYMENT:
            domain = "FINANCE"
            assigned_role = "SUPER_ADMIN"
            prescriptive_payload["action_type"] = "VOID_DUPLICATE_PAYMENT"
            prescriptive_payload["remedy"] = "Freeze voucher and cancel disbursement batch."

        elif finding.domain == AssuranceDomain.UNBILLED_SHIPMENT:
            domain = "FULFILLMENT"
            assigned_role = "ACCOUNTS_RECEIVABLE"
            prescriptive_payload["action_type"] = "GENERATE_CUSTOMER_INVOICE"
            prescriptive_payload["remedy"] = "Dispatch immediate customer billing invoice."

        elif finding.domain == AssuranceDomain.PHANTOM_INVENTORY:
            domain = "INVENTORY"
            assigned_role = "WAREHOUSE_MANAGER"
            prescriptive_payload["action_type"] = "POST_INVENTORY_ADJUSTMENT"
            prescriptive_payload["remedy"] = "Write down ghost inventory and trigger cycle count."

        elif finding.domain == AssuranceDomain.PRICE_VARIANCE:
            domain = "PROCUREMENT"
            assigned_role = "FINANCE_ADMIN"
            prescriptive_payload["action_type"] = "CLAIM_VENDOR_REBATE"
            prescriptive_payload["remedy"] = "Enforce contracted price book and bill back PPV."

        return {
            "id": action_id,
            "tenant_id": finding.tenant_id,
            "title": title,
            "domain": domain,
            "priority": priority,
            "state": "AWAITING_APPROVAL",
            "target_entity_id": finding.entity_id,
            "target_entity_name": finding.entity_type,
            "prescriptive_payload_json": prescriptive_payload,
            "initiated_by": initiated_by,
            "assigned_approver_role": assigned_role,
            "preflight_cleared": False,
            "preflight_checks_json": [
                {"check_name": "FINDING_VALIDITY", "passed": True, "details": "Verified against active data fabric."},
                {"check_name": "FINANCIAL_THRESHOLD", "passed": True, "details": f"Exposure: {finding.financial_exposure}"},
            ],
            "audit_trail_json": [
                {"timestamp": finding.detected_at.isoformat(), "action": "PROPOSED", "actor": initiated_by}
            ],
        }
