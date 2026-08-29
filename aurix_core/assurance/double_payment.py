"""
AURIX Continuous Assurance — Double Payment & Duplicate Disbursement Prevention
Phase 20 Core Implementation.
Detects exact and fuzzy duplicate payment transactions.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from aurix_core.assurance.contracts import (
    AssuranceDomain,
    AssuranceFinding,
    LeakageSeverity,
)


class DoublePaymentEngine:
    """Detects exact and fuzzy duplicate payment disbursements."""

    @staticmethod
    def sanitize_doc_number(doc_num: str) -> str:
        """Sanitize document numbers for fuzzy duplicate detection."""
        if not doc_num:
            return ""
        return re.sub(r"[^A-Za-z0-9]", "", str(doc_num)).upper()

    @classmethod
    def evaluate_payments(
        cls,
        tenant_id: str,
        payments: List[Dict[str, Any]],
        invoices: Optional[List[Dict[str, Any]]] = None,
    ) -> List[AssuranceFinding]:
        """Scan a list of payments to identify duplicate disbursements."""
        findings: List[AssuranceFinding] = []
        seen_hashes: Dict[str, Dict[str, Any]] = {}
        fuzzy_groups: Dict[str, List[Dict[str, Any]]] = {}

        for p in payments:
            pay_id = str(p.get("id") or p.get("payment_number") or "")
            inv_id = str(p.get("invoice_id") or "")
            vendor_id = str(p.get("vendor_id") or p.get("supplier_id") or "")
            amount = float(p.get("amount") or 0.0)

            # 1. Exact Duplicate Check (Same vendor, invoice, amount)
            exact_key = f"{tenant_id}:{vendor_id}:{inv_id}:{amount:.2f}"
            exact_hash = hashlib.sha256(exact_key.encode("utf-8")).hexdigest()

            if exact_hash in seen_hashes:
                prior = seen_hashes[exact_hash]
                finding = AssuranceFinding(
                    tenant_id=tenant_id,
                    domain=AssuranceDomain.DOUBLE_PAYMENT,
                    severity=LeakageSeverity.CRITICAL,
                    title=f"Duplicate Payment Detected: {pay_id}",
                    description=f"Payment {pay_id} is identical to prior payment {prior['id']} ({amount} {p.get('currency', 'USD')}).",
                    financial_exposure=amount,
                    entity_type="payment",
                    entity_id=pay_id,
                    evidence_data={"duplicate_payment_id": prior["id"], "amount": amount, "invoice_id": inv_id},
                    recommended_action="Immediately void payment voucher and freeze automated disbursement.",
                )
                findings.append(finding)
            else:
                seen_hashes[exact_hash] = {"id": pay_id, "data": p}

            # 2. Fuzzy Duplicate Grouping (Same vendor, same amount, slightly altered invoice ref)
            sanitized_ref = cls.sanitize_doc_number(inv_id)
            fuzzy_key = f"{tenant_id}:{vendor_id}:{amount:.2f}"
            if fuzzy_key not in fuzzy_groups:
                fuzzy_groups[fuzzy_key] = []

            for prior in fuzzy_groups[fuzzy_key]:
                if prior["id"] != pay_id and prior["sanitized_ref"] != sanitized_ref and sanitized_ref in prior["sanitized_ref"] or prior["sanitized_ref"] in sanitized_ref:
                    finding = AssuranceFinding(
                        tenant_id=tenant_id,
                        domain=AssuranceDomain.DOUBLE_PAYMENT,
                        severity=LeakageSeverity.HIGH,
                        title=f"Potential Fuzzy Duplicate Payment: {pay_id}",
                        description=f"Payment {pay_id} (Ref: {inv_id}) matches amount {amount} of Payment {prior['id']} (Ref: {prior['orig_ref']}).",
                        financial_exposure=amount,
                        entity_type="payment",
                        entity_id=pay_id,
                        evidence_data={"matched_payment_id": prior["id"], "amount": amount, "ref_1": inv_id, "ref_2": prior["orig_ref"]},
                        recommended_action="Audit vendor statement for duplicate invoice submission with altered numbering.",
                    )
                    findings.append(finding)

            fuzzy_groups[fuzzy_key].append({"id": pay_id, "orig_ref": inv_id, "sanitized_ref": sanitized_ref})

        return findings
